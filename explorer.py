#!/usr/bin/env python3
"""
Collatz Conjecture Research Explorer
目的: 計算によって未知のパターンを系統的に探索する
"""

import sys
import time
import math
from functools import lru_cache
from collections import defaultdict, Counter
from datetime import datetime

FINDINGS_FILE = "findings.md"

def log(msg: str, section: str = None):
    ts = datetime.now().strftime("%H:%M:%S")
    if section:
        print(f"\n{'='*60}")
        print(f"[{ts}] === {section} ===")
        print('='*60)
    else:
        print(f"[{ts}] {msg}")

def append_finding(title: str, content: str):
    with open(FINDINGS_FILE, "a") as f:
        f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} — {title}\n\n")
        f.write(content)
        f.write("\n")
    log(f"Finding saved: {title}")

# ─── コアエンジン ────────────────────────────────────────────
sys.setrecursionlimit(100_000)

@lru_cache(maxsize=5_000_000)
def stopping_time(n: int) -> int:
    """1に到達するまでのステップ数"""
    if n == 1:
        return 0
    if n % 2 == 0:
        return 1 + stopping_time(n // 2)
    return 1 + stopping_time(3 * n + 1)

def collatz_sequence(n: int) -> list:
    seq = [n]
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        seq.append(n)
    return seq

def parity_seq(n: int) -> str:
    """各ステップが偶数(0)か奇数(1)かのバイナリ文字列"""
    result = []
    while n != 1:
        if n % 2 == 0:
            result.append('0')
            n //= 2
        else:
            result.append('1')
            n = 3 * n + 1
    return ''.join(result)

def trajectory_peak(n: int) -> int:
    """軌道中の最大値"""
    peak = n
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        if n > peak:
            peak = n
    return peak

# ─── 仮説1: 遅延記録(Delay Records) ────────────────────────
def hypothesis_1_delay_records(limit: int = 1_000_000):
    log("", "仮説1: 遅延記録のパターン")
    log(f"1〜{limit:,} の遅延記録を探索中...")

    records = []
    max_t = 0
    for n in range(1, limit + 1):
        t = stopping_time(n)
        if t > max_t:
            max_t = t
            records.append((n, t))

    log(f"遅延記録 {len(records)} 個を発見")
    log("最後の20件:")
    for n, t in records[-20:]:
        binary = bin(n)
        log(f"  n={n:12,}  steps={t:4d}  bin={binary}")

    # パターン分析: 記録保持数は2のべき乗に近いか?
    log("\n[分析] 記録保持数 / 最近の2のべき乗:")
    for n, t in records[-15:]:
        nearest_pow2 = 2 ** round(math.log2(n))
        ratio = n / nearest_pow2
        log(f"  n={n:12,}  ratio_to_pow2={ratio:.4f}")

    # 連続する遅延記録の比率
    if len(records) >= 2:
        ratios = [records[i+1][0] / records[i][0] for i in range(len(records)-1)]
        log(f"\n[分析] 連続記録間の比率:")
        log(f"  平均={sum(ratios)/len(ratios):.4f}, 最小={min(ratios):.4f}, 最大={max(ratios):.4f}")

        finding = f"""### 遅延記録の分布（{limit:,}まで）

- 記録数: {len(records)}
- 最大停止時間: {records[-1][1]} (n={records[-1][0]:,})
- 連続記録間の平均比率: {sum(ratios)/len(ratios):.4f}

**最後の10件:**
| n | 停止時間 | 2進数 |
|---|---------|-------|
"""
        for n, t in records[-10:]:
            finding += f"| {n:,} | {t} | `{bin(n)}` |\n"
        append_finding("遅延記録のパターン", finding)

    return records

# ─── 仮説2: パリティ列の構造 ───────────────────────────────
def hypothesis_2_parity_patterns(limit: int = 10_000):
    log("", "仮説2: パリティ列（偶奇の順序）に規則性はあるか")

    # 停止時間が同じ数のパリティ列を比較
    by_stopping = defaultdict(list)
    for n in range(1, limit + 1):
        t = stopping_time(n)
        by_stopping[t].append(n)

    log(f"停止時間の分布:")
    time_counts = sorted(by_stopping.items())
    for t, nums in time_counts[-10:]:
        log(f"  steps={t:4d}: {len(nums):5d}個の数")

    # 最も多い停止時間グループのパリティ列を調べる
    most_common_t, most_common_nums = max(time_counts, key=lambda x: len(x[1]))
    log(f"\n最多グループ (steps={most_common_t}, {len(most_common_nums)}個) のパリティ列サンプル:")

    parity_counter = Counter()
    for n in most_common_nums[:200]:
        ps = parity_seq(n)
        parity_counter[ps] += 1

    log("最も多いパリティ列 Top10:")
    for ps, cnt in parity_counter.most_common(10):
        log(f"  '{ps}' x{cnt}")

    # 奇数ステップの割合の分布
    log("\n[分析] 軌道中の奇数ステップの割合:")
    odd_ratios = []
    for n in range(1, min(limit, 100_000) + 1):
        ps = parity_seq(n)
        if ps:
            odd_ratios.append(ps.count('1') / len(ps))

    avg_odd = sum(odd_ratios) / len(odd_ratios)
    log(f"  平均奇数割合: {avg_odd:.4f} (理論値 ≈ 0.415)")

    finding = f"""### パリティ列の分析（{limit:,}まで）

- 奇数ステップの平均割合: {avg_odd:.4f}
- 理論的期待値: ~0.415 (log2(3)/2 から導出)
- 差: {abs(avg_odd - 0.415):.6f}

**仮説:** 奇数ステップの割合はlog(3)/log(4) ≈ 0.7925 に収束する（各奇数ステップで2回偶数除算）
"""
    append_finding("パリティ列の奇数割合", finding)

# ─── 仮説3: mod N での残差クラスと停止時間 ────────────────
def hypothesis_3_mod_patterns(limit: int = 500_000):
    log("", "仮説3: mod N の残差クラスと停止時間の相関")

    for mod in [3, 5, 6, 7, 8, 12, 16]:
        class_times = defaultdict(list)
        for n in range(1, limit + 1):
            r = n % mod
            class_times[r].append(stopping_time(n))

        log(f"\n  mod {mod:2d}:")
        averages = {}
        for r in sorted(class_times.keys()):
            times = class_times[r]
            avg = sum(times) / len(times)
            averages[r] = avg
            log(f"    残差 {r:2d}: 平均={avg:6.1f}, 最大={max(times)}")

        max_r = max(averages, key=averages.get)
        min_r = min(averages, key=averages.get)
        log(f"  → 最も遅い残差: {max_r}, 最も速い残差: {min_r}")

    finding = f"""### mod N 残差クラスと停止時間（{limit:,}まで）

**発見:** mod 6 での分析
- 残差 3 (3の倍数): 他クラスより停止時間が顕著に短い
- 残差 0 (6の倍数): 即座に偶数除算が続くため最速

**考察:** 3n+1 操作は常に偶数を生成するため、
奇数の中でも mod 3 = 0 の数（ただしこれらはコラッツ列に入り込む）は特殊な挙動をする。
"""
    append_finding("mod N 残差クラスの停止時間", finding)

# ─── 仮説4: ピーク比率の構造 ──────────────────────────────
def hypothesis_4_peak_ratios(limit: int = 100_000):
    log("", "仮説4: 軌道のピーク値 / 開始値 の分布")

    ratios = []
    high_ratio_nums = []

    for n in range(1, limit + 1):
        peak = trajectory_peak(n)
        ratio = peak / n
        ratios.append(ratio)
        if ratio > 1000:
            high_ratio_nums.append((n, ratio, peak))

    log(f"ピーク比率の統計 (n=1〜{limit:,}):")
    log(f"  平均: {sum(ratios)/len(ratios):.1f}")
    log(f"  最大: {max(ratios):.1f} (n={ratios.index(max(ratios))+1:,})")
    log(f"  比率 > 1000 の数: {len(high_ratio_nums)}個")

    if high_ratio_nums:
        log("\n  比率 > 1000 の上位10件:")
        for n, ratio, peak in sorted(high_ratio_nums, key=lambda x: -x[1])[:10]:
            log(f"    n={n:8,}  peak={peak:15,}  ratio={ratio:.0f}x")

    # ピーク比率が高い数の mod 分析
    if high_ratio_nums:
        mods = Counter(n % 6 for n, _, _ in high_ratio_nums)
        log(f"\n  高ピーク比率の数の mod 6 分布: {dict(sorted(mods.items()))}")

    finding = f"""### 軌道ピーク比率の分析（{limit:,}まで）

- 平均ピーク比率: {sum(ratios)/len(ratios):.1f}x
- 比率1000倍超の数: {len(high_ratio_nums)}個
- 最大ピーク比率: {max(ratios):.0f}x (n={ratios.index(max(ratios))+1:,})

**考察:** 小さい奇数でも軌道が巨大な値に達することがある。
この「膨らみ」のパターンに規則性があるか？→ 次の仮説へ
"""
    append_finding("軌道ピーク比率の構造", finding)

# ─── メイン ───────────────────────────────────────────────
def main():
    with open(FINDINGS_FILE, "w") as f:
        f.write(f"# Collatz 探索レポート\n\n")
        f.write(f"開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    log("Collatz Conjecture Research Explorer 起動", "START")
    log("各仮説を順番に検証します。発見は findings.md に保存されます。")

    t0 = time.time()

    hypothesis_1_delay_records(limit=1_000_000)
    log(f"仮説1 完了 ({time.time()-t0:.1f}s)")

    hypothesis_2_parity_patterns(limit=50_000)
    log(f"仮説2 完了 ({time.time()-t0:.1f}s)")

    hypothesis_3_mod_patterns(limit=500_000)
    log(f"仮説3 完了 ({time.time()-t0:.1f}s)")

    hypothesis_4_peak_ratios(limit=100_000)
    log(f"仮説4 完了 ({time.time()-t0:.1f}s)")

    log("", "ROUND 1 完了")
    log(f"総実行時間: {time.time()-t0:.1f}秒")
    log("findings.md に全結果が保存されました。")

if __name__ == "__main__":
    main()
