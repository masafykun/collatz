# 🔢 Collatz Conjecture — Computational Research

> 77の仮説と2億件の計算実験で、コラッツ予想の構造に迫る。命題Aの帰納法証明がほぼ完成。

コラッツ予想 (3n+1問題) を計算実験的に探索したPythonプロジェクトです。  
n ≤ 2×10⁸ の大規模探索・77仮説の検証・命題Aの数学的証明構造の発見を行いました。  
VPS (1vCPU / 960MB RAM) 上での継続的な計算実験です。

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![matplotlib](https://img.shields.io/badge/matplotlib-3.x-11557c?style=flat-square)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)

🔗 **[論文草案 (paper_draft.md)](paper_draft.md)**

---

## 📸 結果図

| Δ vs k (命題A) | 命題A の余裕推移 |
|:---:|:---:|
| ![fig1](figures/fig1_delta_vs_k.png) | ![fig2](figures/fig2_proposition_a.png) |

| 遅延記録 & スケーリング則 | 数学定数比較 & Δ収束 |
|:---:|:---:|
| ![fig3](figures/fig3_delay_records.png) | ![fig4](figures/fig4_constants_convergence.png) |

| 情報損失の可視化 | 理論的導出の概略図 |
|:---:|:---:|
| ![fig5](figures/fig5_information.png) | ![fig6](figures/fig6_theory_diagram.png) |

---

## ✨ 主要な観察・考察

- **命題A（末尾全1ビット則）の帰納法証明** — n ≡ 2^k−1 (mod 2^k) の剰余クラスが最大停止時間を持つことを示す帰納法がほぼ完成。補題1〜4は数学的に完全証明済み（基底 k=1 の解析的証明のみ残課題）。k≤15, n≤5×10⁶ で反例ゼロ
- **Δ公式** — kビット全1クラス間の停止時間差分 Δ = 6.309 ± 0.080 を計測し、理論式 `Δ = 2 + C(N)×log₂(3/2)` を導出。最良近似定数は 4log₂3 ≈ 6.340。この形での定式化は既存文献に見当たらなかった
- **n ≤ 2×10⁸ 範囲での最長停止時間** — n = 169,941,673 が 953ステップ（この探索範囲内での確認。世界記録ではない）
- **情報理論的収束根拠** — 全軌道を通じた情報損失 −0.1340 bits/step が、収束の情報理論的な直観を与える
- **スケーリング則** — 最大停止時間 T_max ∝ (log₂N)^1.596 の超対数的成長を確認

> **注記:** 本研究は計算実験に基づく探索的研究です。命題Aの帰納段の証明は数学的に完成していますが、基底 k=1 の解析的証明は未完です。Δ公式の定式化は既存文献への徹底的な調査を経ておらず、独自性の確認には査読が必要です。

---

## 🛠️ 技術スタック

| カテゴリ | 技術 |
|---|---|
| 言語 | Python 3.10+ |
| 数値計算 | numpy, collections |
| 可視化 | matplotlib (Noto Sans CJK JP フォント) |
| PDF生成 | Pandoc + Typst |
| 実行環境 | Linux VPS (1vCPU, 960MB RAM) |

---

## 📁 ディレクトリ構成

```
collatz/
├── research.py      # H1–H16   初期仮説検証
├── research2.py     # H11–H16  (再探索)
├── research3.py     # H17–H22
├── research4.py     # H23–H28
├── research5.py     # H29–H34
├── research6.py     # H35–H40
├── research7.py     # H41–H46
├── research8.py     # H47–H52
├── research9.py     # H53–H58
├── research10.py    # H59–H64  命題A拡張探索
├── research11.py    # H65–H66  完全テーブル再検証
├── research12.py    # H67–H69  証明構造形式化
├── research13.py    # H70–H75  帰納法Step深堀り
├── research14.py    # H75–H77  完全証明まとめ
├── explorer.py      # 対話的探索スクリプト
├── explorer2.py     # 200M範囲遅延記録探索
├── make_figures.py  # 6つの論文図を生成
├── paper_draft.md   # 論文草案 (全文)
└── figures/         # 生成済みPNG図 (6枚)
```

---

## 🚀 セットアップ

```bash
# 依存パッケージをインストール
pip install matplotlib numpy

# フォント (Ubuntu / Debian)
sudo apt install fonts-noto-cjk

# 仮説検証スクリプトを実行 (H1–H16)
python3 research.py

# すべての仮説を順番に実行 (H1–H58)
for i in "" 2 3 4 5 6 7 8 9; do python3 research${i}.py; done

# 論文図を生成
python3 make_figures.py

# 論文PDFを生成 (Pandoc + Typst が必要)
pandoc --from=markdown+tex_math_dollars --to=typst paper_draft.md -o paper_draft.typ
typst compile paper_draft.typ paper_draft.pdf
```

---

## 📄 コラッツ予想について

```
C(n) = n / 2      (n が偶数のとき)
C(n) = 3n + 1     (n が奇数のとき)
```

どんな正整数 n から始めても、この操作を繰り返すと最終的に 1 に到達する — という未解決問題です (1937年, Lothar Collatz)。  
2026年時点で n < 2⁶⁹ まで計算機による検証済みですが、一般的な証明はまだ存在しません。

---

## ライセンス

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

このプロジェクトは **MIT ライセンス** のもとで公開しています。

© 2026 masafykun (https://github.com/masafykun)
