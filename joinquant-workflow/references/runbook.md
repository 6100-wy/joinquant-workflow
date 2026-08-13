# 聚宽 Runbook（详细命令）

> 路径占位符：`<PROFILE_DIR>` / `<WORK>` / `<STRATEGY_ROOT>` / `<VAULT>` / `<EXPORT_ROOT>` / `<LOG_ROOT>`，按本机实际路径替换。

## 目录

1. 浏览器与会话
2. 收盘例行工作分步命令
3. 资料库/日志更新模板
4. 代码注入与回测
5. 常见问题

## 1. 浏览器与会话

```powershell
# 查看会话
npx --yes --package @playwright/cli playwright-cli tab-list

# 重启（有登录态时无头即可）
npx --yes --package @playwright/cli playwright-cli open "https://www.joinquant.com/algorithm/trade/list" --persistent --profile "<PROFILE_DIR>" --browser chrome

# 需要用户登录时加 --headed，登录后保存状态
npx --yes --package @playwright/cli playwright-cli state-save "<WORK>\jq_auth.json"
```

凭据文件 `$env:USERPROFILE\.joinquant-credentials.json`（密码经 Windows DPAPI 加密，磁盘无明文）：
```json
{"phone": "13800000000", "password_enc": "<DPAPI 加密串>"}
```
读取解密：`powershell -File <skill>/scripts/jq_get_credentials.ps1`（输出 `phone=...` 与 `password=...` 两行）。密码只在本机当前用户下可解。
登录步骤：`find "密码登录"` 点击 → `fill` 手机号/密码输入框 → 勾选协议复选框 → `click` “登 录”。出现验证码则请用户在可见窗口完成。
注意：`fill` 命令会把密码明文出现在命令日志中，属本机自动登录的固有行为；凭据文件本身保持加密。

## 2. 收盘例行工作分步命令

### 读列表页
```powershell
npx --yes --package @playwright/cli playwright-cli eval "() => { const t = document.querySelector('table'); return t ? t.innerText : 'no table'; }"
```
期望列：`名称 | 频率 | 状态 | 开始时间 | 累计收益 | 年化收益 | 今日收益 | 最大回撤 | 微信通知 | 时限`。

### 逐策略导出（三个策略重复）
```powershell
# 1) 在列表页找到策略链接并点击（会开新标签）
npx --yes --package @playwright/cli playwright-cli find "重点关注_3ETF-模拟交易"   # 记下 link ref
npx --yes --package @playwright/cli playwright-cli click <ref>
# 2) 切到新标签，找到两个“导出全部”链接
npx --yes --package @playwright/cli playwright-cli tab-select <N>
npx --yes --package @playwright/cli playwright-cli snapshot   # 记下持仓/下单两个 export ref
# 3) 逐个点击导出并立即复制（同名覆盖！）
npx --yes --package @playwright/cli playwright-cli click <posRef>
Start-Sleep -Seconds 4
Copy-Item ".playwright-cli\live-position-list.csv" "<EXPORT_ROOT>\<YYYY-MM-DD>\3ETF_positions.csv" -Force
npx --yes --package @playwright/cli playwright-cli click <txnRef>
Start-Sleep -Seconds 4
Copy-Item ".playwright-cli\live-transaction-list.csv" "<EXPORT_ROOT>\<YYYY-MM-DD>\3ETF_transactions.csv" -Force
```
策略名映射：`重点关注_3ETF`、`重点关注_2ETF`、`双龙出海_五福x2.0合并版`。

### 日志核对
```powershell
npx --yes --package @playwright/cli playwright-cli find "日志"; npx --yes --package @playwright/cli playwright-cli click <ref>
npx --yes --package @playwright/cli playwright-cli eval "() => { /* 取日志容器文本，统计 ERROR/Traceback，检查今日行 */ }"
```
重点：ERROR=0；成交价 vs 预估含成本价差 ≤ 千一；无漏单；走弱期判定与持仓一致；14:55 强制买入标的记录在案。

### 对账
```powershell
python <skill>/scripts/jq_daily_analyze.py "<EXPORT_ROOT>\<YYYY-MM-DD>" <3ETF累计> <2ETF累计> <双龙累计>
```

## 3. 资料库/日志更新模板

### 收盘观察（资料库 `07-股票投资\复盘\YYYY-MM-DD_收盘观察.md`）
```
---
tags: 复盘
日期: YYYY-MM-DD
---
# YYYY-MM-DD 收盘观察（第 N 个交易日）
## 页面收益（最终值）  表格：累计/年化/今日/回撤
## 今日动作（各策略买卖/换仓/无交易）
## 日志核对（0 报错 / 滑点 / 信号与持仓一致 / 对账差异）
## 观察点（只记录不干预：持仓集中度、Regime 分歧、14:55 强制买入标的等）
## 关联（三张策略笔记、首页、上一份复盘）
```

### 工作日志（`<LOG_ROOT>\复盘记录_YYYY-MM-DD.md`）
按既有格式追加：背景与目标、页面收益、今日动作、日志核对、观察点、数据文件。

## 4. 代码注入与回测

### 注入 Ace 编辑器（本地文件 → 页面）
1. 起本地 CORS 服务（`http.server` 加 `Access-Control-Allow-Origin: *`，目录指向含策略文件的文件夹）。
2. 在编辑器页执行：
```js
async () => {
  const resp = await fetch('http://127.0.0.1:<port>/<file>.py');
  const code = await resp.text();
  const el = document.querySelector('.ace_editor');
  const editor = el && el.env ? el.env.editor : null;
  if (!editor) return 'no-ace';
  editor.setValue(code, -1);
  editor.clearSelection();
  return 'set len=' + editor.getValue().length;
}
```
3. 确认页面显示“已保存”。

### 回测参数
- 开始：`2020-01-01`；结束：**前一个交易日**（页面会拒绝“今天”）；资金：100000；频率：分钟；Python3。
- 日期输入是 jQuery datepicker，用 eval 设置 `input.datepicker` 的 value 并派发 `change`。
- 频率：点“每天”按钮 → 菜单选“分钟”。
- 运行后轮询 `状态：` 文本直到“回测完成”；读取指标：策略收益/年化/超额/基准/Alpha/Beta/夏普/胜率/盈亏比/最大回撤（含区间）/波动率/盈利次数。

## 5. 常见问题

- **浏览器“is already in use”**：Chrome 配置档被占用；改用独立 `pw_jq_profile`，或先 `playwright-cli close`。
- **eval 中文/引号被拆**：用 `--raw` 导出 JSON 字符串到文件再解码；复杂代码写成脚本文件执行。
- **下载文件未找到**：playwright-cli 下载落在当前目录的 `.playwright-cli\` 下（`live-position-list.csv` / `live-transaction-list.csv`），逐次立即复制。
- **CSV 编码**：GBK/UTF-8 都可能，读取时先试 `utf-8-sig` 再 `gb18030`。
- **结束时间不能大于前一个交易日**：结束日期设为 `(今天-1)`，非交易日取最近交易日。
