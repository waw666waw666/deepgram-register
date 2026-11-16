"""
Disposable Email Client -- Multi-Backend with Automatic Failover.

Provides zero-configuration temporary mailboxes for account registration
workflows that require email verification.

Design notes
------------
* Three independent public providers are supported. If one is down, rate
  limited, or returns an unexpected payload, the client transparently fails
  over to the next. A single dead provider must never break a registration run.
* Every failure is surfaced as an exception. The client NEVER fabricates a
  placeholder address on network failure -- writing a fake mailbox into a
  signup form produces a silent hang instead of an actionable error.
* No credentials required. These are public, no-signup services.

Provider capability matrix (verified live):

    provider          create  read    auth         sample domain
    ---------------   ------  -----   ----------   ------------------------
    mail.tm           201     200     Bearer       fldubai.com
    guerrillamail     200     200     sid_token    guerrillamailblock.com
    tempmail.io       200     200     Bearer       bwmyga.com
"""
import re
import time
import random
import string
from typing import Optional, List, Dict, Any, Tuple, Callable

import requests


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class MailboxError(RuntimeError):
    """Base class for temporary-mailbox failures."""


class NoProviderAvailable(MailboxError):
    """Every configured provider failed to issue a usable mailbox."""


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _random_local_part(length: int = 12) -> str:
    """Return a random lowercase-alphanumeric local part for an address."""
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=length))


def _random_password(length: int = 16) -> str:
    """Return a random password suitable for provider account creation."""
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(random.choices(alphabet, k=length))


# ---------------------------------------------------------------------------
# Backend: mail.tm
# ---------------------------------------------------------------------------

class _MailTmBackend:
    """mail.tm -- JSON REST, Bearer token auth."""

    name = "mail.tm"
    base = "https://api.mail.tm"

    def __init__(self, proxies: Optional[Dict[str, str]], timeout: int):
        self.proxies = proxies
        self.timeout = timeout
        self._token: Optional[str] = None
        self._address: Optional[str] = None

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"} if self._token else {}

    def create(self) -> str:
        r = requests.get(f"{self.base}/domains", proxies=self.proxies, timeout=self.timeout)
        r.raise_for_status()
        members = r.json().get("hydra:member") or []
        if not members:
            raise MailboxError("mail.tm returned no available domains")
        domain = members[0]["domain"]

        address = f"{_random_local_part()}@{domain}"
        password = _random_password()

        r = requests.post(
            f"{self.base}/accounts",
            json={"address": address, "password": password},
            proxies=self.proxies, timeout=self.timeout,
        )
        if r.status_code >= 300:
            raise MailboxError(f"mail.tm create failed: {r.status_code} {r.text[:120]}")

        r = requests.post(
            f"{self.base}/token",
            json={"address": address, "password": password},
            proxies=self.proxies, timeout=self.timeout,
        )
        if r.status_code >= 300:
            raise MailboxError(f"mail.tm token failed: {r.status_code} {r.text[:120]}")

        self._token = r.json()["token"]
        self._address = address
        return address

    def messages(self) -> List[Dict[str, Any]]:
        r = requests.get(
            f"{self.base}/messages",
            headers=self._headers(), proxies=self.proxies, timeout=self.timeout,
        )
        r.raise_for_status()
        out = []
        for m in r.json().get("hydra:member") or []:
            out.append({"id": m.get("id"), "subject": m.get("subject", "")})
        return out

    def body(self, message_id: Any) -> str:
        r = requests.get(
            f"{self.base}/messages/{message_id}",
            headers=self._headers(), proxies=self.proxies, timeout=self.timeout,
        )
        r.raise_for_status()
        j = r.json()
        # mail.tm exposes text; html carries the richer body when text is empty.
        return "\n".join(filter(None, [j.get("subject", ""), j.get("text", ""), j.get("html", "")]))


# ---------------------------------------------------------------------------
# Backend: tempmail.io
# ---------------------------------------------------------------------------

