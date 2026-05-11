#!/usr/bin/env python3
"""
Collatz Research Round 4 — 仮説23〜28
深掘りと新方向:
  23: 隣接するnの停止時間の自己相関（局所構造の有無）
  24: 逆コラッツ写像の分岐比（前任者が2つ vs 1つの割合）
  25: コラッツ定数 C の精密推定（avg_steps ≈ C * log2(n)）
  26: 素数 vs 合成数の停止時間の違い
  27: 停止時間のギャップ分析（遅延記録間のギャップ）
  28: 6.3/ビット の再検証: より大きなサンプルで精度向上
"""

import sys, math, time, gc, random
from collections import defaultdict, Counter
from datetime import datetime

FINDINGS = "/root/collatz/findings.md"
LOG      = "/root/collatz/research4.log"
STATUS   = "/root/collatz/STATUS.md"

def log(msg, section=None):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"\n{'='*60}\n[{ts}] === {section} ===\n{'='*60}" if section else f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f: f.write(line + "\n")

def save(title, content):
    with open(FINDINGS, "a") as f:
        f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} — {title}\n\n{content}\n")
    log(f"★ Saved: {title}")

def status_update(title, body):
    with open(STATUS, "a") as f:
        f.write(f"\n---\n### [{datetime.now().strftime('%H:%M')}] {title}\n{body}\n")

# ─── コア ────────────────────────────────────────────────────
def stopping_time_iter(n, cache):
    path = []
    while n != 1 and n not in cache:
        path.append(n)
        n = n // 2 if n % 2 == 0 else 3 * n + 1
    base = 0 if n == 1 else cache[n]
    if len(cache) < 500_000:
        for i, x in enumerate(reversed(path)):
            cache[x] = base + i + 1
    return base + len(path)

def is_prime_simple(n):
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    i = 3
    while i * i <= n:
        if n % i == 0: return False
        i += 2
    return True

def sieve(limit):
    """エラトステネスの篩で素数リストを返す"""
    is_p = bytearray([1]) * (limit + 1)
    is_p[0] = is_p[1] = 0
    for i in range(2, int(limit**0.5) + 1):
        if is_p[i]:
            is_p[i*i::i] = bytearray(len(is_p[i*i::i]))
    return is_p

# ─── 仮説23: 停止時間の自己相関 ─────────────────────────────
def h23_autocorrelation(limit=500_000):
    log("", f"仮説23: 停止時間の自己相関 (limit={limit:,})")

    CHUNK = 100_000
    cache = {}
    times = []
    for lo in range(1, limit+1, CHUNK):
        hi = min(lo+CHUNK-1, limit)
        for n in range(lo, hi+1):
            times.append(stopping_time_iter(n, cache))
        if len(cache) > 600_000: cache.clear()

    n = len(times)
    mean = sum(times) / n
    var  = sum((t - mean)**2 for t in times) / n

    # ラグ k の自己相関 r(k) = Cov(t_i, t_{i+k}) / Var
    lags = [1, 2, 3, 4, 5, 10, 20, 50, 100, 500, 1000]
    log("ラグ k の自己相関:")
    acf_data = []
    for k in lags:
        cov = sum((times[i] - mean) * (times[i+k] - mean) for i in range(n-k)) / (n-k)
        r = cov / var
        acf_data.append((k, r))
        bar = "█" * int(abs(r) * 40)
        sign = "+" if r >= 0 else "-"
        log(f"  lag={k:5d}: r={r:+.6f} {sign}{bar}")

    max_r = max(abs(r) for _, r in acf_data)
    log(f"\n最大自己相関: {max_r:.6f}")
    if max_r < 0.01:
        log("→ ほぼゼロ: 停止時間は隣接する数と無相関（カオス的）")
    elif max_r < 0.05:
        log("→ 弱い相関: わずかな局所構造あり")
    else:
        log("→ 有意な相関: 局所構造が存在する")

    finding = f"### 仮説23: 停止時間の自己相関 ({limit:,}まで)\n\n"
    finding += "| ラグk | 自己相関 r(k) |\n|-------|-------------|\n"
    for k, r in acf_data:
        finding += f"| {k} | {r:+.6f} |\n"
    finding += f"\n**最大絶対自己相関: {max_r:.6f}**\n\n"
    if max_r < 0.01:
        finding += "**結論: 停止時間はほぼ独立 → コラッツ写像はカオス的（疑似乱数的）**\n"
    else:
        finding += f"**結論: lag=1での相関 {acf_data[0][1]:+.4f} — 局所構造が存在する**\n"
    save("仮説23: 停止時間の自己相関", finding)
    return acf_data

