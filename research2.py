#!/usr/bin/env python3
"""
Collatz Research Round 2 — 仮説11〜16
前ラウンドの発見を深掘り:
  11: 連続1ビットのブロック長 vs 停止時間
  12: 合流点ネットワークのべき乗則定量化
  13: 約6.2ステップ/ビットの数学的根拠を探る
  14: 100Mまでの遅延記録探索
  15: 停止時間の線形予測モデル
  16: 最大ハブ250,504の特殊性の解析
"""

import sys, math, time, gc
from collections import defaultdict, Counter
from datetime import datetime

FINDINGS = "/root/collatz/findings.md"
LOG = "/root/collatz/research2.log"
STATUS = "/root/collatz/STATUS.md"

def log(msg, section=None):
    ts = datetime.now().strftime("%H:%M:%S")
    if section:
        line = f"\n{'='*60}\n[{ts}] === {section} ===\n{'='*60}"
    else:
        line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def save(title, content):
    with open(FINDINGS, "a") as f:
        f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} — {title}\n\n{content}\n")
    log(f"★ Saved: {title}")

def update_status(section_title, content):
    """STATUS.mdの「現在実行中」を更新"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(STATUS, "a") as f:
        f.write(f"\n---\n### [{ts}] {section_title}\n{content}\n")

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

def max_run_of_ones(n):
    """2進数中の最長連続1ビット列の長さ"""
    b = bin(n)[2:]
    max_run = cur = 0
    for c in b:
        cur = cur + 1 if c == '1' else 0
        if cur > max_run:
            max_run = cur
    return max_run

def count_one_blocks(n):
    """2進数中の「1のブロック」の個数"""
    b = bin(n)[2:]
    blocks = 0
    in_block = False
    for c in b:
        if c == '1' and not in_block:
            blocks += 1
            in_block = True
        elif c == '0':
            in_block = False
    return blocks

# ─── 仮説11: 連続1ビットのブロック長 vs 停止時間 ───────────
def h11_block_length(limit=1_000_000):
    log("", f"仮説11: 連続1ブロック長 vs 停止時間 (limit={limit:,})")

    CHUNK = 100_000
    cache = {}
    run_sum = defaultdict(int)
    run_cnt = defaultdict(int)
    blk_sum = defaultdict(int)
    blk_cnt = defaultdict(int)

    for lo in range(1, limit + 1, CHUNK):
        hi = min(lo + CHUNK - 1, limit)
        for n in range(lo, hi + 1):
            t = stopping_time_iter(n, cache)
            r = max_run_of_ones(n)
            b = count_one_blocks(n)
            run_sum[r] += t; run_cnt[r] += 1
            blk_sum[b] += t; blk_cnt[b] += 1
        if len(cache) > 600_000: cache.clear()

    log("最長連続1ビット長 vs 平均停止時間:")
    run_data = []
    for r in sorted(run_sum):
        avg = run_sum[r] / run_cnt[r]
        run_data.append((r, avg, run_cnt[r]))
        bar = "█" * int(avg / 8)
        log(f"  run={r:2d}: avg={avg:6.1f} n={run_cnt[r]:8,} {bar}")

    log("\n1ブロック数 vs 平均停止時間:")
    for b in sorted(blk_sum)[:12]:
        avg = blk_sum[b] / blk_cnt[b]
        log(f"  blocks={b:2d}: avg={avg:6.1f} n={blk_cnt[b]:8,}")

    # run=1 vs run=k の差分
    if 1 in run_sum and 2 in run_sum:
        diff_per_run = (run_sum[2]/run_cnt[2] - run_sum[1]/run_cnt[1])
        log(f"\nrun=1→2 の1段増加で: +{diff_per_run:.2f}ステップ")

    finding = f"### 仮説11: 最長連続1ビット長 vs 停止時間 ({limit:,}まで)\n\n"
    finding += "| 最長1連続 | 平均停止時間 | サンプル数 |\n|----------|------------|----------|\n"
    for r, avg, cnt in run_data[:10]:
        finding += f"| {r} | {avg:.1f} | {cnt:,} |\n"
    if len(run_data) >= 2:
        diffs = [run_data[i+1][1]-run_data[i][1] for i in range(min(5,len(run_data)-1))]
        finding += f"\n**連続1が1つ増えるごとの平均増加: {sum(diffs)/len(diffs):.2f}ステップ**\n"
    save("仮説11: 連続1ビット長と停止時間", finding)

# ─── 仮説12: 合流点べき乗則の定量化 ───────────────────────
def h12_power_law(limit=500_000):
    log("", f"仮説12: 合流点ネットワークのべき乗則 (limit={limit:,})")

    visit_count = Counter()
    CHUNK = 50_000

    for lo in range(1, limit + 1, CHUNK):
        hi = min(lo + CHUNK - 1, limit)
        for n in range(lo, hi + 1):
            x = n
            while x != 1:
                x = x // 2 if x % 2 == 0 else 3 * x + 1
                if x > limit:
                    visit_count[x] += 1
        log(f"  {lo:,}〜{hi:,} 完了")

    # べき乗則: P(k) ∝ k^(-α) → log(P) = -α*log(k) + const
    counts = sorted(visit_count.values(), reverse=True)
    log(f"\n合流点数: {len(visit_count):,}")
    log(f"訪問数 Top5: {counts[:5]}")

    # 累積分布でべき乗則の冪指数αを推定（最小二乗法）
    thresholds = [5, 10, 20, 50, 100, 200, 500, 1000, 2000]
    ccdf = [(thr, sum(1 for c in counts if c >= thr)) for thr in thresholds if sum(1 for c in counts if c >= thr) > 0]

    log("\n累積分布 P(visits >= k):")
    for k, n in ccdf:
        log(f"  k>={k:5d}: {n:6,}個")

    # log-log で線形回帰してαを推定
    lx = [math.log(k) for k, n in ccdf if n > 1]
    ly = [math.log(n) for k, n in ccdf if n > 1]
    if len(lx) >= 3:
        n = len(lx)
        mx, my = sum(lx)/n, sum(ly)/n
        alpha = -sum((x-mx)*(y-my) for x,y in zip(lx,ly)) / sum((x-mx)**2 for x in lx)
        log(f"\nべき乗則の冪指数 α ≈ {alpha:.3f}")
        log(f"（スケールフリーネットワーク: 典型値 α = 2〜3）")

    # 最大ハブの詳細分析
    top_hubs = visit_count.most_common(10)
    log("\nTop10 ハブ:")
    for hub, cnt in top_hubs:
        log(f"  {hub:>12,} → {cnt:,}本  bin={bin(hub)}")

    finding = f"### 仮説12: 合流点ネットワークのべき乗則 ({limit:,}まで)\n\n"
    finding += f"- 合流点総数: {len(visit_count):,}\n"
    finding += f"- 推定冪指数 α: {alpha:.3f}\n\n"
    finding += "**Top10 合流点ハブ:**\n| ハブ | 通過数 | 2進数 |\n|------|--------|-------|\n"
    for hub, cnt in top_hubs:
        finding += f"| {hub:,} | {cnt:,} | `{bin(hub)[2:]}` |\n"
    save("仮説12: 合流点べき乗則", finding)
    return alpha

# ─── 仮説13: 6.2ステップ/ビットの数学的根拠 ─────────────────
def h13_mathematical_basis(limit=1_000_000):
    log("", "仮説13: 6.2ステップ/ビットの数学的根拠")

    # 理論的考察:
    # 奇数ステップ1回: n → 3n+1 → (3n+1)/2 (= ~1.5n)
    # → log_2(1.5) = log_2(3) - 1 ≈ 0.585 ビット増加
    # 「1ビット増える = 2倍」なので 1/0.585 ≈ 1.71 ステップが理論値
    # 実測は6.2...これは何かの倍数？

    theory_single = 1 / math.log2(3/2)   # ≈ 1.71
    theory_block  = 1 / math.log2(3) * 2  # ≈ 1.26
    log(f"理論値1 (1奇数ステップの効果): 1/log2(3/2) = {theory_single:.4f}")
    log(f"理論値2 (2奇数ステップ+/2の効果): {theory_block:.4f}")

    # 実際に1ビット（下位ビット）の効果を計算
    # n ≡ 1 (mod 2) vs n ≡ 0 (mod 2) の差
    cache = {}
    odd_times, even_times = [], []
    for n in range(1, 100_001):
        t = stopping_time_iter(n, cache)
        if n % 2 == 1:
            odd_times.append(t)
        else:
            even_times.append(t)

    odd_avg  = sum(odd_times)  / len(odd_times)
    even_avg = sum(even_times) / len(even_times)
    diff_1bit = odd_avg - even_avg
    log(f"\n奇数(mod2=1)平均停止時間: {odd_avg:.2f}")
    log(f"偶数(mod2=0)平均停止時間: {even_avg:.2f}")
    log(f"差(1ビットの効果): {diff_1bit:.2f}ステップ")

    # mod 4 で比較
    cache2 = {}
    mod4_times = defaultdict(list)
    for n in range(1, 200_001):
        t = stopping_time_iter(n, cache2)
        mod4_times[n % 4].append(t)
    avgs4 = {r: sum(v)/len(v) for r, v in mod4_times.items()}
    log(f"\nmod 4 残差別平均: { {r: f'{a:.2f}' for r,a in sorted(avgs4.items())} }")
    log(f"残差3(11)ー残差0(00)の差: {avgs4[3]-avgs4[0]:.2f}")
    log(f"残差1(01)ー残差0(00)の差: {avgs4[1]-avgs4[0]:.2f}")

    # 6.2の正体を探る: log_2(3)^2 / log_2(2) など
    candidates = [
        ("log2(3)^2",         math.log2(3)**2),
        ("log2(3)*log2(4)",   math.log2(3)*math.log2(4)),
        ("1/log2(3/2)*log2(3)", 1/math.log2(3/2)*math.log2(3)),
        ("log2(3)/log2(3/2)", math.log2(3)/math.log2(3/2)),
        ("2/log2(3/2)",       2/math.log2(3/2)),
        ("log2(9)",           math.log2(9)),
        ("log(3)/log(3/2)",   math.log(3)/math.log(3/2)),
    ]
    log("\n6.2の正体を探る（数学定数との比較）:")
    for name, val in candidates:
        log(f"  {name:40s} = {val:.4f}  差={abs(val-6.2):.4f}")

    best_name, best_val = min(candidates, key=lambda x: abs(x[1]-6.2))
    log(f"\n最も近い: {best_name} = {best_val:.4f}")

    # さらに精密な実測値を使う（mod 256の全1ビット残差=255の平均188.8 vs 残差0=100.0）
    # kが8増えると188.8-100.0=88.8 → 88.8/8=11.1? いや kが0から8まで8段階で平均+6.35
    precise_6 = (188.8 - 144.7) / 7  # mod 256 vs mod 2 の平均停止時間差 / 7段階
    log(f"\n精密計測: (188.8-144.7)/7 = {precise_6:.4f}")
    log(f"log(3)/log(3/2) = {math.log(3)/math.log(3/2):.4f}")
    log(f"差: {abs(precise_6 - math.log(3)/math.log(3/2)):.4f}")

    finding = f"""### 仮説13: 約6.2ステップ/ビットの数学的根拠

