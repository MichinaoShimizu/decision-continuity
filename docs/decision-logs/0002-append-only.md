---
kind: log
category: product
keywords: [append-only, updateDiscussion, 追記, 書き換えない, premises]
---

# [decision-continuity] 記録の本文は書き換えず、追記で育てる形になった

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-03 置き換え済み：記録の本文を書き換えず、結果も崩れた前提もコメントで追記する形にした。置き換えは、古い記録に新しい番号をコメントして閉じる。`discussion` ワークフローから `update` を外した。履歴：[PR #8](https://github.com/MichinaoShimizu/decision-continuity/pull/8) ／ 現在：ワークフローは削除済み（[PR #45](https://github.com/MichinaoShimizu/decision-continuity/pull/45)）
- C2 2026-10-16 置き換え済み：追記を Discussions のコメントから、ファイル末尾の `## 追記 YYYY-MM-DD` に替えた。履歴：[PR #13](https://github.com/MichinaoShimizu/decision-continuity/pull/13) ／ 現在：`records.py` は削除済み
- C3 2026-10-17 いまも同じ：決まりとして「本文は書いたあと書き換えない。訂正と後の変化は追記で足す」が残った。履歴：[PR #45](https://github.com/MichinaoShimizu/decision-continuity/pull/45) ／ 現在：[`SKILL.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/SKILL.md) の「守ること」6

## 理由

記録あり（本文・AI）：PR #8 の本文に、Actions のトークンでは `updateDiscussion` が "Resource not accessible by integration" で失敗するとある。追記だけにする理由がこの失敗だけなのか、書き換えられない記録を求めたのかは、本文からは分からない。

## 関わった人

PR の記録から。決めた人とは限らない。

- PR #8：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-03）。承認は見えない
- PR #13：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-16）。承認は見えない
- PR #45：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-17）。承認は見えない

## 分かっていないこと

- 追記だけにする方針は、トークンの制約への対処か、書き換えられない記録を求める意図が先にあったか（@MichinaoShimizu に聞く）。

## 関係する記録

- DL-1

---

## 追記 2026-10-18（Claude、再確認）

**再確認**（2026-10-18、fbc765a）
**いま**：本文は書き換えず、追記で育てる。確かめ直した結果も「再確認」の追記で足す形になった（DL-14 の後の PR #73）。

- C3 はいまも同じ（SKILL.md の守ること 6）
