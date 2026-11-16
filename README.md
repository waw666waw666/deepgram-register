<h1 align="center">Deepgram Register</h1>

<p align="center">
  <b>Deepgram 语音 AI 平台自动化注册与 $200 免费额度 API Key 极速直出工具</b><br>
  <i>遵循“开箱即用，极简交付”原则，零复杂配置，一键下号并提取可用 API Key。</i>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-22272e.svg?style=flat-square" alt="License"></a>
  <a href="DISCLAIMER.zh.md"><img src="https://img.shields.io/badge/Disclaimer-Legal%20Terms-red.svg?style=flat-square" alt="Disclaimer"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776ab.svg?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://playwright.dev/"><img src="https://img.shields.io/badge/Playwright-Stealth-2EAD33.svg?style=flat-square&logo=playwright&logoColor=white" alt="Playwright"></a>
  <a href="https://github.com/waw666waw666/RegisterHub"><img src="https://img.shields.io/badge/Powered%20By-RegisterHub-purple.svg?style=flat-square" alt="Powered By"></a>
</p>

<p align="center">
  <a href="./README.md">简体中文</a> | <a href="./README_EN.md">English</a>
</p>

---

## 框架母港与生态互链 (Ecosystem Backlink)

> **项目背景与互相引流说明**：  
> 本独立工程由 **[RegisterHub](https://github.com/waw666waw666/RegisterHub)** 开源注册自动化主框架一键解耦派生。  
> 
> 如果你需要探索**更多站点的自动化支持**（如 Deepgram、100MilionSeek、AMD、Coarena 等）、**三通道公网临时邮箱轮换**、**账号资产全生命周期审计**、或通过**脚手架一键生成新站点适配器**，欢迎前往并 Star 我们的主框架仓库：  
> 
> **主框架项目传送门**：**[https://github.com/waw666waw666/RegisterHub](https://github.com/waw666waw666/RegisterHub)**

---

## 项目简介

基于 Playwright + 纯 REST 协议的混合注册引擎，专为 Deepgram (https://console.deepgram.com) 打造。支持 Google reCAPTCHA v2 主动穿透与 100ms 原子级 API Key 提纯，新号即送 $200 满额使用额度。

### 核心优势与技术特征

- **赠送 $200 美元真金使用额度**：新号开通直接到账 $200 官方余额，无需绑信用卡
- **Google reCAPTCHA v2 主动穿透**：干净代理节点免人工干预，自动定位复选框并打绿勾
- **REST 协议极速提纯**：会话捕获后 100ms 纯后台接口原子直出 40 位标准 API Key
- **三通道公网临时邮箱**：内置 mail.tm / tempmail.io / guerrillamail 自动轮换轮询激活链接

---

## 极速上手

### 1. 环境准备与依赖安装

确保你的系统已安装 **Python ≥ 3.10**：

```bash
# 1. 克隆本项目
git clone https://github.com/waw666waw666/deepgram-register.git
cd deepgram-register

# 2. 安装核心依赖
pip install -r requirements.txt

# 3. 安装 Playwright 浏览器驱动内核
playwright install chromium
```

### 2. 运行配置与核心实操说明

项目根目录提供开箱即用的 `config.example.json`。可复制为 `config.json` 进行配置：

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

### 核心必读：邮箱配置与人机协同实操 (Email & Captcha Guide)

1. **自备真实邮箱配置（100% 成功率保底，强烈推荐）**：
   - Deepgram 官方封禁了公共临时邮箱域名（如 `mail.tm` 等）；
   - 强烈建议在 `config.json` 中配置你自己的真实邮箱（推荐 Outlook、Gmail 或企业域名）：
     ```json
     {
       "email": "your_personal_email@outlook.com",
       "browser": {
         "headless": false,
         "proxy": "http://127.0.0.1:7897"
       }
     }
     ```
2. **真机窗口人机协同**：
   - 必须在桌面有头窗口运行（双击 `run.bat` 选 1）；
   - 表单输入完毕后，若页面弹出 Google reCAPTCHA v2 复选框，在弹出的 Chrome 窗口中轻点一下完成绿勾验证；
   - 收到官方激活邮件后，点击链接激活；
   - 脚本随后将以纯 REST 协议直连官方管理接口，秒级提纯并保存 $200 额度 API Key 至 `results/accounts.txt`！

### 3. 一键启动下号

在 Windows 终端中直接双击 **`run.bat`** 交互菜单，或在命令行运行：

```bash
# 默认生成 1 个账号凭据
python main.py

# 批量生成指定数量账号（如 5 个）
python main.py -n 5

# 无头静默模式运行
python main.py --headless -n 1
```

执行完毕后，所有生成的账号凭据将原子持久化落盘至 **`results/accounts.txt`**：
```text
邮箱----密码----有效API_Key----时间戳
```

### 4. AI 助手协同指南 (Cursor / Claude Code / Windsurf / Gemini)

本项目对 AI 编程助手高度友好，开箱即用：

**前置操作**：使用你的 AI 编程客户端将本子项目文件夹（**`deepgram-register`**）作为独立工作区根目录打开。

载入工作区后，推荐使用以下两种方式引导 AI 协助运行与排障：

- **方法一：直接丢（快捷交互）**：直接向 AI 发送 `请帮我检查本地环境并运行本项目，将新号凭据保存到 results/accounts.txt`。
- **方法二：给步骤（强烈推荐，稳健可靠）**：向 AI 发送：
  1. 检查 Python 依赖与 Playwright 浏览器内核；
  2. 参考 config.example.json 配置 config.json（填入代理或邮箱）；
  3. 执行 python main.py 并在控制台监控运行日志；
  4. 检查 results/accounts.txt 中的成号数据与 API Key 格式。

---

## 体系化生态矩阵

本工程为 RegisterHub 家族核心实战矩阵之一：

| 独立开源项目 | 核心特色与福利 | 源码直达 |
| :--- | :--- | :--- |
| **RegisterHub** | 通用自动化注册母港与脚手架引擎 | [GitHub](https://github.com/waw666waw666/RegisterHub) |
| **Deepgram Register** | 官方 $200 免费额度 + 谷歌人机穿透 + 纯协议提 Key | [GitHub](https://github.com/waw666waw666/deepgram-register) |
| **100MilionSeek Register** | 每天免费 1 亿 Token 算力 + 免收信秒出 Key + 母号裂变 | [GitHub](https://github.com/waw666waw666/100milionseek-register) |
| **AMD AI Dev Register** | AMD 官方大厂计划 + Akamai 遥测 + OneTrust 穿透 | [GitHub](https://github.com/waw666waw666/amd-register) |
| **Coarena Register** | 谷歌登录后 100% 协议提 Key 与每日额度审计 | [GitHub](https://github.com/waw666waw666/coarena-register) |

---

## 免责声明 (Disclaimer)

本项目仅供软件工程自动化、浏览器驾驶协议与网络可用性技术交流与合法测试使用。使用者必须严格遵守目标平台服务条款与当地法律法规，严禁将本项目用于未经授权的大规模滥用或非法用途。作者不对任何因使用本项目造成的损失承担法律责任。详见 [DISCLAIMER.zh.md](DISCLAIMER.zh.md)。

---

## 开发者社区与交流

如果你在账号工程自动化、协议逆向、云端风控自洽或 API Key 提取落地中有任何技术疑问、适配需求或交流想法，欢迎加入我们的开发者社群：

- **QQ 交流群**：1130324020
- **Discord 社区**：[点击加入 Discord](https://discord.gg/USnVJ9YQX)