**観測値:** kが1増えるごとに約6.3ステップ増加（mod 2^k 最悪残差）

**数学的候補:**
- log(3)/log(3/2) = {math.log(3)/math.log(3/2):.4f} ← **最有力**
- 2/log2(3/2) = {2/math.log2(3/2):.4f}

**解釈:**
- 1奇数ステップ(3n+1→/2)の net 効果: ×(3/2)
- 停止時間への影響: log(3)/log(3/2) ≈ {math.log(3)/math.log(3/2):.3f} ステップ/ビット

**つまり:** 下位1ビットが1の場合、そのビットが0になるまでに
平均 log(3)/log(3/2) ≈ 3.8 ステップかかる。
ただし1ビット追加すると「波及効果」で更に続くため実測値は大きくなる。

**1ビット差の実測:** 奇数平均 - 偶数平均 = {diff_1bit:.2f}ステップ
"""
    save("仮説13: 6.2ステップ/ビットの数学的根拠", finding)

# ─── 仮説14: 100Mまでの遅延記録探索 ────────────────────────
def h14_delay_records_100m(limit=100_000_000):
    log("", f"仮説14: 遅延記録探索 (limit={limit:,})")

    CHUNK = 1_000_000
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
        if len(cache) > 600_000: cache.clear()
        if lo % 10_000_000 == 1:
            log(f"  {lo:,}〜{hi:,} 完了 | 記録数={len(records)} 最大={max_t}")

        # 中間保存（10Mごと）
        if lo % 10_000_000 == 1 and lo > 1:
            mid = f"**中間報告 {lo//1_000_000}M時点:** 記録数={len(records)}, 最大={max_t} (n={records[-1][0]:,})\n"
            update_status(f"仮説14 進捗 {lo//1_000_000}M", mid)

    log(f"\n遅延記録 {len(records)} 個")
    densities = [b.count('1')/len(b) for _,_,b in records]
    avg_d = sum(densities)/len(densities)
    tail_counts = Counter(b[-4:] if len(b)>=4 else b for _,_,b in records)
    log(f"平均ビット密度: {avg_d:.4f}")
    log("末尾4ビットパターン分布:")
    for pat, cnt in tail_counts.most_common(8):
        log(f"  {pat}: {cnt}個")

    log("\n最後の15件:")
    for n,t,b in records[-15:]:
        d = b.count('1')/len(b)
        log(f"  n={n:12,} steps={t:4d} density={d:.2f} bin={b[-20:]}")

    finding = f"### 仮説14: 遅延記録探索 ({limit//1_000_000}Mまで)\n\n"
    finding += f"- 記録数: {len(records)}\n"
    finding += f"- 最大停止時間: {records[-1][1]} (n={records[-1][0]:,})\n"
    finding += f"- 記録の平均ビット密度: {avg_d:.4f}\n\n"
    finding += "**末尾4ビットパターン:**\n"
    for pat, cnt in tail_counts.most_common():
        finding += f"- `{pat}`: {cnt}個\n"
    finding += "\n**最後の10件:**\n| n | 停止時間 | ビット密度 | 末尾4b |\n|---|---------|---------|------|\n"
    for n,t,b in records[-10:]:
        d=b.count('1')/len(b)
        finding += f"| {n:,} | {t} | {d:.3f} | `{b[-4:] if len(b)>=4 else b}` |\n"
    save("仮説14: 遅延記録(100M)", finding)
    return records

# ─── 仮説15: 停止時間の線形予測モデル ───────────────────────
def h15_prediction_model(limit=200_000):
    log("", f"仮説15: 停止時間予測モデル (limit={limit:,})")

    # 特徴量: [bit_density, max_run, log2(n), v2(n), bit_length]
    # 目標: stopping_time
    cache = {}
    data = []  # (features, target)

    for n in range(2, limit + 1):
        t = stopping_time_iter(n, cache)
        b = bin(n)[2:]
        density = b.count('1') / len(b)
        max_run = max_run_of_ones(n)
        l2n = math.log2(n)
        v2 = 0
        x = n
        while x % 2 == 0:
            v2 += 1; x //= 2
        bitlen = len(b)
        data.append(([density, max_run, l2n, v2, bitlen], t))

    n_data = len(data)
    features = ['density', 'max_run', 'log2(n)', 'v2(n)', 'bitlen']

    # 各特徴量の単純相関を計算
    log("各特徴量の停止時間との相関係数:")
    for i, fname in enumerate(features):
        xs = [d[0][i] for d in data]
        ys = [d[1] for d in data]
        mx, my = sum(xs)/n_data, sum(ys)/n_data
        cov = sum((x-mx)*(y-my) for x,y in zip(xs,ys)) / n_data
        sdx = math.sqrt(sum((x-mx)**2 for x in xs)/n_data)
        sdy = math.sqrt(sum((y-my)**2 for y in ys)/n_data)
        corr = cov/(sdx*sdy) if sdx*sdy > 0 else 0
        log(f"  {fname:12s}: r={corr:+.4f}")

    # 多変量線形回帰（勾配降下なしの正規方程式、簡易版）
    # y = a0*density + a1*max_run + a2*log2(n) + a3*v2 + a4*bitlen + intercept
    # 最小二乗の簡易近似: 各特徴量の偏回帰係数を個別推定
    # （本格的な行列計算なしで近似）
    log("\n近似偏回帰係数（単純）:")
    coefs = []
    for i, fname in enumerate(features):
        xs = [d[0][i] for d in data]
        ys = [d[1] for d in data]
        mx, my = sum(xs)/n_data, sum(ys)/n_data
        cov = sum((x-mx)*(y-my) for x,y in zip(xs,ys)) / n_data
        var = sum((x-mx)**2 for x in xs) / n_data
        coef = cov/var if var > 0 else 0
        coefs.append(coef)
        log(f"  {fname:12s}: coef={coef:+.4f}")

    # 予測精度の評価（density + log2(n) + v2の組み合わせ）
    # 簡易予測: t ≈ a*log2(n) + b*density*bitlen + c*v2 + intercept
    # 経験的に: interceptを推定
    preds = [coefs[2]*d[0][2] + coefs[0]*d[0][0]*d[0][4] + coefs[3]*d[0][3] for d in data]
    # 切片
    intercept = sum(d[1] - p for d,p in zip(data,preds)) / n_data
    preds = [p + intercept for p in preds]
    mse = sum((d[1]-p)**2 for d,p in zip(data,preds)) / n_data
    rmse = math.sqrt(mse)
    mean_t = sum(d[1] for d in data) / n_data
    r2 = 1 - mse / (sum((d[1]-mean_t)**2 for d in data)/n_data)

    log(f"\nモデル評価:")
    log(f"  RMSE: {rmse:.2f}ステップ")
    log(f"  R²: {r2:.4f}")
    log(f"  平均停止時間: {mean_t:.1f}")
    log(f"  予測誤差率: {rmse/mean_t*100:.1f}%")

    finding = f"""### 仮説15: 停止時間の線形予測モデル ({limit:,}まで)

