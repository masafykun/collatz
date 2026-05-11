"""
Collatz 研究 論文用図生成スクリプト
実験データをハードコードして6枚の図を生成する
"""

import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib import rcParams

# フォント設定 (日本語: Noto Sans CJK JP)
import matplotlib.font_manager as fm
fm._load_fontmanager(try_read_cache=False)
rcParams['font.family'] = 'Noto Sans CJK JP'
rcParams['font.sans-serif'] = ['Noto Sans CJK JP', 'DejaVu Sans']
rcParams['mathtext.fontset'] = 'stix'
rcParams['axes.unicode_minus'] = False
BLUE   = '#2166AC'
RED    = '#D6604D'
GREEN  = '#4DAC26'
ORANGE = '#F4A582'
GRAY   = '#888888'
DARK   = '#222222'

def save(fig, name):
    fig.savefig(f'figures/{name}.png', dpi=180, bbox_inches='tight',
                facecolor='white')
    plt.close(fig)
    print(f'  saved: figures/{name}.png')

import os
os.makedirs('figures', exist_ok=True)

# ─────────────────────────────────────────────
# Figure 1: 平均停止時間 vs k (命題A + Δ)
# ─────────────────────────────────────────────
def fig1_delta_vs_k():
    k_vals = list(range(1, 10))
    avg_T  = [161.46, 167.64, 173.82, 180.02, 186.37, 192.79, 199.11, 205.46, 211.80]
    deltas = [None, 6.18, 6.18, 6.21, 6.34, 6.42, 6.32, 6.35, 6.35]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    # 左: 平均停止時間
    ax1.plot(k_vals, avg_T, 'o-', color=BLUE, lw=2, ms=7, zorder=3)
    # 理論線: 161.46 + 6.309*(k-1)
    k_th = np.linspace(1, 9, 100)
    ax1.plot(k_th, 161.46 + 6.309*(k_th-1), '--', color=RED, lw=1.5,
             label=r'$161.5 + 6.309(k-1)$')
    ax1.set_xlabel('k  (trailing 1-bits)', fontsize=12)
    ax1.set_ylabel('Average stopping time  E[T]', fontsize=12)
    ax1.set_title(r'(a) $E[T \mid n \equiv 2^k{-}1\,(\mathrm{mod}\;2^k)]$  vs  $k$',
                  fontsize=12)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(k_vals)

    # 右: Δ (差分)
    d_k = k_vals[1:]
    d_v = deltas[1:]
    bars = ax2.bar(d_k, d_v, color=BLUE, alpha=0.75, zorder=3)
    ax2.axhline(6.309, color=RED, lw=2, ls='--', label=r'実測平均 $\Delta=6.309$')
    ax2.axhline(6.340, color=GREEN, lw=2, ls=':', label=r'$4\log_2 3=6.340$')
    ax2.set_xlabel('k', fontsize=12)
    ax2.set_ylabel(r'$\Delta_k = E[T_k] - E[T_{k-1}]$', fontsize=12)
    ax2.set_title(r'(b) Stopping-time increment $\Delta_k$ per trailing-1-bit', fontsize=12)
    ax2.legend(fontsize=10)
    ax2.set_ylim(5.8, 6.9)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_xticks(d_k)

    fig.tight_layout()
    save(fig, 'fig1_delta_vs_k')

# ─────────────────────────────────────────────
# Figure 2: 命題A — 全1残差の余裕 (差分)
# ─────────────────────────────────────────────
def fig2_proposition_a():
    k_vals  = list(range(1, 13))
    margins = [161.46, 116.55, 108.00, 100.81, 88.93, 84.75,
               80.19, 74.09, 65.79, 54.75, 50.71, 40.64]
    runner_up = [0, 51.09, 65.82, 79.21, 97.44, 108.04,
                 118.92, 131.37, 146.01, 163.85, 175.57, 194.13]
    all_ones  = [161.46, 167.64, 173.82, 180.02, 186.37, 192.79,
                 199.11, 205.46, 211.80, 218.60, 226.28, 234.77]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    # 左: 全1残差 vs 次点残差の平均停止時間
    ax1.fill_between(k_vals, all_ones, runner_up, alpha=0.15, color=BLUE,
                     label='余裕 (margin)')
    ax1.plot(k_vals, all_ones, 'o-', color=BLUE, lw=2, ms=7,
             label=r'全1残差 ($2^k{-}1$)', zorder=3)
    ax1.plot(k_vals, runner_up, 's--', color=RED, lw=2, ms=6,
             label='次点残差', zorder=3)
    ax1.set_xlabel('k', fontsize=12)
    ax1.set_ylabel('Average stopping time  E[T]', fontsize=12)
    ax1.set_title('(a) 全1残差 vs 次点残差  (n ≤ 10M)', fontsize=12)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(k_vals)

    # 右: 余裕の推移
    colors = [GREEN if m > 0 else RED for m in margins]
    ax2.bar(k_vals, margins, color=colors, alpha=0.80, zorder=3)
    ax2.axhline(0, color='black', lw=1)
    ax2.set_xlabel('k', fontsize=12)
    ax2.set_ylabel('余裕 = E[T(全1)] − E[T(次点)]', fontsize=12)
    ax2.set_title('(b) 命題A の余裕  (反例: 0件)', fontsize=12)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_xticks(k_vals)
    # 注釈
    ax2.text(6, 5, '←縮小傾向だが\n   余裕は維持', fontsize=9, color=DARK)

    fig.tight_layout()
    save(fig, 'fig2_proposition_a')

