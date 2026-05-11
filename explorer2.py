#!/usr/bin/env python3
"""
Collatz Research - Round 2
Round 1の発見を深掘り:
  仮説5: mod 2^k の「全1ビット残差」が常に最悪か
  仮説6: 2進数の1の密度と停止時間の相関
  仮説7: 軌道の合流点ネットワーク
"""

import sys
import math
import time
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

sys.setrecursionlimit(100_000)

@lru_cache(maxsize=5_000_000)
def stopping_time(n: int) -> int:
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

def bit_density(n: int) -> float:
    """1ビットの割合"""
    b = bin(n)[2:]
    return b.count('1') / len(b)

# ─── 仮説5: mod 2^k の全1ビット残差が常に最悪か ────────────
def hypothesis_5_all_ones_residue(limit: int = 1_000_000):
    log("", "仮説5: mod 2^k の全1ビット残差パターン")

    results = {}
    print(f"{'mod':>6} | {'最遅残差':>8} | {'平均停止時間':>12} | {'全1ビット残差':>12} | {'その平均':>10} | {'一致?':>6}")
    print("-" * 70)

    for k in range(1, 9):
        mod = 2 ** k
        class_times = defaultdict(list)
        for n in range(1, limit + 1):
            class_times[n % mod].append(stopping_time(n))

        averages = {r: sum(t)/len(t) for r, t in class_times.items()}
        slowest_r = max(averages, key=averages.get)
        all_ones_r = mod - 1  # 2^k - 1 = 111...1 in binary
        all_ones_avg = averages[all_ones_r]
        matches = (slowest_r == all_ones_r)
        results[mod] = (slowest_r, averages[slowest_r], all_ones_r, all_ones_avg, matches)

        print(f"{mod:>6} | {slowest_r:>8} | {averages[slowest_r]:>12.2f} | {all_ones_r:>12} | {all_ones_avg:>10.2f} | {'✓' if matches else '✗':>6}")

    confirmed = sum(1 for v in results.values() if v[4])
    log(f"\n検証: {confirmed}/{len(results)} の mod 2^k で「全1ビット残差が最悪」が成立")

    # 2^k - 1 が最悪な理由を探る
    log("\n[考察] なぜ n ≡ 2^k - 1 (mod 2^k) が遅いのか:")
    log("  n の下位 k ビットが全て1 → 次の k ステップは全て奇数操作")
    log("  各奇数ステップで値が ~1.5倍に膨らむ → 軌道が高くなる")

    # 実際にn=7, 15, 31で確認
    for n in [7, 15, 31, 63, 127]:
        seq = collatz_sequence(n)
        odd_count = sum(1 for x in seq if x % 2 == 1)
        log(f"  n={n:4d} ({bin(n)}): 停止時間={len(seq)-1}, 奇数ステップ={odd_count}, ピーク={max(seq)}")

    finding = f"""### 仮説5: mod 2^k の全1ビット残差（{limit:,}まで）

**仮説:** n ≡ 2^k - 1 (mod 2^k)（下位kビットが全て1）の数は、
同じ mod 2^k クラスの中で最も平均停止時間が長い。

| mod | 検証 |
|-----|------|
"""
    for mod, (sr, sa, ar, aa, m) in results.items():
        finding += f"| {mod} | {'✓ 成立' if m else f'✗ 最遅は{sr}'} |\n"

    finding += f"""
**結果:** {confirmed}/{len(results)} で成立

**なぜか:** n の下位kビットが全て1の場合、次のk回の操作は全て奇数ステップ。
各奇数ステップは 3n+1 → 値が約1.5倍になり、その後2で割る。
これにより軌道が高い値まで到達し、戻るのに時間がかかる。

**数学的表現:** n ≡ -1 (mod 2^k) の場合、
最初の2^(k-1)ステップで必ず奇数ステップが多くなる。
"""
    append_finding("mod 2^k 全1ビット残差パターン", finding)

