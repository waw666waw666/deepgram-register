# Deepgram AutoRegister

> **Automated Registration & $200 Free Credit API Key Harvester for Deepgram Voice AI**  
> Built for zero-configuration, production-grade automated account generation and API key minting.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/playwright-stealth-orange.svg)](https://playwright.dev/)
[![Powered By](https://img.shields.io/badge/Powered%20By-AutoRegister%20Community-purple.svg)](https://github.com/waw666waw666/register-community)

---

## Ecosystem & Backlink Notice

> **Framework Origin**:  
> This standalone tool is derived directly from **[AutoRegister Community](https://github.com/waw666waw666/register-community)**, a general-purpose automated account registration and credential management framework.  
> 
> If you need multi-site orchestration, tri-channel disposable mailbox rotators, lifecycle credential verification, or automated adapter code generation scaffolds, check out our primary repository:  
> 
> **Main Framework Repository**: **[https://github.com/waw666waw666/register-community](https://github.com/waw666waw666/register-community)**

---

## Overview

A hybrid Playwright + REST protocol registration engine tailored for Deepgram (https://console.deepgram.com). Features active Google reCAPTCHA v2 penetration and sub-100ms atomic API key harvesting with official $200 USD free credit allowance.

### Key Highlights

- **$200 USD Free Credit**: New accounts receive $200 official balance without credit card requirements
- **Active reCAPTCHA v2 Penetration**: Automatically resolves checkboxes on clean proxies without human intervention
- **Sub-100ms Key Harvesting**: Pure REST protocol key generation and extraction directly via management API
- **Tri-Channel Disposable Email**: Integrated mail.tm / tempmail.io / guerrillamail fallback polling

---

## Quickstart

### 1. Prerequisites and Installation

Requires **Python ≥ 3.10**:

```bash
# Clone the repository
git clone https://github.com/waw666waw666/deepgram-register.git
cd deepgram-register

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium
```

### 2. Configuration & Crucial Guidance

Copy `config.example.json` to `config.json` to configure proxies or headless mode:

```json
{
  "email": null,
  "browser": {
    "headless": false,
    "slow_mo": 50,
    "timeout": 35000,
    "channel": "chrome",
    "proxy": "http://127.0.0.1:7897"
  },
  "output_dir": "./results"
}
```

### Crucial: Mailbox Configuration & Captcha Guidance

1. **Custom Mailbox Recommended (100% Success Guarantee)**:
   - Deepgram explicitly blacklists common disposable email domains (such as mail.tm);
   - Strongly recommend providing your own Outlook, Gmail, or custom domain email in `config.json`:
     ```json
     {
       "email": "your_personal_email@outlook.com",
       "browser": {
         "headless": false,
         "proxy": "http://127.0.0.1:7897"
       }
     }
     ```
2. **Human-in-the-Loop Verification**:
   - Run in headed mode on your desktop (double-click `run.bat` and select 1);
   - When Google reCAPTCHA v2 appears, check the box in the Chrome window;
   - Click the confirmation link in the received activation email;
   - The script immediately executes pure REST protocols to extract and save the $200 API Key to `results/accounts.txt`.

### 3. Execution

Launch via **`run.bat`** on Windows or execute directly via CLI:

```bash
# Mint 1 account & API key
python main.py

# Batch generate multiple accounts
python main.py -n 5

# Run headlessly in the background
python main.py --headless -n 1
```

Extracted credentials will be safely recorded in **`results/accounts.txt`**:
```text
email----password----api_key----timestamp
```

---

## Ecosystem Portfolio

Part of the AutoRegister open-source automation family:

| Standalone Project | Characteristics | Source Repository |
| :--- | :--- | :--- |
| **AutoRegister Community** | General Registration Engine & Scaffolding | [GitHub](https://github.com/waw666waw666/register-community) |
| **Deepgram AutoRegister** | $200 USD Allowance + reCAPTCHA v2 Penetration | [GitHub](https://github.com/waw666waw666/deepgram-register) |
| **100MilionSeek AutoRegister** | 100M Tokens/day + Instant Card Key Harvester | [GitHub](https://github.com/waw666waw666/100milionseek-register) |
| **AMD AI Dev AutoRegister** | Official AMD Program + Akamai Telemetry Parity | [GitHub](https://github.com/waw666waw666/amd-register) |
| **Coarena AutoRegister** | Post-OAuth Pure REST Protocol Key Minting | [GitHub](https://github.com/waw666waw666/coarena-register) |

---

## Legal Disclaimer

This project is intended strictly for authorized educational research, browser automation benchmarking, and legitimate quality assurance. Users must strictly adhere to the target platform's Terms of Service and all applicable regional laws. See [DISCLAIMER.md](DISCLAIMER.md).
