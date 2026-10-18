---
category: product
checked: 15e9528
---

# スキルと Decision log の形を、ぎりぎりまで簡素にした

## ステータス

Active：指示は [SKILL.md][skill] と [format.md][format] の 2 つだけで、モードは `audit` と `write`。Decision log は「いま」、起きたこと、理由、分かっていないことの 4 つで、前の形も [build_index.py][bi] が読む。

## 起きたこと

- 2026-10-18 状態を 5 つから 3 つに、理由を `記録あり：<要約>（<出典>）` の 1 つの形に、追記の印を 4 つから 2 つに絞り、分類と `checked` はフロントマターで直すようにした。指示は 54KB から 39KB に（[PR #78][pr78]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 行の番号（`C1`）、状態の語、「履歴：／現在：」、関わった人の節、`kind`・`keywords` をやめ、references を `format.md` の 1 つにまとめた。指示は 14KB に。評価で見つかった 2 点（英語の README を見て英語で書いた、確かめ直しで調査を最初から回した）も直した（[PR #79][pr79]。作成・マージ @MichinaoShimizu、レビューなし）

## 理由

記録あり：決まりと指示が多すぎて、書くモデルが崩しやすく、読む人にも重い。リリースのたびに「再確認」の追記が要る仕組みも手間を生んでいた（PR #78 の本文。AI の印あり）。

## 分かっていないこと

- 行ごとの状態と `keywords` をなくしたことで、変更の多いリポジトリや 2 回目以降の洗い出しで精度が落ちないか（評価 E01〜E10 は main と同じく通ったが、合成のリポジトリでの結果。@MichinaoShimizu が実際のリポジトリで確かめる）。
- PR 本文の理由は、人の判断と合っているか（本文は AI が書いた。@MichinaoShimizu に聞く）。

[pr78]: https://github.com/MichinaoShimizu/decision-continuity/pull/78
[pr79]: https://github.com/MichinaoShimizu/decision-continuity/pull/79
[skill]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/SKILL.md#L11-L15
[format]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/references/format.md
[bi]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/scripts/build_index.py#L63-L64

## 追記 2026-10-18

- 2026-10-18 「いま」の行を「## ステータス」の節に移し、`Active`・`Superseded`・`Removed` のどれかで始めるようにした。起きたこと（履歴）とステータスを混ぜないため。行の中のハッシュもやめた（[PR #83](https://github.com/MichinaoShimizu/decision-continuity/pull/83)。作成 @MichinaoShimizu）