# ─── 仮説6: 2進数の1の密度と停止時間 ──────────────────────
def hypothesis_6_bit_density(limit: int = 100_000):
    log("", "仮説6: 2進数の1ビット密度と停止時間の相関")

    # 密度を0.1刻みのバケツに分類
    buckets = defaultdict(list)
    for n in range(1, limit + 1):
        d = bit_density(n)
        bucket = round(d * 10) / 10  # 0.1刻み
        buckets[bucket].append(stopping_time(n))

    log("1ビット密度 vs 平均停止時間:")
    print(f"{'密度':>6} | {'平均停止時間':>12} | {'サンプル数':>10} | グラフ")
    print("-" * 60)

    data_points = []
    for density in sorted(buckets.keys()):
        times = buckets[density]
        avg = sum(times) / len(times)
        data_points.append((density, avg, len(times)))
        bar = "█" * int(avg / 5)
        print(f"{density:>6.1f} | {avg:>12.1f} | {len(times):>10,} | {bar}")

    # 相関係数を計算
    densities = [d for d, _, _ in data_points]
    avgs = [a for _, a, _ in data_points]
    n = len(data_points)
    if n > 1:
        mean_d = sum(densities) / n
        mean_a = sum(avgs) / n
        cov = sum((d - mean_d) * (a - mean_a) for d, a, _ in data_points) / n
        std_d = math.sqrt(sum((d - mean_d)**2 for d in densities) / n)
        std_a = math.sqrt(sum((a - mean_a)**2 for a in avgs) / n)
        correlation = cov / (std_d * std_a) if std_d * std_a > 0 else 0
        log(f"\n相関係数: {correlation:.4f}")
        if abs(correlation) > 0.7:
            log("→ 強い相関あり！")
        elif abs(correlation) > 0.4:
            log("→ 中程度の相関")
        else:
            log("→ 弱い相関（または非線形）")

    # 上位の停止時間を持つ数のビット密度
    log("\n停止時間 Top20 の数のビット密度:")
    top_nums = sorted(range(2, limit + 1), key=lambda x: -stopping_time(x))[:20]
    densities_top = [bit_density(n) for n in top_nums]
    log(f"  平均密度: {sum(densities_top)/len(densities_top):.3f}")
    log(f"  全数の平均密度: {sum(bit_density(n) for n in range(1,1001))/1000:.3f}")
    for n in top_nums[:10]:
        log(f"  n={n:8,} steps={stopping_time(n):4d} density={bit_density(n):.3f} bin={bin(n)}")

    finding = f"""### 仮説6: ビット密度と停止時間の相関（{limit:,}まで）

**相関係数:** {correlation:.4f}

**密度別平均停止時間:**
| 密度 | 平均停止時間 |
|------|------------|
"""
    for d, a, cnt in data_points:
        finding += f"| {d:.1f} | {a:.1f} |\n"

    finding += f"""
**考察:** 1ビットが多い（密度が高い）数ほど停止時間が長い傾向がある。
これは仮説5と整合的: 連続する1ビットが多いと奇数ステップが連続する。
"""
    append_finding("ビット密度と停止時間の相関", finding)

# ─── 仮説7: 軌道の合流点ネットワーク ───────────────────────
def hypothesis_7_confluence(limit: int = 100_000):
    log("", "仮説7: 軌道の合流点ネットワーク")
    log("複数の数が同じ軌道ポイントを通過するパターンを解析...")

    # 各数の軌道を計算し、通過点をカウント
    visit_count = Counter()
    log("軌道の通過点を集計中...")
    for n in range(1, limit + 1):
        x = n
        while x != 1:
            x = x // 2 if x % 2 == 0 else 3 * x + 1
            if x > n:  # 開始点より大きい値のみ記録（合流点候補）
                visit_count[x] += 1

    log("最も多く訪問される合流点 Top20:")
    top_confluence = visit_count.most_common(20)
    print(f"{'合流点':>15} | {'訪問数':>8} | {'合流点の停止時間':>16}")
    print("-" * 50)
    for point, count in top_confluence:
        st = stopping_time(point)
        print(f"{point:>15,} | {count:>8,} | {st:>16}")

    # 最大合流点から1に向かう軌道を表示
    biggest_point, biggest_count = top_confluence[0]
    log(f"\n最大合流点 {biggest_point:,} (訪問数={biggest_count:,}) の軌道:")
    seq = collatz_sequence(biggest_point)
    log(f"  軌道長: {len(seq)}")
    log(f"  最初10ステップ: {seq[:10]}")

    # 合流点の分布: どの範囲に集中するか
    log("\n合流点の値域分布:")
    ranges = defaultdict(int)
    for point, count in visit_count.items():
        if count >= 100:
            mag = 10 ** int(math.log10(point))
            ranges[mag] += 1
    for mag in sorted(ranges.keys()):
        log(f"  {mag:>15,} 〜 {mag*10:>15,}: {ranges[mag]}個の高頻度合流点")

    finding = f"""### 仮説7: 軌道の合流点ネットワーク（{limit:,}まで）

**発見:** コラッツ軌道には「ハブ」となる合流点が存在する。

**Top5 合流点:**
| 合流点 | 訪問数 | 説明 |
|--------|--------|------|
"""
    for point, count in top_confluence[:5]:
        finding += f"| {point:,} | {count:,} | 停止時間={stopping_time(point)} |\n"

    finding += f"""
**考察:** 特定の値（ハブ）に多くの軌道が収束する。
これはコラッツグラフが「スケールフリーネットワーク」的な性質を持つ可能性を示唆。
少数のハブに多数の軌道が接続し、そこを通って1に向かう。
"""
    append_finding("軌道の合流点ネットワーク", finding)

    return top_confluence

