#!/usr/bin/env python3
"""
Collatz Research - 省メモリ版 夜通し探索
戦略: チャンク処理、再帰なし、キャッシュ上限管理
"""

import sys
import math
import time
import gc
from collections import defaultdict, Counter
from datetime import datetime

FINDINGS_FILE = "/root/collatz/findings.md"
LOG_FILE = "/root/collatz/research.log"

def log(msg: str, section: str = None):
    ts = datetime.now().strftime("%H:%M:%S")
    if section:
        line = f"\n{'='*60}\n[{ts}] === {section} ===\n{'='*60}"
    else:
        line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def save_finding(title: str, content: str):
    with open(FINDINGS_FILE, "a") as f:
        f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} — {title}\n\n")
        f.write(content)
        f.write("\n")
    log(f"★ Finding saved: {title}")

# ─── コア: 反復計算（再帰・大キャッシュなし）─────────────────
def stopping_time_iter(n: int, cache: dict) -> int:
    """反復+小キャッシュで停止時間を計算"""
    path = []
    original = n
    while n != 1 and n not in cache:
        path.append(n)
        n = n // 2 if n % 2 == 0 else 3 * n + 1
    base = 0 if n == 1 else cache[n]
    # キャッシュサイズ制限: 50万件まで
    store = len(cache) < 500_000
    for i, x in enumerate(reversed(path)):
        t = base + i + 1
        if store:
            cache[x] = t
    return base + len(path)

def build_cache_range(lo: int, hi: int) -> dict:
    """lo〜hiの停止時間を一括計算して辞書で返す"""
    cache = {}
    for n in range(lo, hi + 1):
        stopping_time_iter(n, cache)
    return cache

def bit_density(n: int) -> float:
    b = bin(n)[2:]
    return b.count('1') / len(b)

def trajectory_peak(n: int) -> int:
    peak = n
    x = n
    while x != 1:
        x = x // 2 if x % 2 == 0 else 3 * x + 1
        if x > peak:
            peak = x
    return peak

# ─── 仮説5: mod 2^k の全1ビット残差（省メモリ版）────────────
def h5_mod_power2(limit: int = 2_000_000):
    log("", f"仮説5: mod 2^k 全1ビット残差 (limit={limit:,})")

    CHUNK = 100_000
    # 各 mod に対する残差別の累積停止時間と件数
    MOD_LIST = [2**k for k in range(1, 9)]
    sums = {m: defaultdict(int) for m in MOD_LIST}
    counts = {m: defaultdict(int) for m in MOD_LIST}

    cache = {}
    for lo in range(1, limit + 1, CHUNK):
        hi = min(lo + CHUNK - 1, limit)
        for n in range(lo, hi + 1):
            t = stopping_time_iter(n, cache)
            for m in MOD_LIST:
                r = n % m
                sums[m][r] += t
                counts[m][r] += 1
        # キャッシュ肥大化を防ぐ
        if len(cache) > 600_000:
            cache.clear()
        log(f"  チャンク {lo:,}〜{hi:,} 完了 (cache={len(cache):,})")

    log("\n結果:")
    finding = f"### 仮説5: mod 2^k 全1ビット残差パターン ({limit:,}まで)\n\n"
    finding += "| mod | 全1ビット残差 | その平均停止時間 | 最遅残差 | 最遅平均 | 一致? |\n"
    finding += "|-----|------------|--------------|--------|--------|------|\n"

    all_confirmed = True
    for m in MOD_LIST:
        avgs = {r: sums[m][r] / counts[m][r] for r in sums[m]}
        slowest_r = max(avgs, key=avgs.get)
        all_ones_r = m - 1
        all_ones_avg = avgs.get(all_ones_r, 0)
        match = (slowest_r == all_ones_r)
        if not match:
            all_confirmed = False
        sym = "✓" if match else "✗"
        log(f"  mod {m:3d}: 全1ビット残差={all_ones_r:3d} avg={all_ones_avg:.1f} | 最遅={slowest_r:3d} avg={avgs[slowest_r]:.1f} {sym}")
        finding += f"| {m} | {all_ones_r} | {all_ones_avg:.1f} | {slowest_r} | {avgs[slowest_r]:.1f} | {sym} |\n"

    conclusion = "**全mod 2^k で成立**" if all_confirmed else "**一部で不成立**"
    finding += f"\n**結論:** {conclusion}\n"
    save_finding("仮説5: mod 2^k 全1ビット残差 (2M)", finding)