class _TempMailIoBackend:
    """tempmail.io -- JSON REST, Bearer token auth."""

    name = "tempmail.io"
    base = "https://api.internal.temp-mail.io/api/v3"

    def __init__(self, proxies: Optional[Dict[str, str]], timeout: int):
        self.proxies = proxies
        self.timeout = timeout
        self._token: Optional[str] = None
        self._address: Optional[str] = None

    def create(self) -> str:
        r = requests.get(f"{self.base}/domains", proxies=self.proxies, timeout=self.timeout)
        r.raise_for_status()
        payload = r.json()
        # Response shape has varied: a bare list, or {"domains": [{"name": ...}]}.
        if isinstance(payload, dict):
            domains = payload.get("domains") or []
            domain = domains[0]["name"] if domains else None
        elif isinstance(payload, list):
            first = payload[0] if payload else None
            domain = first["name"] if isinstance(first, dict) else first
        else:
            domain = None
        if not domain:
            raise MailboxError("tempmail.io returned no available domains")

        r = requests.post(
            f"{self.base}/email/new",
            json={"name": _random_local_part(), "domain": domain},
            proxies=self.proxies, timeout=self.timeout,
        )
        if r.status_code >= 300:
            raise MailboxError(f"tempmail.io create failed: {r.status_code} {r.text[:120]}")

        j = r.json()
        self._token = j.get("token")
        self._address = j.get("email")
        if not self._address:
            raise MailboxError("tempmail.io returned no address")
        return self._address

    def messages(self) -> List[Dict[str, Any]]:
        r = requests.get(
            f"{self.base}/email/{self._address}/messages",
            headers={"Authorization": f"Bearer {self._token}"},
            proxies=self.proxies, timeout=self.timeout,
        )
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict):
            data = data.get("messages") or []
        out = []
        for m in data or []:
            out.append({
                "id": m.get("id"),
                "subject": m.get("subject", ""),
                "body": m.get("body_text") or m.get("body_html") or "",
            })
        return out

    def body(self, message_id: Any) -> str:
        # tempmail.io returns bodies inline; no per-message fetch endpoint needed.
        for m in self.messages():
            if m.get("id") == message_id:
                return "\n".join(filter(None, [m.get("subject", ""), m.get("body", "")]))
        return ""


# ---------------------------------------------------------------------------
# Backend: Guerrilla Mail
# ---------------------------------------------------------------------------

class _GuerrillaMailBackend:
    """Guerrilla Mail -- query-string API, session-token auth (no signup)."""

    name = "guerrillamail"
    base = "https://api.guerrillamail.com/ajax.php"

    def __init__(self, proxies: Optional[Dict[str, str]], timeout: int):
        self.proxies = proxies
        self.timeout = timeout
        self._sid: Optional[str] = None
        self._address: Optional[str] = None

    def create(self) -> str:
        r = requests.get(
            f"{self.base}?f=get_email_address&ip=127.0.0.1&agent=autoregister",
            proxies=self.proxies, timeout=self.timeout,
        )
        r.raise_for_status()
        j = r.json()
        self._sid = j.get("sid_token")
        self._address = j.get("email_addr")
        if not (self._sid and self._address):
            raise MailboxError("guerrillamail returned no address/session")
        return self._address

    def messages(self) -> List[Dict[str, Any]]:
        # Guerrilla Mail serves a welcome message on first access. It occupies
        # the first slot, so reading only seq=0 would permanently miss the real
        # verification mail that arrives behind it. Walk forward until the
        # provider stops returning entries.
        out: List[Dict[str, Any]] = []
        seq = 0
        seen_ids = set()
        while seq < 25:  # hard ceiling; inboxes here hold a handful of messages
            r = requests.get(
                f"{self.base}?f=check_email&seq={seq}&sid_token={self._sid}",
                proxies=self.proxies, timeout=self.timeout,
            )
            r.raise_for_status()
            batch = r.json().get("list") or []
            if not batch:
                break
            advanced = False
            for m in batch:
                mid = m.get("mail_id")
                if mid in seen_ids:
                    continue
                seen_ids.add(mid)
                advanced = True
                out.append({
                    "id": mid,
                    "subject": m.get("mail_subject", ""),
                    "body": m.get("mail_excerpt", ""),
                })
            if not advanced:
                break
            seq += len(batch)
        return out

    def body(self, message_id: Any) -> str:
        r = requests.get(
            f"{self.base}?f=fetch_email&email_id={message_id}&sid_token={self._sid}",
            proxies=self.proxies, timeout=self.timeout,
        )
        r.raise_for_status()
        j = r.json()
        # Guerrilla returns raw RFC822 in mail_body; strip tags for matching.
        raw = "\n".join(filter(None, [j.get("mail_subject", ""), j.get("mail_body", "")]))
        return re.sub(r"<[^>]+>", " ", raw)


# ---------------------------------------------------------------------------
# Public client
# ---------------------------------------------------------------------------

_BACKENDS: Tuple[Callable[..., Any], ...] = (
    _MailTmBackend,
    _TempMailIoBackend,
    _GuerrillaMailBackend,
)