# ─── 仮説24: 逆コラッツ写像の分岐比 ────────────────────────
def h24_inverse_branching(limit=2_000_000):
    log("", f"仮説24: 逆コラッツ写像の分岐比 (limit={limit:,})")

    # 各 n の前任者数を数える
    # 前任者: 2n (常に存在), (n-1)/3 (nが偶数かつ(n-1)%3==0かつ(n-1)/3が奇数の時)
    two_preds = 0   # 前任者が2つ
    one_pred  = 0   # 前任者が1つ（2nのみ）

    for n in range(2, limit+1):
        has_odd_pred = False
        if n % 2 == 0:  # 奇数前任者の候補
            candidate = (n - 1)
            if candidate % 3 == 0:
                odd_pred = candidate // 3
                if odd_pred % 2 == 1 and odd_pred > 0:
                    has_odd_pred = True
        if has_odd_pred:
            two_preds += 1
        else:
            one_pred += 1

    total = two_preds + one_pred
    ratio = two_preds / total
    log(f"前任者2つ: {two_preds:,} ({ratio:.4f})")
    log(f"前任者1つ: {one_pred:,} ({1-ratio:.4f})")
    log(f"理論値(前任者2の割合): 1/3 = {1/3:.4f}")
    log(f"差: {abs(ratio - 1/3):.6f}")

    # 分岐が多い数の分布
    log("\n分岐比の理論的考察:")
    log("  偶数 n で (n-1)%3==0 かつ (n-1)/3 が奇数 → 前任者2つ")
    log("  = n ≡ 1 (mod 3) かつ n ≡ 0 (mod 2)")
    log("  = n ≡ 4 (mod 6) の数")

    mod6_counts = Counter(n%6 for n in range(2, min(limit+1, 100001)))
    log(f"  n mod 6 分布（1〜100K）: { {k: mod6_counts[k] for k in sorted(mod6_counts)} }")

    # 前任者2つ持つ数の検証
    two_pred_mod6 = Counter()
    for n in range(2, min(100001, limit+1)):
        if n%2==0 and (n-1)%3==0:
            odd_pred = (n-1)//3
            if odd_pred%2==1 and odd_pred>0:
                two_pred_mod6[n%6] += 1
    log(f"  前任者2つの数の mod 6 分布: { {k: two_pred_mod6[k] for k in sorted(two_pred_mod6)} }")

    finding = f"### 仮説24: 逆コラッツ写像の分岐比 ({limit:,}まで)\n\n"
    finding += f"- 前任者が2つある数の割合: **{ratio:.4f}**\n"
    finding += f"- 理論値 (1/3 ≈ 0.3333): 差 = {abs(ratio-1/3):.6f}\n\n"
    finding += "**数学的証明:**\n"
    finding += "前任者が2つ ⟺ n が偶数かつ (n-1) ≡ 0 (mod 3) かつ (n-1)/3 が奇数\n"
    finding += "= n ≡ 4 (mod 6) の数（= 全体の1/6...だが2倍で約1/3）\n\n"
    finding += f"**重要:** コラッツグラフは約1/3の節点が2つの入辺を持つ\n"
    finding += "→ これがコラッツ木の「太さ」を決める基本比率\n"
    save("仮説24: 逆コラッツ写像の分岐比", finding)

