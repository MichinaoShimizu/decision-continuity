---
category: product
checked: 15e9528
---

# 理由の確かさを、書かれていた場所で分けるようになった

## 状態

いまも同じ：理由の 1 行目は `記録あり：<要約>（<どこに書かれていたか>）`・`推測：<内容>`・`不明。` のどれかで、本文に AI の印があれば出典に添え、人の判断と合っているかを問いに足す（[format.md:34][f34]）。日付は JST で書く（[format.md:33][f33]）。

## 起きたこと

- 2026-10-16 「書かれていた理由と他の案」を「理由」節に置き換え、1 行目を記録あり／推測／不明のどれかにした（[PR #24][pr24]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 PR の本文やコミットに AI の印があるか作成者がボットなら「記録あり（AI が書いた本文）」とし、人の判断と合っているかの問いを足すようにした。日付も JST にそろえた（[PR #33][pr33]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 記録ありを、書き手の推測ではなく理由が書かれていた場所で議論／本文／本文・AI の 3 つに分けた。問いを付けるのは本文・AI のときだけにし、文体から AI を推測しないと明記した（[PR #34][pr34]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 「記録あり（差分）」を足し、3 つから 4 つにした（[PR #67][pr67]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 4 つの分け方をやめ、`記録あり：<要約>（<出典>）` の 1 つの形にした。AI の印は出典に添える（[PR #78][pr78]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 指示を SKILL.md と format.md に絞り、「文体から推測しない」の一文はなくなった（[PR #79][pr79]。作成・マージ @MichinaoShimizu、レビューなし）

## 理由

記録あり：変更ごとに PR の本文にある（いずれも AI の印あり）。

- PR #33：このリポジトリで audit を試運転して見つかった 2 つの穴をふさぐ（PR #33 の本文）
- PR #34：AI が書いたかどうかは印がなければ分からないので、書き手を推測せず出典で分ける。「本文」に毎回問いを付けると多すぎる（PR #34 の本文）
- PR #78・#79：決まりと指示が増えすぎて重くなっていたので、精度に効かない部分を削った（PR #78・#79 の本文）

## 分かっていないこと

- 理由に「推測」を書く方針の根拠は何か（PR #24 の本文にはない。@MichinaoShimizu に聞く）
- 「文体から推測しない」の一文を消したのは意図どおりか（@MichinaoShimizu に聞く）
- PR #33・#34・#78 の本文（AI の印あり）の理由は、@MichinaoShimizu の判断と合っているか

[pr24]: https://github.com/MichinaoShimizu/decision-continuity/pull/24
[pr33]: https://github.com/MichinaoShimizu/decision-continuity/pull/33
[pr34]: https://github.com/MichinaoShimizu/decision-continuity/pull/34
[pr67]: https://github.com/MichinaoShimizu/decision-continuity/pull/67
[pr78]: https://github.com/MichinaoShimizu/decision-continuity/pull/78
[pr79]: https://github.com/MichinaoShimizu/decision-continuity/pull/79
[f33]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/references/format.md#L33
[f34]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/references/format.md#L34

## 追記 2026-10-18

**分かった**（2026-10-18）：「「文体から推測しない」の一文を消したのは意図どおりか」

PR #79 を書いた Claude が、削るときに意図せず落としたもの。Decision log を書き直したときに見つかり、@MichinaoShimizu の判断で [PR #82](https://github.com/MichinaoShimizu/decision-continuity/pull/82) で戻した（会話で。元の場所なし）。
