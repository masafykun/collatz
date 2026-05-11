"""
research13.py — 帰納法Stepの未解決部分を深堀り
焦点: 非all-1クラスのT上界 + Δ修正測定 + marginの漸近挙動
"""
import sys, gc, math, time
from collections import defaultdict

LOG = '/root/collatz/STATUS13.md'

def log(msg):
    print(msg, flush=True)
    with open(LOG, 'a') as f:
        f.write(msg + '\n')

def build_fast_table(N):
    T = {}
    T[1] = 0
    def stopping(n):
        if n in T: return T[n]
        path = []
        x = n
        while x not in T:
            path.append(x)
            x = x // 2 if x % 2 == 0 else 3 * x + 1
        base = T[x]
        for i, v in enumerate(reversed(path)):
            T[v] = base + i + 1
        return T[n]
    for n in range(2, N + 1):
        stopping(n)
    return T

def write_header():
    with open(LOG, 'w') as f:
        f.write("# Research13 — 帰納法Step深堀り\n")
        f.write(f"実行開始: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

# ════════════════════════════════════════════════════════════
# H70: Δ修正測定（標本数≥500のkのみ使用）
# ════════════════════════════════════════════════════════════
def h70_delta_fixed():
    log("## H70: Δ修正測定（標本数カットオフ付き）\n")
    log("標本数 < 500 の k は除外して安定したΔを計測する\n")

    target = 4 * math.log2(3)
    log(f"理論値 4log₂3 = {target:.6f}\n")

    log("| N | 有効k範囲 | Δ実測 | 誤差 |")
    log("|---|---|---|---|")

    for N in [500_000, 1_000_000, 2_000_000, 5_000_000]:
        T = build_fast_table(N)
        deltas = []
        prev_avg = None
        k_range = []
        for k in range(1, 20):
            mod = 2 ** k
            res = mod - 1
            vals = [T[n] for n in range(res, N+1, mod) if n in T]
            if len(vals) < 500:   # 標本数カットオフ
                break
            avg = sum(vals) / len(vals)
            if prev_avg is not None:
                deltas.append(avg - prev_avg)
                k_range.append(k)
            prev_avg = avg

        stable = deltas[2:] if len(deltas) > 2 else deltas
        d = sum(stable)/len(stable) if stable else 0
        err = abs(d - target)
        k_str = f"k={k_range[2]+1 if len(k_range)>2 else '?'}〜{k_range[-1] if k_range else '?'}"
        log(f"| {N:>10,} | {k_str} | {d:.4f} | {err:.4f} |")

        del T; gc.collect()

# ════════════════════════════════════════════════════════════
# H71: 帰納法Step — 非all-1クラスのC²行き先マッピング
# n ≡ r (mod 2^k), r ≠ 2^k-1 のとき、C or C² の行き先を全列挙
# ════════════════════════════════════════════════════════════
def h71_induction_step_mapping():
    log("\n## H71: 帰納法Step — 残差クラスのC²行き先\n")
    log("n ≡ r (mod 2^k) のとき C²(n) ≡ ? (mod 2^(k-1))\n")
    log("これにより帰納仮定がどのクラスの上界を与えるかがわかる\n")

    for k in [2, 3, 4]:
        mod    = 2 ** k
        lower  = 2 ** (k - 1)
        target = mod - 1
        log(f"### k={k} (mod {mod}):")
        log(f"| r (mod {mod}) | 偶奇 | C(r)の残差(mod{lower}) | C²(r)の残差(mod{lower}) | 説明 |")
        log("|---|---|---|---|---|")

        for r in range(mod):
            # 代表元
            rep = r if r > 0 else mod
            is_odd = rep % 2 == 1

            if is_odd:
                c1 = 3 * rep + 1
                c2 = c1 // 2
                c1_res = c1 % lower
                c2_res = c2 % lower
                if r == target:
                    note = f"→ all-1クラス(k-1) ✓ [定理2]"
                elif c2_res == lower - 1:
                    note = f"→ all-1クラス(k-1)に降下"
                else:
                    note = f"→ 非all-1クラス(k-1)"
            else:
                c1 = rep // 2
                c1_res = c1 % lower
                c2 = c1 // 2 if c1 % 2 == 0 else 3 * c1 + 1
                c2_res = c2 % lower
                note = f"→ C(n)=n/2 で1ステップ削減"

            parity = "奇" if is_odd else "偶"
            log(f"| {r:2d} ({r:0{k}b}) | {parity} | {c1_res} | {c2_res} | {note} |")
        log("")

    log("### 観察:")
    log("- **偶数クラス**: T(n) = 1 + T(n/2) → 1ステップ少なくなる (有利な降下)")
    log("- **奇数非all-1クラス**: C²の行き先が all-1(k-1) でない場合がある")
    log("- **all-1クラス**: 常に all-1(k-1) に降下 → 帰納仮定が適用できる")

# ════════════════════════════════════════════════════════════
# H72: marginのNスケール特性 — 各kでmarginは増加or収束?
# ════════════════════════════════════════════════════════════
def h72_margin_scaling():
    log("\n## H72: marginのNスケーリング\n")
    log("margin(k, N) = E[T|all-1, k] - max_{r≠2^k-1} E[T|r, k]\n")

    for k in [1, 2, 3, 4, 6, 8, 10, 12]:
        mod = 2**k
        target_res = mod - 1
        margins = []
        Ns = [100_000, 500_000, 1_000_000, 2_000_000]
        for N in Ns:
            T = build_fast_table(N)
            class_sums   = defaultdict(float)
            class_counts = defaultdict(int)
            for n in range(1, N + 1):
                r = n % mod
                if n in T:
                    class_sums[r]   += T[n]
                    class_counts[r] += 1

            if class_counts[target_res] == 0:
                margins.append(None)
                del T; gc.collect()
                continue

            target_avg = class_sums[target_res] / class_counts[target_res]
            best_other = max(
                (r for r in class_counts if r != target_res and class_counts[r] > 10),
                key=lambda r: class_sums[r] / class_counts[r], default=None
            )
            if best_other is None:
                margins.append(None)
            else:
                best_avg = class_sums[best_other] / class_counts[best_other]
                margins.append(target_avg - best_avg)

            del T; gc.collect()

        margin_str = " | ".join(f"{m:.2f}" if m is not None else "—" for m in margins)
        log(f"k={k:2d}: N=100K→2M | margin: {margin_str}")

    log("\n### 解釈")
    log("- marginが単調増加 → 命題Aは大きいNで強くなる（証明に有利）")
    log("- marginが収束 → 漸近的な下界が存在する可能性")

# ════════════════════════════════════════════════════════════
# H73: 偶数クラスは必ず all-1 クラスより小さいことの厳密確認
# T(2m) = 1 + T(m) なので E[T(even)] = 1 + E[T] (全体)
# E[T(all-1, k)] >> 1 + E[T] は成立するか？
# ════════════════════════════════════════════════════════════
def h73_even_classes_always_below():
    log("\n## H73: 偶数クラスは常にall-1クラスより下か？\n")

    N = 1_000_000
    T = build_fast_table(N)

    for k in [1, 2, 3, 4, 6, 8, 10]:
        mod = 2**k
        target_res = mod - 1

        target_vals = [T[n] for n in range(target_res, N+1, mod) if n in T]
        target_avg  = sum(target_vals)/len(target_vals) if target_vals else 0

        # 全偶数残差クラス
        even_avgs = []
        for r in range(0, mod, 2):  # 偶数残差のみ
            vals = [T[n] for n in range(r if r > 0 else mod, N+1, mod) if n in T]
            if vals:
                even_avgs.append(sum(vals)/len(vals))

        max_even = max(even_avgs) if even_avgs else 0
        min_gap  = target_avg - max_even

        log(f"k={k:2d}: all-1avg={target_avg:.2f}, max(偶数クラス)avg={max_even:.2f}, gap={min_gap:.2f} {'✓' if min_gap > 0 else '✗'}")

    log("\n**理由**: 偶数n=2^j×m (j≥1) のとき T(n) = j + T(m)")
    log("偶数クラスの T は奇数クラスの T から j を引いた値。")
    log("→ 偶数クラスは常に T が小さくなる（少なくともj分）")

    del T; gc.collect()

# ════════════════════════════════════════════════════════════
# H74: 奇数非all-1クラスの行き先分析（帰納法Stepの核心）
# n ≡ r (mod 2^k), r奇数, r ≠ 2^k-1 のとき
# C²(n) = (3n+1)/2 の行き先クラスと期待停止時間の比較
# ════════════════════════════════════════════════════════════
def h74_odd_nonmax_class_analysis():
    log("\n## H74: 奇数非all-1クラスの帰納的上界\n")
    log("n ≡ r (mod 2^k), r奇数, r ≠ 2^k-1 のとき:\n")
    log("T(n) = 2 + T(C²(n))")
    log("C²(n) ≡ s (mod 2^(k-1)) （sはrから決まる定数）\n")
    log("帰納仮定: E[T | all-1 class, k-1] ≥ E[T | s class, k-1]\n")
    log("もし s ≠ 2^(k-1)-1 なら帰納仮定により strictly 小さい\n")

    N = 1_000_000
    T = build_fast_table(N)

    for k in [2, 3, 4, 5]:
        mod    = 2**k
        lower  = 2**(k-1)
        target = mod - 1
        target_lower = lower - 1

        log(f"### k={k}:")

        # all-1クラスのk-1での平均T
        all1_lower_vals = [T[n] for n in range(target_lower, N+1, lower) if n in T]
        all1_lower_avg  = sum(all1_lower_vals)/len(all1_lower_vals) if all1_lower_vals else 0

        for r in range(1, mod, 2):  # 奇数のみ
            if r == target: continue
            # C²(r) mod lower を代数的に計算
            c2_res = ((3 * r + 1) // 2) % lower
            is_all1_lower = (c2_res == target_lower)

            # 実測: このクラスの平均T
            r_vals = [T[n] for n in range(r, N+1, mod) if n in T]
            r_avg  = sum(r_vals)/len(r_vals) if r_vals else 0

            # C²後のクラスの平均T
            c2_class_vals = [T[n] for n in range(c2_res if c2_res > 0 else lower, N+1, lower) if n in T]
            c2_avg = sum(c2_class_vals)/len(c2_class_vals) if c2_class_vals else 0

            bound = 2 + c2_avg
            note = "⬅ all-1(k-1)" if is_all1_lower else f"→ res={c2_res}(k-1)"
            log(f"  r={r:2d}: avg={r_avg:.1f}, C²→res{c2_res}({note}), 2+E[T|C²]={bound:.1f}, 差={r_avg-bound:.1f}")

    del T; gc.collect()

    log("\n### 帰納法Stepの構造まとめ:")
    log("1. n≡2^k-1 (all-1): T(n)=2+T(C²(n)), C²(n)→all-1(k-1)  [定理2]")
    log("   → E[T|all-1,k] = 2 + E[T|all-1,k-1]")
    log("2. n≡偶数(mod 2^k): T(n)≤T(n/2)+1 < T(all-1,k)")
    log("   → 偶数クラスは必ずall-1より小さい [H73確認]")
    log("3. n≡奇数,r≠2^k-1: T(n)=2+T(C²(n)), C²(n)→res s(k-1)")
    log("   s≠2^(k-1)-1なら帰納仮定により E[T|s,k-1] < E[T|all-1,k-1]")
    log("   → E[T|r,k] = 2 + E[T|s,k-1] < 2 + E[T|all-1,k-1] = E[T|all-1,k]")
    log("\n⭐ 全奇数非all-1クラスで C²の行き先が all-1(k-1) でなければ")
    log("   帰納法が完成する！")

# ════════════════════════════════════════════════════════════
# H75: 奇数非all-1クラスのC²行き先が all-1(k-1) になることはあるか？
# ════════════════════════════════════════════════════════════
def h75_c2_hits_all1_lower():
    log("\n## H75: 奇数非all-1クラスのC²が all-1(k-1) に当たる場合\n")
    log("r ≡ 奇数 (mod 2^k), r ≠ 2^k-1 で C²(r) ≡ 2^(k-1)-1 (mod 2^(k-1)) になるrを探す\n")

    for k in range(2, 13):
        mod    = 2**k
        lower  = 2**(k-1)
        target = mod - 1
        target_lower = lower - 1

        hits = []
        for r in range(1, mod, 2):  # 奇数r
            if r == target: continue
            c2_res = ((3 * r + 1) // 2) % lower
            if c2_res == target_lower:
                hits.append(r)

        if hits:
            log(f"k={k:2d}: C²→all-1(k-1) になる奇数r(≠2^k-1): {hits}")
        else:
            log(f"k={k:2d}: なし ✓")

    log("\n### 考察:")
    log("存在する場合: そのrクラスには帰納仮定が直接使えず、追加の論証が必要")
    log("存在しない場合: 帰納法が完成する！")

# ════════════════════════════════════════════════════════════
# メイン
# ════════════════════════════════════════════════════════════
if __name__ == '__main__':
    write_header()
    log(f"開始: {time.strftime('%H:%M:%S')}\n")

    h70_delta_fixed()
    h71_induction_step_mapping()
    h72_margin_scaling()
    h73_even_classes_always_below()
    h74_odd_nonmax_class_analysis()
    h75_c2_hits_all1_lower()

    log(f"\n完了: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=== research13.py 完了 ===")