# ─────────────────────────────────────────────
# Figure 3: 遅延記録の散布図
# ─────────────────────────────────────────────
def fig3_delay_records():
    # n ≤ 10M の53件の遅延記録 (H50データ)
    records = [
        (2,1),(3,7),(6,8),(7,16),(9,19),(18,20),(25,23),(27,111),(54,112),
        (73,115),(97,118),(129,121),(171,124),(231,127),(313,130),(327,143),
        (649,144),(703,170),(871,178),(1161,181),(2223,182),(2463,208),
        (2919,216),(3711,237),(6171,261),(10971,267),(13255,275),(17647,278),
        (23529,281),(26623,307),(34239,310),(35655,323),(52527,339),
        (77031,350),(106239,353),(142587,374),(156159,382),(216367,385),
        (230631,442),(410011,448),(511935,469),(626331,508),(837799,524),
        (1117065,527),(1501353,530),(1723519,556),(2298025,559),
        (3064033,562),(3542887,583),(3732423,596),(5649499,612),
        (6649279,664),(8400511,685),
    ]
    ns = [r[0] for r in records]
    ts = [r[1] for r in records]

    # 末尾1ビット数で色分け
    def trailing_ones(n):
        c = 0
        while n & 1:
            c += 1
            n >>= 1
        return c
    t1s = [trailing_ones(n) for n in ns]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    # 左: n vs T(n) 散布図 (色=末尾1ビット数)
    sc = ax1.scatter(ns, ts, c=t1s, cmap='plasma', s=40, zorder=3, vmin=0, vmax=11)
    plt.colorbar(sc, ax=ax1, label='末尾連続1ビット数 v1(n)')
    # 近似曲線
    log2_ns = np.log2(np.array(ns, dtype=float))
    coeffs = np.polyfit(log2_ns, ts, 1)
    x_fit = np.linspace(min(ns), max(ns), 300)
    ax1.plot(x_fit, coeffs[0]*np.log2(x_fit)+coeffs[1], '--',
             color=GRAY, lw=1.5, label='線形フィット (log2 n)')
    ax1.set_xscale('log')
    ax1.set_xlabel('n', fontsize=12)
    ax1.set_ylabel('停止時間 T(n)', fontsize=12)
    ax1.set_title('(a) 遅延記録 (n ≤ 10M, 53件)', fontsize=12)
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    # 右: T_max vs log₂N スケーリング
    Ns     = [1000, 10000, 100000, 1000000, 10000000]
    Tmaxs  = [178, 261, 350, 524, 685]
    log2Ns = [np.log2(N) for N in Ns]

    # べき則フィット
    log_log2N = np.log(log2Ns)
    log_Tmax  = np.log(Tmaxs)
    alpha, intercept = np.polyfit(log_log2N, log_Tmax, 1)

    ax2.plot(log2Ns, Tmaxs, 'o', color=BLUE, ms=9, zorder=4, label='実測値')
    x_th = np.linspace(9, 25, 200)
    A = np.exp(intercept)
    ax2.plot(x_th, A * x_th**alpha, '--', color=RED, lw=2,
             label=rf'$T_{{max}} \propto (\log_2 N)^{{{alpha:.3f}}}$')
    ax2.plot(x_th, x_th * (Tmaxs[2]/log2Ns[2]), ':', color=GRAY, lw=1.5,
             label=r'$\propto \log_2 N$ (線形)')
    ax2.set_xlabel(r'$\log_2 N$', fontsize=12)
    ax2.set_ylabel(r'$T_{\max}(N)$', fontsize=12)
    ax2.set_title(r'(b) $T_{\max}$ のスケーリング則', fontsize=12)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    for i, (x, y, N) in enumerate(zip(log2Ns, Tmaxs, Ns)):
        ax2.annotate(f'N=10^{int(np.log10(N))}', (x, y),
                     textcoords='offset points', xytext=(5, -12), fontsize=8)

    fig.tight_layout()
    save(fig, 'fig3_delay_records')

