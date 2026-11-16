# RegisterHub Community - AI 全自动环境装配与接管协议 (SETUP_FOR_AI.md)

> **面向对象**：在宿主机上运行的 AI 编程助手（Cursor / Claude Code / Windsurf / GitHub Copilot / Gemini 等）。  
> **核心使命**：自主完成开源社区版的新环境探测、依赖补齐、配置自适应装配与闭环验收，**实现使用者“一句话全自动交付，零手动折腾”**。

---

## 0. 给使用者的极简用法

如果你是收到或克隆本项目的使用者，无需手动敲打繁琐命令。直接在你的 AI 客户端输入框中发送以下**一句话**，AI 将自动执行本协议：

```text
@SETUP_FOR_AI.md 请阅读此文档，全自动为我完成当前机器的环境探测、配置装配与健康验收。
```

---

## 1. AI 代理自主接管准则 (Directives for AI Agents)

当你（AI）接收到上述指令后，必须严格遵循**先探测、再装配、后自检、静默闭环**的四步流水线：

```mermaid
flowchart LR
    A["1. 宿主环境探测"] --> B["2. 依赖自动补齐"] --> C["3. 自适应配置装配"] --> D["4. 闭环验收汇报"]
```

---

## 2. 四步自主装配流水线

### 第一步：宿主环境基线探测 (Host Recon)

以只读方式快速探查当前机器的基础设施：

1. **Python 环境**：检查 `python --version`，要求 Python ≥ 3.10；
2. **代理环境嗅探**：
   - 快速探测常见本地代理端口（如 `127.0.0.1:7897` Clash/Mihomo、`:10809` v2rayN）；
   - 若任一端口处于监听状态，记录该地址备用；若无本地代理，检查系统环境变量 `HTTP_PROXY` / `HTTPS_PROXY`；
3. **网络与临时邮箱连通性**：
   - 内置 `core.mail_client.DisposableMailClient` 会自动调度 `mail.tm` / `tempmail.io` / `guerrillamail` 三大公网临时邮箱服务，无需本地 Docker，无需任何密钥。

---

### 第二步：依赖全自动补齐 (Auto Dependencies)

在当前项目根目录下执行安装与内核拉取：

```bash
# 1. 安装核心 Python 依赖
pip install -r requirements.txt

# 2. 安装 Playwright Chromium 浏览器内核
playwright install chromium
```

---

### 第三步：自适应生产配置装配 (Config Auto-Provisioning)

若项目根目录下不存在 `config.json`：

1. 读取 `config.example.json` 作为基准模板复制为 `config.json`；
2. **智能注入代理配置**：
   - 若第一步探测到了本地活跃代理端口（如 `http://127.0.0.1:7897`），自动填入 `browser.proxy` 字段；
   - 若未探测到任何代理，保留 `browser.proxy: null`；
3. **确保临时邮箱默认启用**：
   - 确认 `defaults.use_disposable_mail` 为 `true`，开箱即用。

---

### 第四步：全自动化验收与交付汇报 (Verification & Handover)

在终端运行体检与单元测试，断言系统 100% 具备运行能力：

```bash
# 1. 执行回归单元测试（验证无语法与导入撕裂）
pytest tests/

# 2. 运行内置离线 Base64 靶场验证完整端到端生命周期
python main.py demo
```

测试全绿且 Demo 运行通过后，向使用者输出**高信号交付汇报**：

```text
【RegisterHub Community 部署完成】

1. 当前环境配置：
   - 运行环境：Python 3.x / Playwright Chromium 已就绪
   - 代理策略：已自动绑定至 http://127.0.0.1:XXXX（或当前为直连模式）
   - 临时邮箱：已启用三通道自动故障转移模式 (mail.tm / tempmail.io / guerrillamail)
2. 验收结果：
   - 单元测试覆盖：6/6 项测试全部通过
   - 离线靶场验证：通过 (Task [1/1] finished successfully)
3. 立即启动使用：
   - 运行指定适配器：python main.py <site_name>（可选: demo, quanticdata, deepgram, amd, coarena, milionseek, automation_exercise）
   - 交互式运行菜单：双击运行 run.bat
```

---

## 3. 常见异常自愈指南 (Self-Healing Directives)

- **遇到境外站点无法访问**：提示用户启动其本机的网络代理工具（如 Clash），并自动将代理地址写入 `config.json`；
- **遇到临时邮箱限速 (HTTP 429)**：客户端内置三后端自动轮换，无需人工干预，会自动切换至下一个可用节点；
- **绝不破坏现场**：在执行配置与代码读写时，只修改当前项目内部文件，严禁扫描或改动宿主计算机上的无关私人目录。
