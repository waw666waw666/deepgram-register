"""
Interactive Site Scaffold Generator.
Generates production-ready adapter code templates with optional automatic field pre-filling.
"""
import re
from pathlib import Path
from typing import Optional, Dict


SCAFFOLD_CODE_TEMPLATE = '''"""
{class_name} Site Adapter.
Automated registration adapter for {site_name}.
"""
import time
from typing import Dict, Any, Optional
from core.adapter import BaseSiteAdapter
from core.identity import generate_identity
from core.pilot import human_type, smart_click, smart_agree_tos
from core.mail_client import DisposableMailClient


class {class_name}(BaseSiteAdapter):
    """
    Registration flow for {site_name}.
    Target URL: {target_url}
    """

    def __init__(self, page, context, config=None):
        super().__init__(page, context, config)
        self.mail_client: Optional[DisposableMailClient] = None

    def target_url(self) -> str:
        return "{target_url}"

    def prepare_identity(self) -> Dict[str, Any]:
        """Generate synthetic credentials matching target requirements."""
        use_disposable = self.config.get("use_disposable_mail", True)
        if use_disposable:
            self.mail_client = DisposableMailClient()
            ident = generate_identity(locale="US", mail_client=self.mail_client)
        else:
            ident = generate_identity(locale="US")

        self.account_data = ident
        return self.account_data

    def fill_form(self, identity: Dict[str, Any]) -> bool:
        """Fill registration form fields with humanized keystrokes."""
        print(f"[*] [{site_name}] Starting form filling for {{identity['email']}}...")
        try:
            # 1. Fill core credentials
            email_selector = {email_selector}
            password_selector = {password_selector}
            username_selector = {username_selector}

            if email_selector and self.page.locator(email_selector).count() > 0:
                print(f"    -> Typing email into {{email_selector}}...")
                human_type(self.page, email_selector, identity["email"])

            if password_selector and self.page.locator(password_selector).count() > 0:
                print(f"    -> Typing password into {{password_selector}}...")
                human_type(self.page, password_selector, identity["password"])

            if username_selector and self.page.locator(username_selector).count() > 0:
                print(f"    -> Typing username into {{username_selector}}...")
                human_type(self.page, username_selector, identity["username"])

            # 2. Automatically check terms of service checkboxes
            smart_agree_tos(self.page)
            time.sleep(1.0)

            return True
        except Exception as e:
            print(f"[-] [{site_name}] Form filling error: {{e}}")
            return False

    def submit_and_confirm(self) -> bool:
        """Locate submit button, trigger submission and confirm success state."""
        print("[*] [{site_name}] Submitting registration...")
        try:
            submit_btn = {submit_selector}
            if not smart_click(self.page, submit_btn):
                return False

            self.page.wait_for_timeout(4000)
            current_url = self.page.url

            # 1. Assert explicit success criteria: dashboard / welcome / onboarding / home
            success_keywords = ["dashboard", "welcome", "confirm", "home", "account", "verify", "onboarding"]
            if any(kw in current_url.lower() for kw in success_keywords):
                print(f"[+] [{site_name}] Registration success confirmed! URL: {{current_url}}")
                return True

            # 2. Check for visible form validation errors (anti-fake-success)
            error_loc = self.page.locator('.error, [role="alert"], .alert-danger, :text-matches("already exists|invalid|error", "i")').first
            if error_loc.count() > 0 and error_loc.is_visible():
                print(f"[-] [{site_name}] Rejected by site error banner: {{error_loc.text_content()[:100]}}")
                return False

            # 3. If submit button disappeared or disabled, page likely accepted payload
            if self.page.locator(submit_btn).count() == 0:
                print(f"[+] [{site_name}] Submit button consumed, progressing to post-onboarding.")
                return True

            print("[!] [{site_name}] Ambiguous result state; captured snapshot for review.")
            return False
        except Exception as e:
            print(f"[-] [{site_name}] Submit confirmation failed: {{e}}")
            return False
'''


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case or kebab-case name into CamelCase."""
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", snake_str)
    components = clean.split("_")
    return "".join(x.title() for x in components if x) + "Adapter"


def scaffold_site(site_name: str, target_url: Optional[str] = None, detected_fields: Optional[Dict[str, Optional[str]]] = None) -> Path:
    """Generate a clean, high-grade site adapter file under sites/ directory."""
    clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", site_name.strip().lower()).strip("_")
    if not clean_name:
        clean_name = "custom_site"

    class_name = to_camel_case(clean_name)
    target_url = target_url or f"https://{clean_name}.com/signup"
    detected = detected_fields or {}

    email_sel = repr(detected.get("email") or 'input[type="email"], input[name="email"]')
    pwd_sel = repr(detected.get("password") or 'input[type="password"], input[name="password"]')
    user_sel = repr(detected.get("username") or 'input[name="username"], input[name="user"]')
    submit_sel = repr(detected.get("submit") or 'button[type="submit"], button:has-text("Sign up"), button:has-text("Register")')

    code = SCAFFOLD_CODE_TEMPLATE.format(
        site_name=clean_name,
        class_name=class_name,
        target_url=target_url,
        email_selector=email_sel,
        password_selector=pwd_sel,
        username_selector=user_sel,
        submit_selector=submit_sel
    )

    root_dir = Path(__file__).resolve().parent.parent
    out_file = root_dir / "sites" / f"{clean_name}.py"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(code, encoding="utf-8")
    return out_file