# ─── 仮説6: ビット密度と停止時間 ────────────────────────────
def h6_bit_density(limit: int = 1_000_000):
    log("", f"仮説6: ビット密度と停止時間の相関 (limit={limit:,})")

    CHUNK = 100_000
    cache = {}
    bucket_sum = defaultdict(float)
    bucket_cnt = defaultdict(int)
    top_records = []  # (stopping_time, n, density)

    for lo in range(1, limit + 1, CHUNK):
        hi = min(lo + CHUNK - 1, limit)
        for n in range(lo, hi + 1):
            t = stopping_time_iter(n, cache)
            d = bit_density(n)
            bucket = round(d * 10) / 10
            bucket_sum[bucket] += t
            bucket_cnt[bucket] += 1
            top_records.append((t, n, d))
        top_records.sort(reverse=True)
        top_records = top_records[:50]  # 上位50件のみ保持
        if len(cache) > 600_000:
            cache.clear()
        log(f"  チャンク {lo:,}〜{hi:,} 完了")

    log("\nビット密度 vs 平均停止時間:")
    data = []
    for density in sorted(bucket_sum.keys()):
        avg = bucket_sum[density] / bucket_cnt[density]
        data.append((density, avg, bucket_cnt[density]))
        bar = "█" * int(avg / 8)
        log(f"  {density:.1f}: {avg:6.1f} {bar}")

    # 相関係数
    ds = [d for d, _, _ in data]
    avgs = [a for _, a, _ in data]
    n = len(data)
    mean_d = sum(ds) / n
    mean_a = sum(avgs) / n
    cov = sum((d - mean_d) * (a - mean_a) for d, a, _ in data) / n
    sd_d = math.sqrt(sum((d - mean_d)**2 for d in ds) / n)
    sd_a = math.sqrt(sum((a - mean_a)**2 for a in avgs) / n)
    corr = cov / (sd_d * sd_a) if sd_d * sd_a > 0 else 0
    log(f"\n相関係数: {corr:.4f}")

    log("\n停止時間 Top10:")
    for t, n, d in top_records[:10]:
        log(f"  n={n:10,} steps={t:4d} density={d:.3f} bin={bin(n)[:30]}")

    finding = f"### 仮説6: ビット密度と停止時間の相関 ({limit:,}まで)\n\n"
    finding += f"**相関係数: {corr:.4f}**\n\n"
    finding += "| ビット密度 | 平均停止時間 | サンプル数 |\n|-----------|------------|----------|\n"
    for d, a, c in data:
        finding += f"| {d:.1f} | {a:.1f} | {c:,} |\n"
    finding += f"\n**Top3 高停止時間:**\n"
    for t, n_val, d in top_records[:3]:
        finding += f"- n={n_val:,}, steps={t}, density={d:.3f}\n"
    save_finding("仮説6: ビット密度と停止時間の相関 (1M)", finding)
    return corr

# ─── 仮説7: 軌道合流点ネットワーク ──────────────────────────
def h7_confluence(limit: int = 200_000):
    log("", f"仮説7: 軌道合流点ネットワーク (limit={limit:,})")

    visit_count = Counter()
    CHUNK = 20_000

    for lo in range(1, limit + 1, CHUNK):
        hi = min(lo + CHUNK - 1, limit)
        for n in range(lo, hi + 1):
            x = n
            while x != 1:
                x = x // 2 if x % 2 == 0 else 3 * x + 1
                if x > limit:
                    visit_count[x] += 1
        log(f"  チャンク {lo:,}〜{hi:,} 完了")

    log("\nTop20 合流点:")
    top = visit_count.most_common(20)
    for point, cnt in top:
        log(f"  {point:>15,} → {cnt:>6,}本の軌道が通過")

    # 合流点の分布: ベキ則に従うか？
    log("\n合流点の訪問数分布 (ベキ則チェック):")
    thresholds = [10, 50, 100, 500, 1000]
    for thr in thresholds:
        c = sum(1 for v in visit_count.values() if v >= thr)
        log(f"  訪問数 >= {thr:5d}: {c:6,}個の合流点")

    finding = f"### 仮説7: 軌道合流点ネットワーク ({limit:,}まで)\n\n"
    finding += "| 合流点 | 通過軌道数 |\n|--------|----------|\n"
    for point, cnt in top[:10]:
        finding += f"| {point:,} | {cnt:,} |\n"
    finding += "\n**考察:** 特定の値に大量の軌道が集中→コラッツグラフはスケールフリー的構造の可能性\n"
    save_finding("仮説7: 軌道合流点ネットワーク (200K)", finding)

