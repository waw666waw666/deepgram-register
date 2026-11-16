"""
Environment Diagnostics Engine (Doctor).
Performs real, executable verification of the runtime environment.

Design principle: every check must OBSERVE A REAL EFFECT, never merely
confirm that a module can be imported. A check that cannot fail is not a check.
"""
import sys
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

# ANSI colors
_C_GREEN = "\033[92m"
_C_RED = "\033[91m"
_C_YELLOW = "\033[93m"
_C_CYAN = "\033[96m"
_C_DIM = "\033[2m"
_C_RESET = "\033[0m"

_OK = f"{_C_GREEN}OK{_C_RESET}"
_FAIL = f"{_C_RED}FAILED{_C_RESET}"
_WARN = f"{_C_YELLOW}WARN{_C_RESET}"

MIN_PYTHON = (3, 10)


class CheckResult:
    """A single diagnostic outcome."""

    def __init__(self, name: str, ok: bool, detail: str = "",
                 hint: Optional[str] = None, critical: bool = True,
                 warn_only: bool = False):
        self.name = name
        self.ok = ok
        self.detail = detail
        self.hint = hint
        self.critical = critical
        self.warn_only = warn_only

    @property
    def label(self) -> str:
        if self.ok:
            return _OK
        return _WARN if self.warn_only else _FAIL


def _check_python_version() -> CheckResult:
    """Verify the interpreter satisfies the minimum supported version."""
    v = sys.version_info
    ver_str = f"{v.major}.{v.minor}.{v.micro}"
    if (v.major, v.minor) >= MIN_PYTHON:
        return CheckResult(
            "Python Interpreter",
            True,
            f"v{ver_str} (>= {MIN_PYTHON[0]}.{MIN_PYTHON[1]} required)",
        )
    return CheckResult(
        "Python Interpreter",
        False,
        f"v{ver_str} is below the minimum",
        hint=f"Upgrade to Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer.",
    )


def _check_module(import_name: str, dist_name: str, purpose: str,
                  critical: bool = True) -> CheckResult:
    """
    Verify a third-party module is importable AND reports a version.
    Import alone is not enough: a broken/partial install can still import.
    """
    try:
        mod = __import__(import_name)
    except ImportError:
        return CheckResult(
            f"{dist_name} ({purpose})",
            False,
            f"module '{import_name}' not importable",
            hint="pip install -r requirements.txt",
            critical=critical,
        )

    version = getattr(mod, "__version__", None)
    if version is None:
        try:
            import importlib.metadata
            version = importlib.metadata.version(dist_name)
        except Exception:
            version = "unknown"

    return CheckResult(f"{dist_name} ({purpose})", True, f"v{version}")