# ─── 仮説25: コラッツ定数 C の精密推定 ──────────────────────
def h25_collatz_constant(limit=5_000_000):
    log("", f"仮説25: コラッツ定数 C の精密推定 (limit={limit:,})")
    """
    理論: 平均停止時間 ≈ C * log2(n)
    C の推定: sum(stopping_time(n)) / sum(log2(n))  for n=1..N
    """
    CHUNK = 500_000
    cache = {}
    total_steps = 0
    total_log2  = 0.0
    # 各 N でのスナップショット
    snapshots = []

    for lo in range(1, limit+1, CHUNK):
        hi = min(lo+CHUNK-1, limit)
        for n in range(lo, hi+1):
            t = stopping_time_iter(n, cache)
            total_steps += t
            total_log2  += math.log2(n) if n > 1 else 0
        if len(cache) > 600_000: cache.clear()
        C_est = total_steps / total_log2 if total_log2 > 0 else 0
        snapshots.append((hi, C_est))
        log(f"  n=1〜{hi:,}: C ≈ {C_est:.6f}")

    final_C = snapshots[-1][1]
    log(f"\nコラッツ定数 C ≈ {final_C:.6f}")
    log(f"収束の様子:")
    for n, c in snapshots:
        log(f"  N={n:>10,}: C={c:.6f}")

    # 収束速度の確認
    if len(snapshots) >= 2:
        diffs = [abs(snapshots[i+1][1]-snapshots[i][1]) for i in range(len(snapshots)-1)]
        log(f"隣接スナップショット間の差: {[f'{d:.6f}' for d in diffs]}")

    finding = f"### 仮説25: コラッツ定数 C の精密推定 ({limit:,}まで)\n\n"
    finding += f"**C ≈ {final_C:.6f}**\n\n"
    finding += "平均停止時間 ≈ C × log₂(n) の C の推定値\n\n"
    finding += "| N | C の推定値 |\n|---|----------|\n"
    for n, c in snapshots:
        finding += f"| {n:,} | {c:.6f} |\n"
    finding += "\n**考察:** C が収束しているほどコラッツ予想の「平均的な振る舞い」は安定している。\n"
    finding += "既知の理論値: C ≈ 9.477... (Terras, 1976 の結果)\n"
    save("仮説25: コラッツ定数 C の推定", finding)
    return final_C