# ─── 仮説8: 遅延記録の2進数パターン（大規模）───────────────
def h8_delay_records_large(limit: int = 10_000_000):
    log("", f"仮説8: 遅延記録パターン (limit={limit:,})")

    CHUNK = 500_000
    cache = {}
    records = []
    max_t = 0

    for lo in range(1, limit + 1, CHUNK):
        hi = min(lo + CHUNK - 1, limit)
        for n in range(lo, hi + 1):
            t = stopping_time_iter(n, cache)
            if t > max_t:
                max_t = t
                records.append((n, t, bin(n)[2:]))
        if len(cache) > 600_000:
            cache.clear()
        log(f"  チャンク {lo:,}〜{hi:,} 完了 | 記録数={len(records)} 最大={max_t}")

    log(f"\n遅延記録 {len(records)} 個 (limit={limit:,})")
    densities = [b.count('1') / len(b) for _, _, b in records]
    avg_d = sum(densities) / len(densities)
    log(f"記録の平均ビット密度: {avg_d:.4f}")
    log("\n最後の15件:")
    for n, t, b in records[-15:]:
        d = b.count('1') / len(b)
        tail4 = b[-4:] if len(b) >= 4 else b
        log(f"  n={n:12,} steps={t:4d} density={d:.2f} tail={tail4} bits={b[:24]}{'…' if len(b)>24 else ''}")

    finding = f"### 仮説8: 遅延記録パターン ({limit:,}まで)\n\n"
    finding += f"- 記録数: {len(records)}\n"
    finding += f"- 最大停止時間: {records[-1][1]} (n={records[-1][0]:,})\n"
    finding += f"- 記録の平均ビット密度: {avg_d:.4f}\n\n"
    finding += "| n | 停止時間 | ビット密度 | 末尾4ビット |\n|---|---------|---------|----------|\n"
    for n, t, b in records[-10:]:
        d = b.count('1') / len(b)
        tail = b[-4:] if len(b) >= 4 else b
        finding += f"| {n:,} | {t} | {d:.3f} | {tail} |\n"
    save_finding("仮説8: 遅延記録パターン (10M)", finding)
    return records

# ─── 仮説9: 3n+1の「上昇段」と「下降段」の比率 ──────────────
def h9_ascent_descent(limit: int = 500_000):
    log("", f"仮説9: 上昇段と下降段の比率 (limit={limit:,})")
    """
    各軌道を「上昇（奇数ステップで値が大きくなる段）」と
    「下降（偶数ステップで値が小さくなる段）」に分割する。
    理論的には (3/2)^a * (1/2)^b → 1 になるはずなので
    a/b ≈ log(2)/log(3/2) ≈ 1.71 が期待値
    """
    ratios = []
    for n in range(2, limit + 1):
        x = n
        odd_steps = 0
        even_steps = 0
        while x != 1:
            if x % 2 == 0:
                even_steps += 1
                x //= 2
            else:
                odd_steps += 1
                x = 3 * x + 1
        if odd_steps > 0:
            ratios.append(even_steps / odd_steps)

    avg_ratio = sum(ratios) / len(ratios)
    theory = math.log(2) / math.log(3/2)
    log(f"  偶数ステップ/奇数ステップの平均比率: {avg_ratio:.4f}")
    log(f"  理論期待値 log(2)/log(3/2) = {theory:.4f}")
    log(f"  差: {abs(avg_ratio - theory):.6f}")

    # 分布の確認
    buckets = Counter(round(r * 10) / 10 for r in ratios)
    log("\n比率の分布 (上位10):")
    for ratio, cnt in sorted(buckets.items(), key=lambda x: -x[1])[:10]:
        log(f"  ratio={ratio:.1f}: {cnt:,}件")

    finding = f"### 仮説9: 偶数/奇数ステップ比率 ({limit:,}まで)\n\n"
    finding += f"- 実測平均比率: **{avg_ratio:.4f}**\n"
    finding += f"- 理論期待値 log(2)/log(3/2): **{theory:.4f}**\n"
    finding += f"- 差: {abs(avg_ratio - theory):.6f}\n\n"
    finding += "**意味:** コラッツ軌道が1に収束するためには偶数ステップが奇数ステップの約1.71倍必要。\n"
    finding += "実測値が理論値に近いほど、軌道は「平均的な」収束をしていることを示す。\n"
    save_finding("仮説9: 偶奇ステップ比率の検証", finding)

