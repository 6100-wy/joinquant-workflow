# joinquant-workflow

聚宽（JoinQuant）量化日常工作流 Codex 技能：模拟盘收盘监控、盈亏对账、日志核对、复盘记录，以及社区策略发掘、克隆、实盘成本改造与回测评估。

## 功能

- **收盘例行工作**：自动打开聚宽 → 读取三个模拟实盘（重点关注_2ETF / 重点关注_3ETF / 双龙出海）收益与持仓 → 导出持仓/下单 CSV → 对账 → 核对日志（报错、滑点、信号一致性）→ 更新 Obsidian 资料库与工作日志
- **策略发掘与回测**：浏览聚宽社区/策略天梯 → 评估候选策略 → 克隆 → 按实盘成本标准改代码 → 跑回测 → 诚实汇报（回撤、成交真实性、社区风评）
- **纪律**：只记录、不干预；参数改动留待周五复盘并形成书面结论

## 目录结构

```
joinquant-workflow/
├── SKILL.md                        # 技能主文档（流程与规则）
├── agents/openai.yaml              # 技能界面元数据
├── references/
│   ├── runbook.md                  # 详细命令（登录/导出/注入/回测）
│   └── strategy-evaluation.md      # 实盘成本标准与策略评估清单
└── scripts/
    ├── jq_daily_analyze.py         # 收盘对账脚本
    └── jq_get_credentials.ps1      # 读取 DPAPI 加密的聚宽凭据
```

## 安装

1. 克隆本仓库，将 `joinquant-workflow/` 目录复制到 Codex 技能目录：
   - Windows：`C:\Users\<你>\.codex\skills\joinquant-workflow`
2. 按 `SKILL.md` 中的占位符（`<PROFILE_DIR>`、`<STRATEGY_ROOT>`、`<VAULT>` 等）替换为本机路径。
3. 依赖：Node.js（npx）、Playwright CLI（`npx --yes --package @playwright/cli playwright-cli`）、Git Bash/PowerShell。

详细配置（路径替换、加密凭据、浏览器会话、与仓库同步）见 [docs/local-setup.md](docs/local-setup.md)。

## 使用

对 Codex 说：

- “帮我跑今天的聚宽收盘例行工作”
- “看下模拟盘数据 / 对账 / 写收盘复盘”
- “在聚宽论坛找几个策略回测一下”
- “克隆策略 / 改策略成本”

## 配置与安全

- **凭据**：不随仓库分发。本地文件 `%USERPROFILE%\.joinquant-credentials.json` 仅存手机号与 **Windows DPAPI 加密串**（无明文密码），由 `scripts/jq_get_credentials.ps1` 解密使用。
- **会话**：优先使用持久化浏览器配置档与 `state-save` 导出的会话文件；会话过期时才走凭据登录。
- **滑块验证码**：AI 无法自动通过，需要用户在可见浏览器窗口中手动完成一次。
- 请勿把任何密钥、令牌、会话文件（`jq_auth.json`）或本地路径提交到仓库。

## 免责声明

本技能仅用于模拟盘监控与策略研究，不构成投资建议。回测结果不代表未来收益。

## License

MIT