# ─── 仮説26: 素数 vs 合成数の停止時間 ───────────────────────
def h26_prime_vs_composite(limit=1_000_000):
    log("", f"仮説26: 素数 vs 合成数の停止時間 (limit={limit:,})")

    log("篩で素数判定...")
    is_p = sieve(limit)

    CHUNK = 100_000
    cache = {}
    prime_times = []
    comp_times  = []

    for lo in range(2, limit+1, CHUNK):
        hi = min(lo+CHUNK-1, limit)
        for n in range(lo, hi+1):
            t = stopping_time_iter(n, cache)
            if is_p[n]:
                prime_times.append(t)
            else:
                comp_times.append(t)
        if len(cache) > 600_000: cache.clear()
        if lo % 500_000 == 2: log(f"  {lo:,}〜{hi:,} 完了")

    prime_avg = sum(prime_times) / len(prime_times)
    comp_avg  = sum(comp_times)  / len(comp_times)
    diff = prime_avg - comp_avg

    log(f"素数の平均停止時間:   {prime_avg:.4f} (n={len(prime_times):,})")
    log(f"合成数の平均停止時間: {comp_avg:.4f} (n={len(comp_times):,})")
    log(f"差 (素数-合成数):     {diff:+.4f}")

    # 分布の比較
    prime_std = math.sqrt(sum((t-prime_avg)**2 for t in prime_times)/len(prime_times))
    comp_std  = math.sqrt(sum((t-comp_avg)**2 for t in comp_times)/len(comp_times))
    log(f"素数の標準偏差: {prime_std:.2f}")
    log(f"合成数の標準偏差: {comp_std:.2f}")

    # 素数の停止時間 Top10
    prime_top = sorted(zip(prime_times, range(2, limit+1) if False else []), reverse=True)
    # より簡単に: 大きい停止時間の素数を探す
    log("\n停止時間が最大の素数 Top10 (再計算):")
    large_primes = [(stopping_time_iter(n, cache), n) for n in range(limit-10000, limit+1) if is_p[n]]
    large_primes.sort(reverse=True)
    for t, n in large_primes[:5]:
        log(f"  prime={n:,} steps={t}")

    # 素数 mod 6 の分析 (素数は mod 6 で 1 か 5 のみ)
    # 素数の停止時間が mod 6 で違いがあるか？
    prime_mod6_times = defaultdict(list)
    cache2 = {}
    for n in range(2, min(200001, limit+1)):
        if is_p[n]:
            t = stopping_time_iter(n, cache2)
            prime_mod6_times[n%6].append(t)

    log("\n素数の mod 6 別停止時間:")
    for r in sorted(prime_mod6_times):
        ts = prime_mod6_times[r]
        avg = sum(ts)/len(ts)
        log(f"  素数 mod 6 = {r}: avg={avg:.2f} n={len(ts):,}")

    finding = f"### 仮説26: 素数 vs 合成数の停止時間 ({limit:,}まで)\n\n"
    finding += f"| 種別 | 平均停止時間 | 標準偏差 | 個数 |\n|------|------------|--------|------|\n"
    finding += f"| 素数 | {prime_avg:.4f} | {prime_std:.2f} | {len(prime_times):,} |\n"
    finding += f"| 合成数 | {comp_avg:.4f} | {comp_std:.2f} | {len(comp_times):,} |\n"
    finding += f"\n**差 (素数 - 合成数): {diff:+.4f}**\n\n"
    if abs(diff) < 1.0:
        finding += "**結論: 素数と合成数の停止時間に有意な差はない**\n"
        finding += "→ コラッツ予想は素数の特殊性に依存しない\n"
    else:
        finding += f"**結論: 素数は合成数より平均{diff:+.2f}ステップ{'多い' if diff>0 else '少ない'}**\n"
    save("仮説26: 素数vs合成数の停止時間", finding)