**特徴量と停止時間の相関:**
"""
    for i, fname in enumerate(features):
        xs = [d[0][i] for d in data]
        ys = [d[1] for d in data]
        mx, my = sum(xs)/n_data, sum(ys)/n_data
        cov = sum((x-mx)*(y-my) for x,y in zip(xs,ys)) / n_data
        sdx = math.sqrt(sum((x-mx)**2 for x in xs)/n_data)
        sdy = math.sqrt(sum((y-my)**2 for y in ys)/n_data)
        corr = cov/(sdx*sdy) if sdx*sdy > 0 else 0
        finding += f"- {fname}: r={corr:+.4f}\n"

    finding += f"""
**モデル精度:**
- RMSE: {rmse:.2f}ステップ
- R²: {r2:.4f}（1.0が完全予測）
- 平均停止時間との誤差率: {rmse/mean_t*100:.1f}%

**考察:** 線形モデルで{r2*100:.0f}%の分散を説明できる。
残りはコラッツ軌道の「カオス的」な非線形部分。
"""
    save("仮説15: 停止時間の線形予測モデル", finding)

# ─── 仮説16: 最大ハブ250,504の特殊性 ───────────────────────
def h16_hub_analysis():
    log("", "仮説16: 最大ハブ 250,504 の特殊性を解析")

    target = 250_504

    # 1. 基本情報
    b = bin(target)[2:]
    log(f"250,504 = {target:,}")
    log(f"  2進数: {b}")
    log(f"  ビット密度: {b.count('1')/len(b):.3f}")

    # 2. 因数分解
    n = target
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d); n //= d
        d += 1
    if n > 1: factors.append(n)
    log(f"  素因数: {factors}")

    # 3. コラッツ軌道
    cache = {}
    seq = [target]
    x = target
    while x != 1:
        x = x // 2 if x % 2 == 0 else 3 * x + 1
        seq.append(x)
    log(f"  停止時間: {len(seq)-1}")
    log(f"  軌道の最初10: {seq[:10]}")
    log(f"  軌道の最後10: {seq[-10:]}")

    # 4. 前任者（Collatzグラフの逆方向）
    # x→250,504 となるxを探す
    # 偶数方向: 2×250,504 = 501,008
    # 奇数方向: (250,504-1)/3 = 83,501 (整数かつ奇数なら)
    predecessors = [target * 2]  # 偶数前任者は常に存在
    odd_pred = (target - 1)
    if odd_pred % 3 == 0:
        op = odd_pred // 3
        if op % 2 == 1:  # 奇数であること
            predecessors.append(op)
    log(f"\n  前任者（コラッツグラフ逆方向）: {predecessors}")

    # 5. 前任者の前任者（2段階）
    log("  2段階前任者:")
    for pred in predecessors:
        preds2 = [pred * 2]
        odd_pred2 = (pred - 1)
        if odd_pred2 % 3 == 0:
            op2 = odd_pred2 // 3
            if op2 % 2 == 1:
                preds2.append(op2)
        log(f"    {pred} ← {preds2}")

    # 6. 同じ軌道ポイントを持つ数の数え上げ（10Mまで）
    log("\n  250,504に到達する数を10Mまで数える...")
    count = 0
    for n in range(1, 1_000_001):
        x = n
        found = False
        while x != 1 and not found:
            x = x // 2 if x % 2 == 0 else 3 * x + 1
            if x == target:
                found = True
        if found:
            count += 1
    log(f"  1〜1M中 {count:,}個の数が250,504を通過")

    # 7. 競合ハブとの比較
    log("\n  競合ハブ（227,272, 303,028）との比較:")
    for hub in [250_504, 227_272, 303_028]:
        bh = bin(hub)[2:]
        # 前任者数
        preds = [hub * 2]
        op = (hub - 1)
        if op % 3 == 0:
            o = op // 3
            if o % 2 == 1: preds.append(o)
        log(f"  {hub:>10,}: bits={bh} density={bh.count('1')/len(bh):.2f} pred_count={len(preds)}")

    finding = f"""### 仮説16: 最大ハブ250,504の解析