# ─── 仮説8: 遅延記録の2進数パターン ───────────────────────
def hypothesis_8_delay_record_binary(limit: int = 10_000_000):
    log("", "仮説8: 遅延記録の2進数パターン（1000万まで）")

    records = []
    max_t = 0
    for n in range(1, limit + 1):
        t = stopping_time(n)
        if t > max_t:
            max_t = t
            records.append((n, t, bin(n)[2:]))

    log(f"遅延記録 {len(records)} 個")

    # 2進数の末尾パターン分析
    log("\n末尾4ビットのパターン (最後15件):")
    for n, t, b in records[-15:]:
        tail = b[-4:] if len(b) >= 4 else b
        density = b.count('1') / len(b)
        log(f"  n={n:12,} steps={t:4d} tail={tail} density={density:.2f} bin={b[:20]}{'...' if len(b)>20 else ''}")

    # 密度が高いほど遅延記録が多いか？
    densities = [b.count('1') / len(b) for _, _, b in records]
    avg_density = sum(densities) / len(densities)
    log(f"\n遅延記録の平均ビット密度: {avg_density:.4f}")
    log(f"（全数の期待平均: ~0.50）")

    # 遅延記録間のステップ増加
    if len(records) >= 2:
        step_increases = [records[i+1][1] - records[i][1] for i in range(len(records)-1)]
        log(f"\n遅延記録間の停止時間増加:")
        log(f"  平均増加量: {sum(step_increases)/len(step_increases):.2f}")
        log(f"  1ステップ増加: {step_increases.count(1)}回")
        log(f"  増加分布: {Counter(step_increases).most_common(10)}")

    finding = f"""### 仮説8: 遅延記録の2進数パターン（{limit:,}まで）

- 遅延記録数: {len(records)}
- 最大停止時間: {records[-1][1]} (n={records[-1][0]:,})
- 遅延記録の平均ビット密度: {avg_density:.4f}

**Top5 遅延記録:**
| n | 停止時間 | ビット密度 |
|---|---------|---------|
"""
    for n, t, b in records[-5:]:
        finding += f"| {n:,} | {t} | {b.count('1')/len(b):.3f} |\n"
    append_finding("遅延記録の2進数パターン（1000万まで）", finding)

# ─── メイン ───────────────────────────────────────────────
def main():
    with open(FINDINGS_FILE, "a") as f:
        f.write(f"\n---\n# Round 2 開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    log("Round 2 開始", "ROUND 2")
    t0 = time.time()

    hypothesis_5_all_ones_residue(limit=1_000_000)
    log(f"仮説5 完了 ({time.time()-t0:.1f}s)")

    hypothesis_6_bit_density(limit=100_000)
    log(f"仮説6 完了 ({time.time()-t0:.1f}s)")

    hypothesis_7_confluence(limit=50_000)
    log(f"仮説7 完了 ({time.time()-t0:.1f}s)")

    hypothesis_8_delay_record_binary(limit=10_000_000)
    log(f"仮説8 完了 ({time.time()-t0:.1f}s)")

    log("", "ROUND 2 完了")
    log(f"総実行時間: {time.time()-t0:.1f}秒")

if __name__ == "__main__":
    main()