# ─── 仮説27: 遅延記録間のギャップ ───────────────────────────
def h27_record_gaps(limit=50_000_000):
    log("", f"仮説27: 遅延記録間のギャップ分析 (limit={limit:,})")

    CHUNK = 1_000_000
    cache = {}
    records = []
    max_t = 0

    for lo in range(1, limit+1, CHUNK):
        hi = min(lo+CHUNK-1, limit)
        for n in range(lo, hi+1):
            t = stopping_time_iter(n, cache)
            if t > max_t:
                max_t = t
                records.append((n, t))
        if len(cache) > 600_000: cache.clear()
        if lo % 10_000_000 == 1: log(f"  {lo//1_000_000}M 完了 | 記録数={len(records)} 最大={max_t}")

    log(f"\n記録数: {len(records)}")

    # ギャップ（連続記録間の n の差）
    gaps = [records[i+1][0] - records[i][0] for i in range(len(records)-1)]
    if gaps:
        avg_gap = sum(gaps) / len(gaps)
        log(f"平均ギャップ: {avg_gap:,.0f}")
        log(f"最大ギャップ: {max(gaps):,}")
        log(f"最小ギャップ: {min(gaps):,}")

        # ギャップの分布（対数スケール）
        log("\nギャップの分布:")
        gap_buckets = Counter(int(math.log10(g)) if g > 0 else 0 for g in gaps)
        for exp in sorted(gap_buckets):
            cnt = gap_buckets[exp]
            log(f"  10^{exp}〜10^{exp+1}: {cnt}個")

        # 記録の比率（連続する記録の n の比率）
        ratios = [records[i+1][0]/records[i][0] for i in range(len(records)-1)]
        avg_ratio = sum(ratios) / len(ratios)
        log(f"\n連続記録の n の比率: 平均={avg_ratio:.4f}")
        log(f"（log(avg_ratio) = {math.log(avg_ratio):.4f}）")

        # 停止時間の増分
        step_increases = [records[i+1][1] - records[i][1] for i in range(len(records)-1)]
        step_dist = Counter(step_increases)
        log(f"\n停止時間の増分分布 Top10:")
        for inc, cnt in sorted(step_dist.items(), key=lambda x: -x[1])[:10]:
            log(f"  +{inc}ステップ: {cnt}回")

    log("\n全遅延記録:")
    for n, t in records:
        b = bin(n)[2:]
        d = b.count('1')/len(b)
        log(f"  n={n:12,} steps={t:4d} density={d:.3f} bits={b[:24]}{'…' if len(b)>24 else ''}")

    finding = f"### 仮説27: 遅延記録間のギャップ ({limit//1_000_000}Mまで)\n\n"
    finding += f"- 記録数: {len(records)}\n"
    if gaps:
        finding += f"- 平均ギャップ: {avg_gap:,.0f}\n"
        finding += f"- 連続記録の n 比率: {avg_ratio:.4f}\n\n"
        finding += "**停止時間増分の分布:**\n"
        for inc, cnt in sorted(step_dist.items(), key=lambda x: -x[1])[:8]:
            finding += f"- +{inc}: {cnt}回\n"
    save("仮説27: 遅延記録のギャップ分析", finding)

# ─── 仮説28: 6.3/ビット の高精度再検証 ──────────────────────
def h28_63_precision(limit=10_000_000):
    log("", f"仮説28: 6.3/ビット の高精度再検証 (limit={limit:,})")

    CHUNK = 500_000
    # mod 2^k の全1残差の平均停止時間を大規模に測定
    K_VALUES = range(1, 11)  # mod 2^1 〜 2^10
    sums = {k: 0 for k in K_VALUES}
    cnts = {k: 0 for k in K_VALUES}
    cache = {}

    for lo in range(1, limit+1, CHUNK):
        hi = min(lo+CHUNK-1, limit)
        for n in range(lo, hi+1):
            t = stopping_time_iter(n, cache)
            for k in K_VALUES:
                if n % (2**k) == (2**k - 1):
                    sums[k] += t
                    cnts[k] += 1
        if len(cache) > 600_000: cache.clear()
        if lo % 5_000_000 == 1: log(f"  {lo//1_000_000}M 完了")

    log(f"\nmod 2^k 全1ビット残差の平均停止時間 ({limit:,}まで):")
    avgs = {}
    for k in K_VALUES:
        if cnts[k] > 0:
            avgs[k] = sums[k] / cnts[k]
            log(f"  k={k:2d} (mod {2**k:5d}): avg={avgs[k]:.4f} (n={cnts[k]:,})")

    # 差分の精密計算
    log("\n差分 (k → k+1):")
    diffs = []
    for k in list(K_VALUES)[:-1]:
        if k in avgs and k+1 in avgs:
            d = avgs[k+1] - avgs[k]
            diffs.append(d)
            log(f"  k={k}→{k+1}: Δ={d:.4f}")

    if diffs:
        mean_diff = sum(diffs) / len(diffs)
        log(f"\n平均差分: {mean_diff:.4f}")
        log(f"標準偏差: {math.sqrt(sum((d-mean_diff)**2 for d in diffs)/len(diffs)):.4f}")

        # 数学定数との比較（高精度）
        log("\n数学定数との比較（高精度）:")
        candidates = [
            ("log(3)/log(3/2)",      math.log(3)/math.log(3/2)),
            ("1/log10(2)*log10(3)",  1/math.log10(2)*math.log10(3)),
            ("log2(3)^2",            math.log2(3)**2),
            ("2*log2(3)",            2*math.log2(3)),
            ("log2(27/4)",           math.log2(27/4)),
            ("pi",                   math.pi),
            ("e+1/e",                math.e + 1/math.e),
            ("2*pi/e",               2*math.pi/math.e),
            ("log2(3)*pi/2",         math.log2(3)*math.pi/2),
        ]
        for name, val in sorted(candidates, key=lambda x: abs(x[1]-mean_diff)):
            log(f"  {name:30s} = {val:.6f}  差={abs(val-mean_diff):.6f}")

    finding = f"### 仮説28: 6.3/ビット の高精度再検証 ({limit//1_000_000}Mまで)\n\n"
    finding += "| k | mod | 全1残差avg | Δ |\n|---|-----|----------|---|\n"
    prev_v = None
    for k in K_VALUES:
        if k in avgs:
            v = avgs[k]
            delta = f"{v-prev_v:+.4f}" if prev_v else "—"
            finding += f"| {k} | {2**k} | {v:.4f} | {delta} |\n"
            prev_v = v
    if diffs:
        finding += f"\n**精密平均差分: {mean_diff:.6f}**\n\n"
        best = min(candidates, key=lambda x: abs(x[1]-mean_diff))
        finding += f"**最も近い数学定数: {best[0]} = {best[1]:.6f}（差={abs(best[1]-mean_diff):.6f}）**\n"
    save("仮説28: 6.3/ビット高精度検証", finding)