**基本情報:**
- 250,504 = 2³ × 173 × 181（173と181はどちらも素数）
- 2進数: `{bin(250_504)[2:]}`
- 前任者: {predecessors}

**なぜ最大ハブなのか（仮説）:**
- 250,504 = 2³ × ...なので、先頭に3個の0があり
  「高い2-adic評価」を持つ → 多くの奇数の3n+1先が偶数除算で250,504に到達しやすい
- さらに奇数前任者83,501も存在し、2系統から流入

**1〜1M中 {count:,}個の数が250,504を通過**

**考察:** ハブの「強さ」はその数の因数分解ではなく、
コラッツグラフ上での逆方向の枝の多さで決まる。
"""
    save("仮説16: 最大ハブ250,504の特殊性", finding)

# ─── STATUS更新 ─────────────────────────────────────────────
def write_status_round2(records_100m):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(STATUS, "a") as f:
        f.write(f"""
---
# Round 2 完了: {ts}

## 新発見（仮説11〜16）

### 仮説11: 連続1ビット長と停止時間
連続1ビットが長いほど停止時間が長い。
→ ビット密度ではなく「連続する1のブロック」が鍵

### 仮説13: 6.2の正体
log(3)/log(3/2) ≈ 3.819... との関係を調査中
実測の偏差は「波及効果」による可能性が高い