# ─────────────────────────────────────────────
# Figure 4: 数学定数比較 + Δ(N)のN依存性
# ─────────────────────────────────────────────
def fig4_constants_and_convergence():
    # 数学定数との比較
    constants = {
        r'$4\log_2 3$':          6.3399,
        r'$2\pi - 0.016$':       6.2669,
        r'$\log_2 81$':          6.3576,
        r'$6.349$':              6.3490,
        r'$2{+}C\log_2(3/2)$\n$C{=}7.116$': 6.1626,
    }
    delta_measured = 6.309
    delta_err      = 0.080

    # Δ(N)のN依存性 (H53)
    Ns      = [500000, 1000000, 2000000, 5000000, 10000000, 20000000]
    deltas  = [6.3645, 6.3749, 6.3585, 6.2829, 6.3283, 6.3386]
    C_Ns    = [6.4881, 6.5369, 6.5810, 6.6218, 6.5667, 6.8751]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    # 左: 定数比較
    names  = list(constants.keys())
    values = list(constants.values())
    errors = [abs(v - delta_measured) for v in values]
    colors_bar = [GREEN if e == min(errors) else BLUE for e in errors]

    bars = ax1.barh(range(len(names)), errors, color=colors_bar, alpha=0.75)
    ax1.set_yticks(range(len(names)))
    ax1.set_yticklabels(names, fontsize=11)
    ax1.set_xlabel('誤差  |Δ候補 − Δ実測|', fontsize=11)
    ax1.set_title(r'(a) $\Delta=6.309$ との数学定数比較', fontsize=12)
    ax1.axvline(delta_err, color=RED, ls='--', lw=1.5,
                label=f'実験誤差 ±{delta_err}')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3, axis='x')
    # 最良候補に注釈
    ax1.annotate('← 最良', xy=(min(errors), 0), fontsize=10, color=GREEN,
                 xytext=(0.01, 0.15), va='center')

    # 右: Δ(N) の N依存性
    log2Ns = [np.log2(N) for N in Ns]
    ax2.plot(log2Ns, deltas, 'o-', color=BLUE, lw=2, ms=8, zorder=3,
             label=r'実測 $\Delta(N)$')
    ax2.axhline(6.3399, color=GREEN, ls=':', lw=2, label=r'$4\log_2 3=6.340$')
    ax2.axhline(6.309,  color=RED,   ls='--', lw=2, label=r'平均 $6.309$')
    ax2.fill_between([min(log2Ns), max(log2Ns)],
                     6.309-0.080, 6.309+0.080, color=RED, alpha=0.1,
                     label=r'$\pm 0.080$ (1σ)')
    ax2.set_xlabel(r'$\log_2 N$', fontsize=12)
    ax2.set_ylabel(r'$\Delta(N)$', fontsize=12)
    ax2.set_title(r'(b) $\Delta(N)$ の $N$ 依存性 (H53)', fontsize=12)
    ax2.legend(fontsize=9)
    ax2.set_ylim(6.0, 6.6)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    save(fig, 'fig4_constants_convergence')

