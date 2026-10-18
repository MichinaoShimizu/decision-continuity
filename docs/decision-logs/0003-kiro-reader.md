---
kind: log
category: architecture
keywords: [decision-log-reader, .kiro/agents, .kiro/skills, thin pointer, 薄い入口, JSON, Markdown]
checked: fbc765a
---

# [decision-continuity] Kiro の対応が、薄い入口の方式から、reader を JSON と Markdown の両方で置く形になった

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-16 置き換え済み：Kiro 用に `.kiro/skills/` へキット全体を二重に写すのをやめ、`.claude/skills/` を完全版にして、Kiro には本文が「そちらを読め」だけの薄い入口を置いた。履歴：[PR #18](https://github.com/MichinaoShimizu/decision-continuity/pull/18) ／ 現在：`adr/templates/kiro/` は基準のコミットにない（[PR #45](https://github.com/MichinaoShimizu/decision-continuity/pull/45) で削除）
- C2 2026-10-17 置き換え済み：`decision-log-reader` を新設した。Claude 用と Kiro 用はどちらも Markdown。候補が 5 件を超えたら分類ごとに名前で呼ぶ。履歴：[PR #27](https://github.com/MichinaoShimizu/decision-continuity/pull/27) ／ 現在：呼び出しの仕組みは [`investigation.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/references/investigation.md) の「サブエージェントに分ける」に残る。Kiro 側の形は C3 で替わった
- C3 2026-10-17 置き換え済み：Kiro 用の定義を Markdown から JSON に替えた。登録がなければ既定のサブエージェントで読む。履歴：[PR #37](https://github.com/MichinaoShimizu/decision-continuity/pull/37) ／ 現在：C4 で両方置く形になった
- C4 2026-10-17 いまも同じ：Kiro 用の定義を JSON と Markdown の両方で置く。履歴：[PR #44](https://github.com/MichinaoShimizu/decision-continuity/pull/44) ／ 現在：[`agents/kiro/decision-log-reader.json`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/agents/kiro/decision-log-reader.json) と [`.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/agents/kiro/decision-log-reader.md)

## 理由

記録あり（本文・AI）：各 PR の本文に次がある。

- C1：2 つのコピーがずれる恐れがあった（PR #18 本文）。
- C2：Kiro はプロンプトで名前を指定するか description が合うときだけサブエージェントを使うため、実際には使われなかった（PR #27 本文）。
- C3：Markdown での定義は Kiro IDE 1.0 と CLI V3 以降で、それより前は JSON しか読まない。登録のない名前で呼ぶと失敗する（PR #37 本文）。
- C4：Kiro の CLI は JSON、IDE は Markdown しか読まないという報告があり（kirodotdev/Kiro#8040、未解決）、JSON だけだと IDE で登録されない（PR #44 本文）。

## 関わった人

PR の記録から。決めた人とは限らない。いずれも承認は見えず、レビューとコメントはない。

- PR #18：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-16）
- PR #27・#37・#44・#45：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-17）

## 分かっていないこと

- PR #27 の本文は実際の Kiro や Claude Code では未確認とする。その後、実機で名前による委譲を確かめたか。
- PR #44 の本文が求めた、IDE と CLI での名前による呼び出しの確認は済んだか。同名の `.json` と `.md` が並んだときの Kiro の挙動はどうか。
- 薄い入口の方式を捨てた理由は、PR #45 の本文には書かれていない。

## 関係する記録

- DL-1、DL-4

---

## 追記 2026-10-18（Claude、再確認）

**再確認**（2026-10-18、fbc765a）
**いま**：reader は Kiro 用に JSON と Markdown の両方で置く。planner も同じ形で置かれている（DL-13）。

- C4 はいまも同じ（定義と investigation.md は変わったが、両方の形で置くことは同じ）