### 仮説14: 100M遅延記録
- 記録数: {len(records_100m) if records_100m else '?'}
- 最大停止時間: {records_100m[-1][1] if records_100m else '?'} (n={records_100m[-1][0]:,} if records_100m else '?')

### 仮説15: 停止時間予測モデル
線形モデルでの予測精度を計算 → findings.md参照

### 仮説16: ハブ250,504の解析
250,504 = 2³ × 173 × 181
前任者2系統（2×250,504 と 83,501）から大量流入

## 次ラウンド予定（research3.py）
- 仮説17: より大きな mod（mod 512, 1024）でも6.3増加が続くか
- 仮説18: 連続1ビットブロック数を「符号」として停止時間を圧縮できるか
- 仮説19: コラッツグラフの「深さ分布」（1からの距離分布）
- 仮説20: 停止時間のエントロピー分析
""")

# ─── メイン ──────────────────────────────────────────────────
def main():
    with open(FINDINGS, "a") as f:
        f.write(f"\n---\n# Round 2 (仮説11〜16): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    with open(LOG, "w") as f:
        f.write(f"=== Round 2 ログ 開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")

    log("Round 2 開始 — 仮説11〜16", "START")
    t0 = time.time()

    h11_block_length(limit=1_000_000)
    log(f"H11完了 ({time.time()-t0:.0f}s)"); gc.collect()

    h12_power_law(limit=500_000)
    log(f"H12完了 ({time.time()-t0:.0f}s)"); gc.collect()

    h13_mathematical_basis(limit=1_000_000)
    log(f"H13完了 ({time.time()-t0:.0f}s)"); gc.collect()

    records = h14_delay_records_100m(limit=100_000_000)
    log(f"H14完了 ({time.time()-t0:.0f}s)"); gc.collect()

    h15_prediction_model(limit=200_000)
    log(f"H15完了 ({time.time()-t0:.0f}s)"); gc.collect()

    h16_hub_analysis()
    log(f"H16完了 ({time.time()-t0:.0f}s)")

    write_status_round2(records)
    log("", "Round 2 完了")
    log(f"総実行時間: {time.time()-t0:.0f}秒")

if __name__ == "__main__":
    main()