class DisposableMailClient:
    """
    Zero-config temporary mailbox with automatic provider failover.

    Usage:
        client = DisposableMailClient()
        email = client.create_mailbox()          # e.g. "a1b2c3d4e5f6@fldubai.com"
        ... submit signup form with `email` ...
        code = client.poll_for_verification_code(timeout_secs=120)

    Args:
        proxy:      Optional proxy URL applied to all provider requests, e.g.
                    "http://127.0.0.1:8080". When omitted, the standard
                    HTTP_PROXY / HTTPS_PROXY environment variables are honoured.
        timeout:    Per-request timeout in seconds.
        providers:  Optional explicit backend ordering by name; defaults to the
                    built-in order (mail.tm -> tempmail.io -> guerrillamail).
    """

    def __init__(self, proxy: Optional[str] = None, timeout: int = 20,
                 providers: Optional[List[str]] = None):
        self.timeout = timeout
        self.proxies = {"http": proxy, "https": proxy} if proxy else None
        self.active_address: Optional[str] = None
        self.provider: Optional[str] = None
        self._backend = None
        self._attempts: List[str] = []

        registry = {b.name: b for b in _BACKENDS}
        names = providers if providers else [b.name for b in _BACKENDS]
        self._order = [registry[n] for n in names if n in registry]
        if not self._order:
            self._order = list(_BACKENDS)

    # -- lifecycle ---------------------------------------------------------

    def create_mailbox(self) -> str:
        """
        Acquire a fresh temporary mailbox.

        Tries each backend in order and returns the first usable address.
        Raises NoProviderAvailable if every provider fails -- it never returns
        a fabricated address.
        """
        errors: List[str] = []
        self._attempts = []

        for backend_cls in self._order:
            name = backend_cls.name
            self._attempts.append(name)
            try:
                backend = backend_cls(self.proxies, self.timeout)
                address = backend.create()
                if not address or "@" not in address:
                    raise MailboxError(f"{name} returned a malformed address: {address!r}")

                self._backend = backend
                self.active_address = address
                self.provider = name
                return address
            except Exception as e:
                errors.append(f"{name}: {type(e).__name__}: {str(e)[:110]}")
                continue

        detail = "\n  ".join(errors)
        raise NoProviderAvailable(
            "All temporary-mail providers failed. Tried:\n  " + detail +
            "\n\nHints: check network/proxy connectivity, or run "
            "`python main.py doctor` to diagnose the environment.\n"
            "If the target site requires a trusted mailbox, supply your own "
            "address via the site adapter instead of a disposable one."
        )

    # -- reading -----------------------------------------------------------

    def check_messages(self) -> List[Dict[str, Any]]:
        """Return the current inbox as a list of {id, subject, body?} dicts."""
        if not self._backend:
            return []
        try:
            return self._backend.messages()
        except Exception:
            # A transient read error must not abort an in-flight poll loop;
            # the caller retries on the next tick.
            return []

    def read_message(self, message_id: Any) -> str:
        """Return the flattened text body of one message."""
        if not self._backend:
            return ""
        try:
            return self._backend.body(message_id)
        except Exception:
            return ""

    # -- polling -----------------------------------------------------------

    def poll_for_verification_code(
        self,
        timeout_secs: int = 120,
        pattern: str = r"\b\d{4,8}\b",
        first_interval: float = 3.0,
        max_interval: float = 10.0,
    ) -> Optional[str]:
        """
        Poll the inbox until a code matching `pattern` arrives.

        Uses adaptive backoff -- fast on the first ticks (verification mail
        usually lands within seconds), then easing off to reduce request load.

        Returns the matched code, or None on timeout.
        """
        if not self._backend:
            raise MailboxError("create_mailbox() must be called before polling")

        deadline = time.time() + timeout_secs
        interval = first_interval
        seen: set = set()

        while time.time() < deadline:
            for msg in self.check_messages():
                mid = msg.get("id")
                if mid in seen:
                    continue
                seen.add(mid)

                text = msg.get("body") or self.read_message(mid)
                match = re.search(pattern, text or "")
                if match:
                    return match.group(0)

            time.sleep(interval)
            interval = min(interval * 1.3, max_interval)

        return None

    def poll_for_verification_link(
        self,
        timeout_secs: int = 120,
        url_pattern: str = r'https?://[^\s"\'<>]+',
        first_interval: float = 3.0,
        max_interval: float = 10.0,
    ) -> Optional[str]:
        """Poll the inbox until a URL matching `url_pattern` arrives."""
        if not self._backend:
            raise MailboxError("create_mailbox() must be called before polling")

        deadline = time.time() + timeout_secs
        interval = first_interval
        seen: set = set()

        while time.time() < deadline:
            for msg in self.check_messages():
                mid = msg.get("id")
                if mid in seen:
                    continue
                seen.add(mid)

                text = msg.get("body") or self.read_message(mid)
                match = re.search(url_pattern, text or "")
                if match:
                    return match.group(0).rstrip(".,;)\"'")

            time.sleep(interval)
            interval = min(interval * 1.3, max_interval)

        return None
