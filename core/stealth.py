"""
Fingerprint & Stealth Enhancement Engine.
Provides client-side fingerprint masking and external Anti-Detect/Fingerprint browser CDP connection.
"""
from typing import Optional, Dict, Any
from playwright.sync_api import BrowserContext, Browser, Playwright


# JavaScript payload to mask automation traces and harmonize browser fingerprints
STEALTH_JS_PAYLOAD = """
(() => {
    // 1. Ensure navigator.webdriver is boolean false
    Object.defineProperty(navigator, 'webdriver', {
        get: () => false,
        configurable: true
    });

    // 2. Harmonize window.chrome
    if (!window.chrome) {
        window.chrome = {};
    }
    if (!window.chrome.runtime) {
        window.chrome.runtime = {
            PlatformOs: { MAC: 'mac', WIN: 'win', ANDROID: 'android', CROS: 'cros', LINUX: 'linux', OPENBSD: 'openbsd' },
            PlatformArch: { ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64', MIPS: 'mips', MIPS64: 'mips64' },
            PlatformNaclArch: { ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64', MIPS: 'mips', MIPS64: 'mips64' }
        };
    }

    // 3. Harmonize notification permissions
    if (window.Notification) {
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );
    }
})();
"""


def apply_stealth_to_context(context: BrowserContext):
    """Inject anti-fingerprint masking scripts into all pages before load."""
    context.add_init_script(STEALTH_JS_PAYLOAD)


def connect_fingerprint_browser(playwright: Playwright, cdp_endpoint: str) -> Browser:
    """
    Connect to an external anti-detect / fingerprint browser instance via CDP.
    Examples:
      - AdsPower: http://127.0.0.1:50325
      - BitBrowser: http://127.0.0.1:9222
      - Hubstudio: ws://127.0.0.1:9222/devtools/browser/...
    """
    if not cdp_endpoint.startswith("http://") and not cdp_endpoint.startswith("https://") and not cdp_endpoint.startswith("ws://"):
        cdp_endpoint = f"http://127.0.0.1:{cdp_endpoint}"
        
    return playwright.chromium.connect_over_cdp(cdp_endpoint)