# ─── 仮説10: 2-adic評価 ──────────────────────────────────
def h10_2adic(limit: int = 1_000_000):
    log("", f"仮説10: 2進評価(2-adic valuation)と停止時間 (limit={limit:,})")
    """
    v2(n) = n の因数に含まれる 2 のべき乗の個数
    v2(n) が大きい = n が高い 2 のべき乗で割り切れる
    これと停止時間の関係は？
    """
    CHUNK = 100_000
    cache = {}
    v2_sum = defaultdict(int)
    v2_cnt = defaultdict(int)

    for lo in range(1, limit + 1, CHUNK):
        hi = min(lo + CHUNK - 1, limit)
        for n in range(lo, hi + 1):
            t = stopping_time_iter(n, cache)
            v = 0
            x = n
            while x % 2 == 0:
                v += 1
                x //= 2
            v2_sum[v] += t
            v2_cnt[v] += 1
        if len(cache) > 600_000:
            cache.clear()
        if lo % 500_000 == 1:
            log(f"  チャンク {lo:,}〜{hi:,} 完了")

    log("\nv2(n) vs 平均停止時間:")
    finding = f"### 仮説10: 2-adic評価と停止時間 ({limit:,}まで)\n\n"
    finding += "| v2(n) | サンプル数 | 平均停止時間 |\n|-------|----------|------------|\n"
    for v in sorted(v2_sum.keys()):
        avg = v2_sum[v] / v2_cnt[v]
        log(f"  v2={v:2d}: {v2_cnt[v]:8,}件 avg={avg:.1f}")
        finding += f"| {v} | {v2_cnt[v]:,} | {avg:.1f} |\n"
    finding += "\n**考察:** v2(n)=0（奇数）が最も停止時間が長い傾向がある。\n"
    finding += "2のべき乗で割り切れるほど、最初に偶数ステップが連続して早く小さくなる。\n"
    save_finding("仮説10: 2-adic評価と停止時間 (1M)", finding)

# ─── メイン ───────────────────────────────────────────────
def main():
    with open(FINDINGS_FILE, "a") as f:
        f.write(f"\n---\n# 夜通し探索セッション開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    with open(LOG_FILE, "w") as f:
        f.write(f"=== 夜通し探索ログ 開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")

    log("夜通し探索 開始", "START")
    t0 = time.time()

    log("RAM節約のため反復計算+チャンク処理方式を使用")
    log("各仮説の結果は findings.md に随時保存")

    h5_mod_power2(limit=2_000_000)
    log(f"仮説5完了 ({time.time()-t0:.0f}s)")
    gc.collect()

    h6_bit_density(limit=1_000_000)
    log(f"仮説6完了 ({time.time()-t0:.0f}s)")
    gc.collect()

    h7_confluence(limit=200_000)
    log(f"仮説7完了 ({time.time()-t0:.0f}s)")
    gc.collect()

    h8_delay_records_large(limit=10_000_000)
    log(f"仮説8完了 ({time.time()-t0:.0f}s)")
    gc.collect()

    h9_ascent_descent(limit=500_000)
    log(f"仮説9完了 ({time.time()-t0:.0f}s)")
    gc.collect()

    h10_2adic(limit=1_000_000)
    log(f"仮説10完了 ({time.time()-t0:.0f}s)")

    log("", "全仮説完了")
    log(f"総実行時間: {time.time()-t0:.0f}秒")
    log("findings.md と research.log に全結果を保存")

if __name__ == "__main__":
    main()