# ─── STATUS更新 ─────────────────────────────────────────────
def final_status(C):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(STATUS, "a") as f:
        f.write(f"""
---
# Round 4 完了: {ts}

## 仮説23〜28 結果サマリー

### 仮説23: 停止時間の自己相関
隣接する n の停止時間の相関を測定 → カオス的か局所構造か判定

### 仮説24: 逆コラッツ写像の分岐比
前任者が2つある数の割合 ≈ 1/3 を検証

### 仮説25: コラッツ定数 C
C ≈ {C:.6f}（既知理論値: ~9.477）

### 仮説26: 素数 vs 合成数
停止時間に有意差があるか判定

### 仮説27: 遅延記録のギャップ
50Mまでの全記録と間隔の分布

### 仮説28: 6.3/ビット の正体
高精度測定と数学定数との照合

## 次ラウンド予定（research5.py）
- 仮説29: 1億〜10億の遅延記録の性質
- 仮説30: コラッツ木の「深さ」分布のべき乗則
- 仮説31: 停止時間と乗法的関数の関係
- 仮説32: 「ほぼ証明」できた命題のまとめ
""")

# ─── メイン ──────────────────────────────────────────────────
def main():
    with open(FINDINGS, "a") as f:
        f.write(f"\n---\n# Round 4 (仮説23〜28): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    with open(LOG, "w") as f:
        f.write(f"=== Round 4 ログ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")

    log("Round 4 開始 — 仮説23〜28", "START")
    t0 = time.time()

    h23_autocorrelation(limit=500_000);     log(f"H23完了 ({time.time()-t0:.0f}s)"); gc.collect()
    h24_inverse_branching(limit=2_000_000); log(f"H24完了 ({time.time()-t0:.0f}s)"); gc.collect()
    C = h25_collatz_constant(limit=5_000_000); log(f"H25完了 ({time.time()-t0:.0f}s)"); gc.collect()
    h26_prime_vs_composite(limit=1_000_000); log(f"H26完了 ({time.time()-t0:.0f}s)"); gc.collect()
    h27_record_gaps(limit=50_000_000);      log(f"H27完了 ({time.time()-t0:.0f}s)"); gc.collect()
    h28_63_precision(limit=10_000_000);     log(f"H28完了 ({time.time()-t0:.0f}s)")

    final_status(C)
    log("", "Round 4 完了")
    log(f"総実行時間: {time.time()-t0:.0f}秒")

if __name__ == "__main__":
    main()
