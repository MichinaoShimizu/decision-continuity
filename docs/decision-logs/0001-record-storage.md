---
category: architecture
checked: 15e9528
---

# 記録の置き場所が Discussions から records/ を経て、置き場所を持たない汎用ツールになった

**いま**：このリポジトリは記録の置き場所を兼ねず、`decision-log` とその planner・reader だけを配る。Decision log は `docs/decision-logs/` か、言われたフォルダーに書く（[SKILL.md:14][s14]）。

## 起きたこと

- 2026-10-03 `decision-record` スキルを新設し、決定の記録の置き場所を GitHub Discussions にした（フォーム、`config.yaml`、評価ケースを含む）（[PR #1][pr1]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-15 コードのリポジトリ向けに `adr/` を足した（reverse-adr、adr-guard、forward-adr、評価、テンプレート）（[PR #9][pr9]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-15 ADR と Decision log も Discussions に移し、`forward-adr` を廃止して `decision-record` に寄せた。状態は提案中・有効・終了で、縛るのは有効だけにした（[PR #10][pr10]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-16 置き場所を Discussions から `records/` の Markdown（1 件 1 ファイル）に替え、`records.py check` で本文の書き換えを検出するようにした（[PR #13][pr13]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-16 記録データを本文末の yaml から先頭の frontmatter に移した（[PR #17][pr17]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 リポジトリ名を `decision-continuity` にした（[PR #39][pr39]。作成・マージ @MichinaoShimizu、レビューなし）。いまも [README.md:1][r1] の見出し
- 2026-10-17 記録の置き場所を兼ねるのをやめ、`decision-log` とその reader だけを配る汎用ツールにした。`decision-record`、`adr-guard`、`adr/`（reverse-adr の後継は `skills/decision-log/`）、`records/`、`records.py`、`config.yaml`、旧評価を削除した。置き場所は「人が指定したフォルダー」か `docs/decision-logs/` の 2 つになり、SKILL.md の「記録の置き場所」の表に書いた（[PR #45][pr45]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 SKILL.md の「記録の置き場所」の表をやめ、`write` は `docs/decision-logs/`（置き場所を言われたらそこ）に書く、の 1 行にした（[PR #79][pr79]。作成・マージ @MichinaoShimizu、レビューなし）

## 理由

記録あり：PR #45 で汎用ツールに絞った（PR #45 の本文に「このリポジトリは記録の置き場所を兼ねない。完成している decision-log と、その読み手のサブエージェントだけを配る汎用のツールにする」。AI の印あり）。adr-guard と decision-record は「再考中」とされた。

Discussions、`records/` と置き場所を選んだ理由は、PR #1・#10・#13 の本文に書かれていない。PR #13 の本文にあるのは、追記だけで育てる決まりをファイルの末尾への追記で守れること、Discussions の既存記録は移さないこと（このセッションでは GraphQL が使えないため）だけである。

## 分かっていないこと

- 置き場所を Discussions にした理由と、ほかの案を比べたか（@MichinaoShimizu に聞く）
- Discussions をやめて `records/` にした決め手は、GraphQL が使えないことか、レビューできる形にしたかったのか（@MichinaoShimizu に聞く）
- Discussions にあった記録は移されたか、使われないまま終わったか（@MichinaoShimizu に聞く）
- 「再考中」の adr-guard と decision-record を再開するか、記録の置き場所を今後どこに置く想定か（@MichinaoShimizu に聞く）
- PR #3・#4・#6・#7 は PR でも issue でもなく（REST で 404）、Discussions か削除されたものかは確かめられていない（@MichinaoShimizu に聞く）
- PR #45 の理由は AI の印のある本文にある。人の判断と合っているか（@MichinaoShimizu に聞く）

[pr1]: https://github.com/MichinaoShimizu/decision-continuity/pull/1
[pr9]: https://github.com/MichinaoShimizu/decision-continuity/pull/9
[pr10]: https://github.com/MichinaoShimizu/decision-continuity/pull/10
[pr13]: https://github.com/MichinaoShimizu/decision-continuity/pull/13
[pr17]: https://github.com/MichinaoShimizu/decision-continuity/pull/17
[pr39]: https://github.com/MichinaoShimizu/decision-continuity/pull/39
[pr45]: https://github.com/MichinaoShimizu/decision-continuity/pull/45
[pr79]: https://github.com/MichinaoShimizu/decision-continuity/pull/79
[s14]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/SKILL.md#L14
[r1]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/README.md#L1
