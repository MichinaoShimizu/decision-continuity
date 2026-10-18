---
category: architecture
checked: 15e9528
---

# Kiro の対応が、薄い入口の方式から、reader を JSON と Markdown の両方で置く形になった

## 状態

いまも同じ：Kiro 用の `decision-log-reader` は JSON と Markdown の両方で置かれ（[decision-log-reader.json:2][kj2]、[decision-log-reader.md:2][km2]）、planner も同じ形で置かれている（DL-13）。スキルは分類ごとに reader を名前で呼び、Kiro では 1 回に 4 つまで並べる（[SKILL.md:31][s31]）。

## 起きたこと

- 2026-10-16 Kiro 用に `.kiro/skills/` へキット全体を二重に写すのをやめ、`.claude/skills/` を完全版にして、Kiro には本文が「そちらを読め」だけの薄い入口を置いた（[PR #18][pr18]。作成・マージ @MichinaoShimizu、レビューなし）。`adr/templates/kiro/` は [PR #45][pr45] で削除された
- 2026-10-17 `decision-log-reader` を新設した。Claude 用と Kiro 用はどちらも Markdown。候補が 5 件を超えたら分類ごとに名前で呼ぶ（[PR #27][pr27]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 Kiro 用の定義を Markdown から JSON に替えた。登録がなければ既定のサブエージェントで読む（[PR #37][pr37]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 Kiro 用の定義を JSON と Markdown の両方で置く形にした（[PR #44][pr44]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 呼び方の説明を `references/investigation.md` の「サブエージェントに分ける」から SKILL.md の手順 3 と続く段落に移し（investigation.md は削除）、reader の定義を短くした。JSON と Markdown の両方で置くことは変わらない（[PR #79][pr79]。作成・マージ @MichinaoShimizu、レビューなし）

## 理由

記録あり：二重のコピーのずれ、Kiro で使われなかったこと、Kiro の版ごとに読める形が違うことへの対処（PR #18・#27・#37・#44 の本文。AI の印あり）。

- PR #18：2 つのコピーがずれる恐れがあった。
- PR #27：Kiro はプロンプトで名前を指定するか description が合うときだけサブエージェントを使うため、実際には使われなかった。
- PR #37：Markdown での定義は Kiro IDE 1.0 と CLI V3 以降で、それより前は JSON しか読まない。登録のない名前で呼ぶと失敗する。
- PR #44：Kiro の CLI は JSON、IDE は Markdown しか読まないという報告があり（kirodotdev/Kiro#8040、未解決）、JSON だけだと IDE で登録されない。

## 分かっていないこと

- PR #27 の本文は実際の Kiro や Claude Code では未確認とする。その後、実機で名前による委譲を確かめたか（@MichinaoShimizu に聞く）
- PR #44 の本文が求めた、IDE と CLI での名前による呼び出しの確認は済んだか。同名の `.json` と `.md` が並んだときの Kiro の挙動はどうか（@MichinaoShimizu に聞く）
- 薄い入口の方式を捨てた理由は、PR #45 の本文には書かれていない（@MichinaoShimizu に聞く）
- 理由は AI の印のある本文にある。人の判断と合っているか（@MichinaoShimizu に聞く）

[pr18]: https://github.com/MichinaoShimizu/decision-continuity/pull/18
[pr27]: https://github.com/MichinaoShimizu/decision-continuity/pull/27
[pr37]: https://github.com/MichinaoShimizu/decision-continuity/pull/37
[pr44]: https://github.com/MichinaoShimizu/decision-continuity/pull/44
[pr45]: https://github.com/MichinaoShimizu/decision-continuity/pull/45
[pr79]: https://github.com/MichinaoShimizu/decision-continuity/pull/79
[kj2]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/agents/kiro/decision-log-reader.json#L2
[km2]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/agents/kiro/decision-log-reader.md#L2
[s31]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/SKILL.md#L31
