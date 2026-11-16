"""
Humanized Pilot Engine.
Provides natural keyboard typing rhythms, robust clicking, and viewport scrolling.
"""
import time
import random
import functools
from typing import Optional, Union, Callable
from playwright.sync_api import Page, Locator


def retry_on_failure(max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 1.5):
    """
    Decorator that retries browser interactions upon transient network or DOM errors.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_err = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    if attempt < max_retries:
                        time.sleep(delay)
                        delay *= backoff_factor
            raise last_err
        return wrapper
    return decorator


@retry_on_failure(max_retries=3, initial_delay=0.8)
def human_type(page: Page, target: Union[str, Locator], text: str, min_delay: float = 0.03, max_delay: float = 0.09):
    """
    Type text character-by-character with natural human cadence,
    including slight keystroke jitter, to defeat basic keystroke dynamics bot detection.
    """
    loc = page.locator(target) if isinstance(target, str) else target
    loc.wait_for(state="visible", timeout=10000)
    loc.scroll_into_view_if_needed()
    loc.click()
    time.sleep(random.uniform(0.1, 0.2))

    # Clear existing content cleanly
    loc.fill("")
    time.sleep(random.uniform(0.05, 0.1))

    for char in text:
        loc.press_sequentially(char, delay=int(random.uniform(min_delay, max_delay) * 1000))
        # Occasional micro-pause simulating reading / thinking
        if random.random() < 0.08:
            time.sleep(random.uniform(0.1, 0.25))

    time.sleep(random.uniform(0.1, 0.2))


@retry_on_failure(max_retries=2, initial_delay=0.5)
def smart_click(page: Page, target: Union[str, Locator], timeout: int = 15000) -> bool:
    """
    Click an element after ensuring it is visible, in viewport, and enabled (not disabled).
    """
    loc = page.locator(target) if isinstance(target, str) else target
    try:
        loc.wait_for(state="visible", timeout=timeout)
        loc.scroll_into_view_if_needed()
        
        # Wait until button is enabled if it's currently disabled
        start_time = time.time()
        while time.time() - start_time < (timeout / 1000.0):
            if loc.is_enabled():
                break
            time.sleep(0.3)

        # Micro-hover before clicking
        box = loc.bounding_box()
        if box:
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            time.sleep(random.uniform(0.05, 0.15))

        loc.click(timeout=timeout)
        return True
    except Exception as e:
        print(f"[Pilot] Smart click failed on {target}: {e}")
        return False


def smart_agree_tos(page: Page) -> bool:
    """
    Detect and check terms-of-service / privacy policy checkboxes automatically.
    """
    tos_selectors = [
        'input[type="checkbox"][name*="terms" i]',
        'input[type="checkbox"][name*="tos" i]',
        'input[type="checkbox"][name*="agree" i]',
        'input[type="checkbox"][id*="terms" i]',
        'input[type="checkbox"][id*="tos" i]',
        'input[type="checkbox"][id*="agree" i]',
        'label:has-text("Terms") input[type="checkbox"]',
        'label:has-text("Agree") input[type="checkbox"]',
        'label:has-text("同意") input[type="checkbox"]',
        'input[type="checkbox"]'
    ]

    for sel in tos_selectors:
        try:
            locs = page.locator(sel)
            count = locs.count()
            if count > 0:
                for i in range(count):
                    box = locs.nth(i)
                    if box.is_visible() and not box.is_checked():
                        box.check(force=True)
                        time.sleep(random.uniform(0.1, 0.2))
                return True
        except Exception:
            continue
    return False


def smart_create_key_flow(page: Page, default_name: str = "AutoKey", timeout: int = 10000) -> bool:
    """
    Anti-Abort Key Recovery Flow:
    Automatically fills required Name/Description fields in 'Create API Key' modals
    and checks necessary permission checkboxes before confirming, rescuing the asset.
    """
    print(f"[Pilot] Triggering smart_create_key_flow (default_name: {default_name})...")
    name_selectors = [
        'input[name*="name" i]',
        'input[id*="name" i]',
        'input[placeholder*="name" i]',
        'input[placeholder*="Key Name" i]',
        'input[placeholder*="Description" i]',
        'div[role="dialog"] input[type="text"]',
        '.modal input[type="text"]'
    ]

    # 1. Try filling key name
    filled = False
    for sel in name_selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible() and loc.is_enabled():
                val = loc.input_value()
                if not val.strip():
                    loc.fill(default_name)
                    print(f"    -> Filled API key name into {sel}: {default_name}")
                    filled = True
                    break
        except Exception:
            continue

    # 2. Try checking permissions if any checkboxes exist inside dialog
    try:
        dialog_checkboxes = page.locator('div[role="dialog"] input[type="checkbox"], .modal input[type="checkbox"]')
        for i in range(dialog_checkboxes.count()):
            cb = dialog_checkboxes.nth(i)
            if cb.is_visible() and not cb.is_checked():
                cb.check(force=True)
                time.sleep(0.1)
    except Exception:
        pass

    # 3. Click confirmation / generate button
    confirm_selectors = [
        'button:has-text("Create Secret Key")',
        'button:has-text("Create Key")',
        'button:has-text("Create API Key")',
        'button:has-text("Generate")',
        'button:has-text("Generate Key")',
        'button:has-text("Create")',
        'button:has-text("Confirm")',
        'button[type="submit"]'
    ]
    for btn_sel in confirm_selectors:
        try:
            btn = page.locator(btn_sel).first
            if btn.count() > 0 and btn.is_visible() and btn.is_enabled():
                print(f"    -> Clicking key generation button: {btn_sel}")
                btn.click()
                time.sleep(1.0)
                return True
        except Exception:
            continue

    return filled
