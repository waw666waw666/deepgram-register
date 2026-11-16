"""
Heuristic Form Inspector Pro.
Scans modern web registration forms, detecting inputs, TOS checkboxes,
verification code fields, and step-wizard controls.
"""
from typing import Dict, Any, Optional
from playwright.sync_api import Page


class FormInspector:
    """Enhanced heuristic scanner for web registration forms."""

    def __init__(self, page: Page):
        self.page = page

    def detect_inputs(self) -> Dict[str, Optional[str]]:
        """
        Analyze page DOM and return discovered selectors for standard fields:
        email, password, confirm_password, username, fullname, verification_code,
        terms_checkbox, and submit button.
        """
        results: Dict[str, Optional[str]] = {
            "email": None,
            "password": None,
            "confirm_password": None,
            "username": None,
            "fullname": None,
            "verification_code": None,
            "terms_checkbox": None,
            "submit": None,
            "next_step": None
        }

        # 1. Detect Email input
        email_candidates = [
            'input[type="email"]',
            'input[name*="email" i]',
            'input[id*="email" i]',
            'input[placeholder*="email" i]',
            'input[placeholder*="邮箱" i]'
        ]
        for sel in email_candidates:
            loc = self.page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                results["email"] = sel
                break

        # 2. Detect Password inputs (Distinguish password vs confirm_password)
        pwd_locs = self.page.locator('input[type="password"]')
        pwd_count = pwd_locs.count()
        if pwd_count >= 2:
            results["password"] = 'input[type="password"]:nth-of-type(1)'
            results["confirm_password"] = 'input[type="password"]:nth-of-type(2)'
        elif pwd_count == 1 and pwd_locs.first.is_visible():
            results["password"] = 'input[type="password"]'
        else:
            for sel in ['input[name*="password" i]', 'input[id*="password" i]', 'input[placeholder*="密码" i]']:
                loc = self.page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible():
                    results["password"] = sel
                    break

        # 3. Detect Username input
        user_candidates = [
            'input[name*="username" i]',
            'input[id*="username" i]',
            'input[name*="user" i]',
            'input[placeholder*="用户名" i]',
            'input[placeholder*="username" i]'
        ]
        for sel in user_candidates:
            loc = self.page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                results["username"] = sel
                break

        # 4. Detect Fullname / Nickname input
        fullname_candidates = [
            'input[name*="fullname" i]',
            'input[name*="full_name" i]',
            'input[id*="fullname" i]',
            'input[name*="name" i]:not([name*="user" i])',
            'input[placeholder*="姓名" i]',
            'input[placeholder*="Full name" i]'
        ]
        for sel in fullname_candidates:
            loc = self.page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                results["fullname"] = sel
                break

        # 5. Detect Verification Code / OTP input
        otp_candidates = [
            'input[name*="code" i]',
            'input[name*="otp" i]',
            'input[id*="code" i]',
            'input[id*="otp" i]',
            'input[placeholder*="验证码" i]',
            'input[placeholder*="code" i]'
        ]
        for sel in otp_candidates:
            loc = self.page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                results["verification_code"] = sel
                break

        # 6. Detect Terms of Service Checkbox
        tos_candidates = [
            'input[type="checkbox"][name*="terms" i]',
            'input[type="checkbox"][name*="tos" i]',
            'input[type="checkbox"][name*="agree" i]',
            'input[type="checkbox"]'
        ]
        for sel in tos_candidates:
            loc = self.page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                results["terms_checkbox"] = sel
                break

        # 7. Detect Submit or Next-step button
        submit_candidates = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Sign up")',
            'button:has-text("Register")',
            'button:has-text("注册")',
            'button:has-text("Create account")',
            'button:has-text("Submit")'
        ]
        for sel in submit_candidates:
            loc = self.page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                results["submit"] = sel
                break

        next_candidates = [
            'button:has-text("Next")',
            'button:has-text("下一步")',
            'button:has-text("Continue")',
            'button:has-text("继续")'
        ]
        for sel in next_candidates:
            loc = self.page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                results["next_step"] = sel
                break

        return results