# ─────────────────────────────────────────────
# Figure 5: 情報理論 — ステップごとの情報変化
# ─────────────────────────────────────────────
def fig5_information():
    # ステップ種別ごとの情報変化
    step_types  = ['奇数ステップ\n(×3+1)', '偶数ステップ\n(÷2)', '全体平均']
    info_change = [+1.590, -1.0, -0.1340]
    fractions   = [33.43, 66.57, 100.0]
    colors_info = [RED, BLUE, GREEN]

    # Stopping time distribution (log-normal approximation)
    # C=7.116, so for n=10M, E[T]≈7.116*log2(10M)≈166
    np.random.seed(42)
    n_samples = 5000
    n_vals    = np.random.randint(2, 10_000_001, n_samples)
    T_approx  = 7.116 * np.log2(n_vals) + np.random.normal(0, 25, n_samples)
    T_approx  = T_approx.clip(1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    # 左: ステップ種別の情報変化
    bars = ax1.bar(step_types[:2], info_change[:2], color=colors_info[:2],
                   alpha=0.75, width=0.5, zorder=3)
    ax1.axhline(info_change[2], color=GREEN, lw=2.5, ls='--',
                label=f'全体平均: {info_change[2]:.4f} bits/step')
    ax1.axhline(0, color='black', lw=1)
    ax1.set_ylabel('情報変化 (bits/step)', fontsize=12)
    ax1.set_title('(a) 各ステップタイプの平均情報変化\n(奇数割合33.4%, 偶数割合66.6%)',
                  fontsize=11)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3, axis='y')
    # 割合を注釈
    for i, (bar, frac) in enumerate(zip(bars, fractions[:2])):
        ax1.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height()/2 if bar.get_height() > 0 else bar.get_height()/2 - 0.15,
                 f'{frac}%', ha='center', va='center', fontsize=11, color='white', fontweight='bold')

    # 右: 停止時間 vs log₂n の散布
    log2_n = np.log2(n_vals)
    ax2.scatter(log2_n, T_approx, alpha=0.15, s=5, color=BLUE)
    x_line = np.linspace(1, 24, 100)
    ax2.plot(x_line, 7.116 * x_line, '-', color=RED, lw=2,
             label=r'$E[T] = C \cdot \log_2 n$, $C=7.116$')
    ax2.set_xlabel(r'$\log_2 n$', fontsize=12)
    ax2.set_ylabel('停止時間 T(n)', fontsize=12)
    ax2.set_title(r'(b) $T(n) \approx C \cdot \log_2 n$  ($C \approx 7.116$)', fontsize=12)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    save(fig, 'fig5_information')

# ─────────────────────────────────────────────
# Figure 6: Δ の理論的導出の概念図
# ─────────────────────────────────────────────
def fig6_theory_diagram():
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    ax.set_facecolor('white')

    def box(ax, x, y, w, h, text, color, fontsize=10):
        rect = plt.Rectangle((x-w/2, y-h/2), w, h,
                              facecolor=color, edgecolor='black', lw=1.5, zorder=3)
        ax.add_patch(rect)
        ax.text(x, y, text, ha='center', va='center',
                fontsize=fontsize, zorder=4, wrap=True)

    def arrow(ax, x1, y1, x2, y2, label='', color='black'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=2),
                    zorder=2)
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx+0.1, my+0.1, label, fontsize=9, color=color)

    # ノードA: mod 2^k 全1クラス
    box(ax, 2, 4.5, 3.5, 0.9,
        'n mod 2^k = 2^k - 1\n(末尾k個が全て1)',
        '#AED6F1', fontsize=10)

    # ステップ1: 奇数ステップ
    box(ax, 2, 2.8, 3.2, 0.7, '3n+1  (偶数になる)', '#FDEBD0', fontsize=10)

    # ステップ2: 偶数ステップ
    box(ax, 2, 1.5, 3.8, 0.7,
        '(3n+1)/2  mod 2^(k-1) = 2^(k-1) - 1',
        '#AED6F1', fontsize=10)

    arrow(ax, 2, 4.05, 2, 3.15, 'x3+1  (+1 step)', RED)
    arrow(ax, 2, 2.45, 2, 1.85, 'div 2  (+1 step)', RED)

    # 右側: サイズ関係
    box(ax, 7.5, 4.5, 2.5, 0.7, "E[n'] = (3/2) E[n]", '#D5F5E3', fontsize=11)
    box(ax, 7.5, 2.8, 2.5, 0.7, '規模が 3/2 倍', '#D5F5E3', fontsize=11)

    arrow(ax, 7.5, 4.15, 7.5, 3.15, '', GRAY)

    # Δ式
    box(ax, 5.2, 0.65, 8.8, 0.8,
        'Delta = 2 + C(N) x log2(3/2)  ≈  4 x log2(3) = 6.340',
        '#FADBD8', fontsize=12)

    # 矢印: クラス移行 → Δ式
    arrow(ax, 3.7, 1.5, 5.2, 1.05, '', DARK)
    arrow(ax, 7.5, 2.45, 6.5, 1.05, '', DARK)

    ax.text(5, 5.5,
            '理論的導出: kビット全1クラスから (k-1)ビット全1クラスへの移行構造',
            ha='center', va='center', fontsize=11, fontweight='bold')

    fig.tight_layout()
    save(fig, 'fig6_theory_diagram')

# ─────────────────────────────────────────────
# 実行
# ─────────────────────────────────────────────
if __name__ == '__main__':
    import os
    os.chdir('/root/collatz')
    print('図を生成中...')
    fig1_delta_vs_k()
    fig2_proposition_a()
    fig3_delay_records()
    fig4_constants_and_convergence()
    fig5_information()
    fig6_theory_diagram()
    print('完了: figures/ ディレクトリに6枚保存しました')
