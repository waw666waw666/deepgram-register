"""
Deepgram AutoRegister - Standalone Entry Point.
Powered by AutoRegister Community (https://github.com/waw666waw666/register-community).
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

from core.stealth import apply_stealth_to_context, connect_fingerprint_browser
from core.identity import generate_identity
from adapter import DeepgramAdapter

def load_config() -> dict:
    cfg_file = Path("config.json")
    if not cfg_file.exists():
        cfg_file = Path("config.example.json")
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_account_record(output_dir: Path, account_data: dict):
    output_dir.mkdir(parents=True, exist_ok=True)
    acc_file = output_dir / "accounts.txt"
    email = account_data.get("email", "")
    password = account_data.get("password", "")
    api_key = account_data.get("api_key", "")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    line = f"{email}----{password}----{api_key}----{timestamp}\n"
    with open(acc_file, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"[+] Record appended to {acc_file.resolve()}")

def run_single(config: dict, headless_override=None, proxy_override=None) -> bool:
    b_cfg = config.get("browser", {})
    headless = headless_override if headless_override is not None else b_cfg.get("headless", False)
    proxy_server = proxy_override or b_cfg.get("proxy") or os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")
    channel = b_cfg.get("channel", "chrome")
    slow_mo = b_cfg.get("slow_mo", 50)
    timeout = b_cfg.get("timeout", 35000)
    output_dir = Path(config.get("output_dir", "./results"))

    print("=" * 65)
    print("  Deepgram AutoRegister - Execution Pipeline")
    print("  Channel  :", channel)
    print("  Headless :", headless)
    print("  Proxy    :", proxy_server or "Direct Connection")
    print("=" * 65)

    with sync_playwright() as p:
        browser = None
        launch_kwargs = {
            "headless": headless,
            "slow_mo": slow_mo,
            "args": ["--disable-blink-features=AutomationControlled", "--no-first-run", "--no-default-browser-check"],
            "ignore_default_args": ["--enable-automation"]
        }
        if proxy_server:
            launch_kwargs["proxy"] = {"server": proxy_server}

        try:
            browser = p.chromium.launch(channel=channel, **launch_kwargs)
        except Exception:
            browser = p.chromium.launch(**launch_kwargs)

        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        context.set_default_timeout(timeout)
        apply_stealth_to_context(context)

        page = context.new_page()
        adapter = DeepgramAdapter(page=page, context=context, config=config)

        try:
            print("[*] Preparing synthetic identity...")
            identity = adapter.prepare_identity()

            print("[*] Executing registration form filling...")
            if not adapter.fill_form(identity):
                print("[-] Form filling failed.")
                return False

            print("[*] Executing submission & credential harvesting...")
            if not adapter.submit_and_confirm():
                print("[-] Submission confirmation failed.")
                return False

            print("[+] Registration lifecycle finished successfully!")
            save_account_record(output_dir, adapter.account_data)
            return True

        except Exception as e:
            print(f"[-] Execution error: {e}")
            return False
        finally:
            try:
                context.close()
                browser.close()
            except Exception:
                pass

def main():
    parser = argparse.ArgumentParser(description="Deepgram 语音 AI 平台自动化注册与 $200 免费额度 API Key 极速直出工具")
    parser.add_argument("-n", "--count", type=int, default=1, help="Number of accounts to generate (default: 1)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--proxy", help="Explicit proxy server URL (e.g. http://127.0.0.1:7897)")
    args = parser.parse_args()

    config = load_config()
    total = args.count
    success = 0

    print(f"[*] Starting task run: target {total} accounts...")
    for i in range(1, total + 1):
        print(f"\n>>> Processing Account [{i}/{total}]...")
        if run_single(config, headless_override=args.headless if args.headless else None, proxy_override=args.proxy):
            success += 1
        time.sleep(1.0)

    print(f"\n=================================================================")
    print(f"  Execution Completed: {success}/{total} Succeeded")
    print(f"  Results saved in: {Path(config.get('output_dir', './results')).resolve()}")
    print(f"=================================================================")

if __name__ == "__main__":
    main()
