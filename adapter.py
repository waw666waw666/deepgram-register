"""
Deepgram Site Adapter.
Automated onboarding adapter for Deepgram Console (https://console.deepgram.com/signup).
Official perk: $200 free credit allowance without credit card requirement.
"""
import time
import re
import requests
from typing import Dict, Any, Optional

from core.adapter import BaseSiteAdapter
from core.identity import generate_identity
from core.pilot import human_type, smart_click
from core.mail_client import DisposableMailClient


class DeepgramAdapter(BaseSiteAdapter):
    """
    Registration adapter for Deepgram Console.
    Target URL: https://console.deepgram.com/signup
    """

    def __init__(self, page, context, config=None):
        super().__init__(page, context, config)
        self.mail_client: Optional[DisposableMailClient] = None
        self.signup_token: Optional[str] = None
        self.api_key: Optional[str] = None

    def target_url(self) -> str:
        return "https://console.deepgram.com/signup"

    def prepare_identity(self) -> Dict[str, Any]:
        """Generate synthetic credentials matching target requirements, supporting custom mailbox."""
        custom_email = self.config.get("email")
        custom_pwd = self.config.get("password")
        if custom_email:
            ident = generate_identity(locale="US")
            ident["email"] = custom_email
            if custom_pwd:
                ident["password"] = custom_pwd
            self.mail_client = None
            self.account_data = ident
            return self.account_data

        use_disposable = self.config.get("defaults", {}).get("use_disposable_mail", self.config.get("use_disposable_mail", True))
        if use_disposable:
            self.mail_client = DisposableMailClient()
            ident = generate_identity(locale="US", mail_client=self.mail_client)
        else:
            ident = generate_identity(locale="US")

        self.account_data = ident
        return self.account_data

    def fill_form(self, identity: Dict[str, Any]) -> bool:
        """Fill Deepgram signup form."""
        self.page.wait_for_selector('#email', timeout=20000)
        self.page.evaluate("() => { document.body.style.zoom = '0.85'; }")

        email = identity["email"]
        password = identity["password"]

        print(f"[*] [Deepgram] Filling credentials: {email}...")
        human_type(self.page, '#email', email)
        time.sleep(0.2)
        human_type(self.page, '#new-password', password)
        time.sleep(0.3)

        return True

    def submit_and_confirm(self) -> bool:
        """Trigger signup, auto-probe Google reCAPTCHA, and extract API Key."""
        btn = self.page.locator('button:has-text("Create account")').first
        smart_click(self.page, btn)

        print("[*] [Deepgram] Probing and auto-clicking Google reCAPTCHA v2 checkbox...")
        # Auto-detect and click reCAPTCHA checkbox inside iframe
        try:
            recaptcha_frame = self.page.frame_locator('iframe[title*="reCAPTCHA"], iframe[src*="recaptcha"]').first
            anchor = recaptcha_frame.locator('#recaptcha-anchor, .recaptcha-checkbox').first
            anchor.wait_for(state="visible", timeout=6000)
            anchor.click()
            print("[+] [Deepgram] Auto-clicked reCAPTCHA checkbox, awaiting verification...")
        except Exception:
            pass

        # Wait for captcha token
        start_wait = time.time()
        captcha_token = None
        while time.time() - start_wait < 60:
            try:
                token = self.page.evaluate("() => window.grecaptcha ? window.grecaptcha.getResponse() : ''")
                if token and len(token) > 20:
                    captcha_token = token
                    print("[+] [Deepgram] Captcha token acquired!")
                    break
            except Exception:
                pass
            time.sleep(1.0)

        if not captcha_token:
            print("[-] [Deepgram] reCAPTCHA challenge did not complete within timeout.")
            return False

        # Execute REST protocol registration
        email = self.account_data["email"]
        password = self.account_data["password"]
        base_url = "https://manage.deepgram.com/v1"
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Origin": "https://console.deepgram.com",
            "Referer": "https://console.deepgram.com/",
        })

        # Copy proxy configuration if set
        proxy_url = self.config.get("browser", {}).get("proxy")
        if proxy_url:
            session.proxies = {"http": proxy_url, "https": proxy_url}

        print("[*] [Deepgram] Submitting registration payload via REST protocol...")
        try:
            r = session.post(f"{base_url}/auth/credentials_signup", json={
                "email": email,
                "password": password,
                "captcha_response": captcha_token,
                "landing_url": "https://console.deepgram.com/signup"
            }, timeout=15)
            if r.status_code not in (200, 201):
                print(f"[-] [Deepgram] Signup failed: {r.status_code} {r.text[:120]}")
                return False
        except Exception as e:
            print(f"[-] [Deepgram] Protocol signup error: {e}")
            return False

        # Poll or prompt for 6-digit email verification code
        code = None
        if self.mail_client:
            print("[*] [Deepgram] Polling public disposable mailbox for 6-digit verification code...")
            code = self.mail_client.poll_for_verification_code(pattern=r'\b\d{6}\b', timeout=90)
        else:
            print(f"\n{'=' * 65}")
            print(f"  [Deepgram] 验证码已发送至自备邮箱: {email}")
            print("  请查收邮件并将 6 位数字验证码粘贴至下方控制台后回车。")
            print(f"{'=' * 65}\n")
            try:
                code = input("[?] 请输入 6 位验证码: ").strip()
            except Exception:
                pass

        if not code:
            print("[-] [Deepgram] Timeout waiting for verification code.")
            return False

        print(f"[+] [Deepgram] Received verification code: {code}")
        r_ver = session.post(f"{base_url}/auth/verify_email", json={"code": code}, timeout=15)
        if r_ver.status_code not in (200, 201):
            print(f"[-] [Deepgram] Verify code failed: {r_ver.status_code}")
            return False

        # Fetch Project ID
        r_proj = session.get(f"{base_url}/projects_with_scopes", timeout=15)
        if r_proj.status_code != 200:
            return False
        projects = r_proj.json().get("projects", [])
        if not projects:
            return False

        p0 = projects[0]
        proj_id = p0.get("project_id") or p0.get("id") or (p0.get("project", {}).get("project_uuid") if isinstance(p0.get("project"), dict) else None)
        if not proj_id:
            return False

        # Issue API Key
        print(f"[*] [Deepgram] Issuing permanent API Key for project: {proj_id}...")
        r_key = session.post(f"{base_url}/projects/{proj_id}/keys", json={
            "comment": "AutoRegister-Key",
            "scopes": ["admin"]
        }, timeout=15)
        if r_key.status_code not in (200, 201):
            return False

        key_data = r_key.json()
        self.api_key = key_data.get("key") or key_data.get("api_key")
        print(f"[★] [Deepgram] Successfully extracted API Key: {self.api_key} ($200 USD allowance)")
        self.account_data["api_key"] = self.api_key
        return True
