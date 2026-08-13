# -*- coding: utf-8 -*-
"""每日收盘后：解析聚宽导出的持仓/下单 CSV，输出盈亏对账摘要。
用法: python jq_daily_analyze.py <导出目录> [累计收益1 累计收益2 累计收益3]
策略顺序: 3ETF, 2ETF, 双龙。累计收益为页面显示的模拟盘累计收益（百分数，如 1.36）。
"""
import sys, io, os, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

STRATEGIES = ["3ETF", "2ETF", "双龙"]


def read_csv(path):
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("gb18030")
    return list(csv.DictReader(io.StringIO(text)))


def analyze(folder):
    rows = []
    for s in STRATEGIES:
        pos_p = os.path.join(folder, f"{s}_positions.csv")
        txn_p = os.path.join(folder, f"{s}_transactions.csv")
        if not (os.path.exists(pos_p) and os.path.exists(txn_p)):
            print(f"[缺失] {s}: 缺少 positions/transactions CSV", flush=True)
            continue
        positions = read_csv(pos_p)
        txns = read_csv(txn_p)
        last_date = max(r["日期"] for r in positions)
        cur = [r for r in positions if r["日期"] == last_date]
        unreal = 0.0
        for r in cur:
            v = r["盈亏/逐笔浮盈"].split("(")[0].replace("%", "").strip()
            try:
                unreal += float(v)
            except ValueError:
                pass
        realized = sum(float(r.get("平仓盈亏") or 0) for r in txns)
        fees = sum(float(r.get("手续费") or 0) for r in txns)
        trades = len(txns)
        rows.append((s, last_date, len(cur), realized, unreal, fees, trades))
    print(f"{'策略':<6}{'持仓日':<12}{'持仓数':<6}{'已实现':>10}{'未实现':>10}{'手续费':>10}{'笔数':>6}")
    for s, d, n, re_, un, fe, tr in rows:
        print(f"{s:<6}{d:<12}{n:<6}{re_:>10.2f}{un:>10.2f}{fe:>10.2f}{tr:>6}")
    if len(sys.argv) > 2 and len(rows) == 3:
        print("\n对账（初始资金 10 万）:")
        for (s, d, n, re_, un, fe, tr), cum in zip(rows, sys.argv[2:5]):
            total = re_ + un - fe
            expect = 100000 * float(cum) / 100
            print(f"  {s}: 权益变化 {total:+.2f} vs 页面累计 {expect:+.2f}  差 {total-expect:+.2f}")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("JQ_EXPORT_ROOT", "")
    if not folder:
        print("用法: python jq_daily_analyze.py <导出目录> [累计收益1 累计收益2 累计收益3]（或设置环境变量 JQ_EXPORT_ROOT）")
        sys.exit(1)
    analyze(folder)