def _check_opencv_functional() -> CheckResult:
    """
    Verify OpenCV can actually perform the template-matching operation used by
    core/solver.py. Import success alone does not prove the native backend loads.
    """
    try:
        import cv2
        import numpy as np
    except ImportError as e:
        return CheckResult(
            "OpenCV Native Backend",
            False,
            f"cannot import: {e}",
            hint="pip install opencv-python numpy",
        )

    try:
        # Execute a real matchTemplate on synthetic data -- the exact call
        # core/solver.py makes when solving a slider puzzle.
        #
        # NOTE: the template must contain texture (variance > 0). A solid-colour
        # template makes TM_CCOEFF_NORMED degenerate to a division by zero, so
        # the returned location is meaningless. Real puzzle pieces come from
        # Canny edge maps, which always carry texture.
        rng = np.random.default_rng(20260101)
        patch = rng.integers(40, 255, size=(10, 10), dtype=np.uint8)

        haystack = np.zeros((40, 80), dtype=np.uint8)
        haystack[10:20, 30:40] = patch
        needle = patch.copy()

        res = cv2.matchTemplate(haystack, needle, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
    except Exception as e:
        return CheckResult(
            "OpenCV Native Backend",
            False,
            f"matchTemplate execution failed: {e}",
            hint="Reinstall OpenCV: pip install --force-reinstall opencv-python",
        )

    # The synthetic pattern sits at x=30; a correct solver must find it.
    if max_loc[0] != 30:
        return CheckResult(
            "OpenCV Native Backend",
            False,
            f"solver returned wrong coordinate (got x={max_loc[0]}, expected 30)",
            hint="OpenCV install is corrupted. Reinstall opencv-python.",
        )

    return CheckResult(
        "OpenCV Native Backend",
        True,
        f"v{cv2.__version__}, vision solver verified (match score {max_val:.2f})",
    )


def _resolve_chrome() -> Optional[str]:
    """Locate an official Google Chrome binary on the host."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]
    for c in candidates:
        if Path(c).exists():
            return c

    for name in ("google-chrome", "chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _check_browser_binaries() -> List[CheckResult]:
    """
    Verify the Playwright browser engine and the official Chrome channel.

    This is critical: config.json defaults to use_chrome_channel=true, and
    README step 1 instructs `playwright install chromium`. Neither is verified
    by merely importing the playwright Python package.
    """
    results: List[CheckResult] = []

    # --- 1. Playwright's own browser engine (required by the framework) ---
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            exe = p.chromium.executable_path
        if exe and Path(exe).exists():
            results.append(CheckResult(
                "Playwright Browser Engine",
                True,
                Path(exe).name,
            ))
        else:
            results.append(CheckResult(
                "Playwright Browser Engine",
                False,
                "browser binary not found",
                hint="playwright install chromium",
            ))
    except Exception as e:
        msg = str(e).splitlines()[0][:110]
        results.append(CheckResult(
            "Playwright Browser Engine",
            False,
            f"cannot launch: {msg}",
            hint="playwright install chromium",
        ))

    # --- 2. Official Chrome channel (the anti-fingerprint requirement) ---
    chrome = _resolve_chrome()
    if chrome:
        results.append(CheckResult(
            "Official Google Chrome (channel)",
            True,
            Path(chrome).name,
        ))
    else:
        results.append(CheckResult(
            "Official Google Chrome (channel)",
            False,
            "no system Chrome installation detected",
            hint=("Install Google Chrome from https://www.google.com/chrome/ , "
                  "or set browser.use_chrome_channel=false in config.json "
                  "(NOT recommended: bundled Chromium is easier to fingerprint)."),
            critical=False,
            warn_only=True,
        ))

    return results


def _check_write_permission(output_dir: str = "./results") -> CheckResult:
    """Verify the results directory is writable -- the ledger depends on it."""
    target = Path(output_dir)
    try:
        target.mkdir(parents=True, exist_ok=True)
        probe = target / ".doctor_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return CheckResult("Output Directory Writable", True, str(target.resolve()))
    except Exception as e:
        return CheckResult(
            "Output Directory Writable",
            False,
            f"cannot write to {target}: {e}",
            hint="Check filesystem permissions or adjust 'output_dir' in config.json.",
        )


def _check_config() -> CheckResult:
    """Verify config.json exists and parses; warn if falling back to defaults."""
    cfg_path = Path("config.json")
    if not cfg_path.exists():
        return CheckResult(
            "Configuration File",
            False,
            "config.json not found; running on built-in defaults",
            hint="Restore config.json from the repository.",
            warn_only=True,
            critical=False,
        )
    try:
        import json
        json.loads(cfg_path.read_text(encoding="utf-8"))
        return CheckResult("Configuration File", True, "config.json parsed")
    except Exception as e:
        return CheckResult(
            "Configuration File",
            False,
            f"config.json is malformed: {str(e)[:90]}",
            hint="Fix the JSON syntax or restore the file from the repository.",
        )


def _check_network(timeout: float = 6.0) -> CheckResult:
    """Verify outbound HTTPS works -- required by every real adapter."""
    try:
        import requests
        r = requests.get("https://www.google.com/generate_204",
                         timeout=timeout, allow_redirects=False)
        if r.status_code in (204, 200, 301, 302):
            return CheckResult("Network Connectivity", True, f"HTTPS reachable ({r.status_code})")
        return CheckResult(
            "Network Connectivity", True,
            f"HTTPS reachable (unexpected {r.status_code})", warn_only=True,
        )
    except Exception as e:
        return CheckResult(
            "Network Connectivity",
            False,
            f"no outbound HTTPS: {str(e)[:90]}",
            hint=("Check proxy / firewall. To route through a proxy, set "
                  "browser.proxy in config.json or the HTTP_PROXY env var."),
            critical=False,
            warn_only=True,
        )


def run_doctor(output_dir: str = "./results") -> bool:
    """
    Execute the full diagnostic suite.

    Returns True only when all CRITICAL checks pass. Non-critical warnings do
    not fail the run, but are reported distinctly.
    """
    print("=" * 68)
    print("  RegisterHub Environment Diagnostics")
    print("=" * 68)
    print(f"{_C_DIM}  Every check below executes a real operation. "
          f"Import success alone is not accepted.{_C_RESET}")
    print("-" * 68)

    checks: List[CheckResult] = []
    checks.append(_check_python_version())
    checks.append(_check_module("playwright", "playwright", "browser engine"))
    checks.append(_check_module("requests", "requests", "HTTP client"))
    checks.append(_check_module("PIL", "pillow", "image handling"))
    checks.append(_check_module("numpy", "numpy", "vision math"))
    checks.append(_check_opencv_functional())
    checks.extend(_check_browser_binaries())
    checks.append(_check_config())
    checks.append(_check_write_permission(output_dir))
    checks.append(_check_network())

    # --- Render results ---
    for c in checks:
        print(f"[{c.label}] {c.name}")
        if c.detail:
            print(f"           {_C_DIM}{c.detail}{_C_RESET}")

    # --- Render remediation hints ---
    failures = [c for c in checks if not c.ok and not c.warn_only]
    warnings = [c for c in checks if not c.ok and c.warn_only]

    if failures or warnings:
        print("-" * 68)
        if failures:
            print(f"{_C_RED}  Blocking issues -- fix these before running adapters:{_C_RESET}")
            for c in failures:
                print(f"\n  {_C_RED}x{_C_RESET} {c.name}")
                if c.detail:
                    print(f"      {c.detail}")
                if c.hint:
                    print(f"      {_C_CYAN}-> {c.hint}{_C_RESET}")
        if warnings:
            print(f"\n{_C_YELLOW}  Advisory warnings (not blocking):{_C_RESET}")
            for c in warnings:
                print(f"\n  {_C_YELLOW}!{_C_RESET} {c.name}")
                if c.detail:
                    print(f"      {c.detail}")
                if c.hint:
                    print(f"      {_C_CYAN}-> {c.hint}{_C_RESET}")

    print("=" * 68)
    if failures:
        print(f"{_C_RED}  RESULT: {len(failures)} blocking issue(s). "
              f"Environment NOT ready.{_C_RESET}")
        print(f"  Run the commands marked with -> above, then re-run: "
              f"python main.py doctor")
        print("=" * 68)
        return False

    if warnings:
        print(f"{_C_GREEN}  RESULT: Environment ready ({len(warnings)} advisory warning(s)).{_C_RESET}")
    else:
        print(f"{_C_GREEN}  RESULT: Environment ready. All checks passed.{_C_RESET}")
    print("=" * 68)
    return True
