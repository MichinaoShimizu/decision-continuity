---
kind: log
category: architecture
keywords: [Discussions, records/, records.py, decision-record, adr-guard, config.yaml, STORE, DISCUSSION_TEMPLATE]
---

# [decision-continuity] 記録の置き場所が Discussions から records/ を経て、置き場所を持たない汎用ツールになった

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-03 置き換え済み：`decision-record` スキルを新設し、決定の記録の置き場所を GitHub Discussions にした（フォーム、`config.yaml`、評価ケースを含む）。履歴：[PR #1](https://github.com/MichinaoShimizu/decision-continuity/pull/1) ／ 現在：基準のコミットに `.claude/skills/decision-record/` も `config.yaml` もない（[PR #45](https://github.com/MichinaoShimizu/decision-continuity/pull/45) で削除）
- C2 2026-10-15 置き換え済み：コードのリポジトリ向けに `adr/` を足した（reverse-adr、adr-guard、forward-adr、評価、テンプレート）。履歴：[PR #9](https://github.com/MichinaoShimizu/decision-continuity/pull/9) ／ 現在：`adr/` は基準のコミットにない（PR #45 で削除。reverse-adr の後継は [`skills/decision-log/SKILL.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/SKILL.md)）
- C3 2026-10-15 置き換え済み：ADR と Decision log も Discussions に移し、`forward-adr` を廃止して `decision-record` に寄せた。状態は提案中・有効・終了で、縛るのは有効だけにした。履歴：[PR #10](https://github.com/MichinaoShimizu/decision-continuity/pull/10) ／ 現在：PR #45 で削除
- C4 2026-10-16 置き換え済み：置き場所を Discussions から `records/` の Markdown（1 件 1 ファイル）に替え、`records.py check` で本文の書き換えを検出するようにした。履歴：[PR #13](https://github.com/MichinaoShimizu/decision-continuity/pull/13) ／ 現在：`records/` は基準のコミットにない（PR #45 で削除）
- C5 2026-10-16 置き換え済み：記録データを本文末の yaml から先頭の frontmatter に移した。履歴：[PR #17](https://github.com/MichinaoShimizu/decision-continuity/pull/17) ／ 現在：`records.py` は削除済み。frontmatter の形は [`writing.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/references/writing.md) の例にある
- C6 2026-10-17 いまも同じ：リポジトリ名を `decision-continuity` にした。履歴：[PR #39](https://github.com/MichinaoShimizu/decision-continuity/pull/39) ／ 現在：[`README.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/README.md) の見出し
- C7 2026-10-17 いまも同じ：記録の置き場所を兼ねるのをやめ、`decision-log` とその reader だけを配る汎用ツールにした。`decision-record`、`adr-guard`、`adr/`、`records/`、`config.yaml`、旧評価を削除した。置き場所は「人が指定したフォルダー」か `docs/decision-logs/` の 2 つになった。履歴：[PR #45](https://github.com/MichinaoShimizu/decision-continuity/pull/45) ／ 現在：[`SKILL.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/SKILL.md) の「記録の置き場所」の表

## 理由

記録あり（本文・AI）：PR #45 の本文に「このリポジトリは記録の置き場所を兼ねない。完成している decision-log と、その読み手のサブエージェントだけを配る汎用のツールにする」とある。adr-guard と decision-record は「再考中」とされた。

C1・C3・C4 の置き場所を選んだ理由は、各 PR の本文に書かれていない。PR #13 の本文にあるのは、追記だけで育てる決まりをファイルの末尾への追記で守れること、Discussions の既存記録は移さないこと（このセッションでは GraphQL が使えないため）だけである。

## 関わった人

PR の記録から。決めた人とは限らない。いずれも、承認したレビューは見えず、レビューとコメントはない。

- PR #1・#9・#10・#13・#17・#39・#45：作成 @MichinaoShimizu、マージ @MichinaoShimizu（日付はそれぞれ 2026-10-03、10-15、10-15、10-16、10-16、10-17、10-17）

## 分かっていないこと

- 置き場所を Discussions にした理由と、ほかの案を比べたか（@MichinaoShimizu に聞く）。
- Discussions をやめて `records/` にした決め手。GraphQL が使えないことか、レビューできる形にしたかったのか。
- Discussions にあった記録は移されたか、使われないまま終わったか。
- 「再考中」の adr-guard と decision-record を再開するか、記録の置き場所を今後どこに置く想定か。
- PR #3・#4・#6・#7 は PR でも issue でもなく（REST で 404）、Discussions か削除されたものかは確かめられていない。

## 関係する記録

- DL-2、DL-3
