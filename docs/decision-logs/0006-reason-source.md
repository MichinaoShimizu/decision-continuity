---
kind: log
category: product
keywords: [記録あり, 推測, 不明, 本文・AI, Generated with Claude Code, JST, TZ=Asia/Tokyo]
---

# [decision-continuity] 理由の確かさを、書かれていた場所で分けるようになった

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-16 いまも同じ：「書かれていた理由と他の案」を「理由」節に置き換え、1 行目を「記録あり／推測／不明」のどれかにした。履歴：[PR #24](https://github.com/MichinaoShimizu/decision-continuity/pull/24) ／ 現在：[`writing.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/references/writing.md) の「理由」
- C2 2026-10-17 置き換え済み：PR 本文やコミットに AI の印があるか作成者がボットなら「記録あり（AI が書いた本文）」とし、人の判断と合っているかの問いを足すようにした。日付も JST にそろえた。履歴：[PR #33](https://github.com/MichinaoShimizu/decision-continuity/pull/33) ／ 現在：[PR #34](https://github.com/MichinaoShimizu/decision-continuity/pull/34) で分け方が替わった。JST の規則は [`investigation.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/references/investigation.md) の手順 0 に残る
- C3 2026-10-17 いまも同じ：「記録あり」を、書き手の推測ではなく、理由が書かれていた場所で議論／本文／本文・AI の 3 つに分けた。問いを付けるのは「本文・AI」のときだけにし、文体から AI を推測しないと明記した。履歴：[PR #34](https://github.com/MichinaoShimizu/decision-continuity/pull/34) ／ 現在：[`SKILL.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/SKILL.md) の「守ること」2

## 理由

記録あり（本文・AI）：

- C2：このリポジトリで audit を試運転して見つかった 2 つの穴をふさぐ（PR #33 本文）。
- C3：AI が書いたかどうかは印がなければ分からないので、書き手を推測せず出典で分ける。「本文」に毎回問いを付けると多すぎる（PR #34 本文）。

## 関わった人

PR の記録から。決めた人とは限らない。いずれも承認は見えず、レビューはない。

- PR #24：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-16）
- PR #33・#34：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-17）

## 分かっていないこと

- 理由に「推測」を書く方針の根拠は何か（PR #24 の本文にはない）。

## 関係する記録

- DL-8

---

## 追記 2026-10-18（Claude、再確認）

**再確認**（2026-10-18、fbc765a）
**いま**：理由の 1 行目は記録あり／推測／不明のどれか。記録ありは、書かれていた場所で議論・本文・本文・AI・差分の 4 つに分ける。

- C3：いまも同じ → 一部置き換え済み。[PR #67][pr67] で「記録あり（差分）」が足され、3 つから 4 つになった（1 日後）
- C1 はいまも同じ

[pr67]: https://github.com/MichinaoShimizu/decision-continuity/pull/67
