# 本地部署说明

本仓库是**通用模板**，不含任何个人路径或凭据。本地使用时按下面步骤配置。

## 1. 安装技能

将 `joinquant-workflow/` 目录复制到 Codex 技能目录：

```powershell
# Windows
$dst = "$env:USERPROFILE\.codex\skills\joinquant-workflow"
Copy-Item -Recurse -Force .\joinquant-workflow $dst
```

## 2. 替换路径占位符

打开 `SKILL.md` 与 `references/runbook.md`，把以下占位符替换为本机实际路径：

| 占位符 | 含义 |
|---|---|
| `<PROFILE_DIR>` | playwright 持久化浏览器配置目录 |
| `<WORK>` | 会话/临时工作目录 |
| `<STRATEGY_ROOT>` | 策略代码根目录 |
| `<VAULT>` | Obsidian 资料库根目录 |
| `<EXPORT_ROOT>` | CSV 导出根目录 |
| `<LOG_ROOT>` | 工作日志目录 |

## 3. 配置凭据（可选，用于会话过期后自动登录）

凭据文件 `%USERPROFILE%\.joinquant-credentials.json`，密码使用 Windows DPAPI 加密，磁盘无明文：

```powershell
$phone = '13800000000'
$pw = Read-Host -AsSecureString '请输入聚宽密码'
$enc = ConvertFrom-SecureString $pw
@{ phone = $phone; password_enc = $enc } | ConvertTo-Json |
    Set-Content -LiteralPath "$env:USERPROFILE\.joinquant-credentials.json" -Encoding UTF8
```

`scripts/jq_get_credentials.ps1` 会自动读取并解密（仅当前 Windows 用户可解）。

## 4. 浏览器会话

- 使用 playwright-cli 持久化配置档保存登录态；登录后执行 `state-save <WORK>\jq_auth.json` 备份。
- 会话过期时按 Runbook 的登录步骤重新登录（滑块验证码需人工完成）。

## 5. 依赖

- Node.js（含 `npx`）
- `@playwright/cli`（`npx --yes --package @playwright/cli playwright-cli ...`）
- PowerShell 5.1+、Git

## 6. 与仓库同步

本机技能目录是“运行版”，本仓库是“发布版”。修改流程：

```powershell
# 本地运行版改好后，同步到仓库工作副本并推送
git add -A
git commit -m "feat: ..."
git push
```

> 提交前务必检查：不要提交 `__pycache__`、`jq_auth.json`、`.joinquant-credentials.json`、浏览器配置档等敏感文件（`.gitignore` 已覆盖）。
