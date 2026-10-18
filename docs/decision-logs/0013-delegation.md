---
category: architecture
checked: 15e9528
---

# 洗い出しと読むことをサブエージェントに任せ、メインの会話はコマンドをほとんど回さない形になった

## 状態

いまも同じ：洗い出しは `decision-log-planner`、読むのは分類ごとの `decision-log-reader` で、reader は 1 回の応答でまとめて呼ぶ（Kiro は 4 つまで）（[SKILL.md:30-31][s30]）。`sleep` で待たない決まりは、いまの指示にはない。

## 起きたこと

- 2026-10-18 洗い出しを新しい `decision-log-planner` に任せ、候補は件数によらず reader に読ませるようにした。それまでは候補が 5 件を超えたときだけ reader に分けていた（[PR #59][pr59]）
- 2026-10-18 reader を 1 回の応答でまとめて呼ぶ（Kiro は 1 回に 4 つまで）と書いた（[PR #59][pr59] の中のコミット `e4d0779`）
- 2026-10-18 サブエージェントの終わりを `sleep` やファイルの監視で待たないと書いた（[PR #69][pr69]）
- 2026-10-18 手順を SKILL.md の 6 行と planner・reader の定義にまとめた。このとき `sleep` で待たない決まりが落ちた（[PR #79][pr79]）

いずれも作成・マージ @MichinaoShimizu、レビューなし。

## 理由

記録あり：Kiro でメインの会話に `git log` などの確認が出続けていた。エージェントの定義の許可は、そのサブエージェントの中でだけ効く（PR #59 の本文。AI の印あり）。reader を 1 つずつ順に呼んでいた（PR #59 の変更の断片）。評価で、メインが `sleep 60` で終わりを待とうとして止められていた（PR #69 の本文。AI の印あり）。

## 分かっていないこと

- Kiro の実機で、メインの会話の確認が消えたか、reader が 4 つ並列で動いたか（PR #59 の本文は「まだ確認していない」。@MichinaoShimizu に聞く）。
- `sleep` で待たない決まりを PR #79 で落としたのは意図したことか。

[pr59]: https://github.com/MichinaoShimizu/decision-continuity/pull/59
[pr69]: https://github.com/MichinaoShimizu/decision-continuity/pull/69
[pr79]: https://github.com/MichinaoShimizu/decision-continuity/pull/79
[s30]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/SKILL.md#L30-L31

## 追記 2026-10-18

**分かった**（2026-10-18）：「`sleep` で待たない決まりを PR #79 で落としたのは意図したことか」

PR #79 を書いた Claude が、削るときに意図せず落としたもの。Decision log を書き直したときに見つかり、@MichinaoShimizu の判断で [PR #82](https://github.com/MichinaoShimizu/decision-continuity/pull/82) で戻した（会話で。元の場所なし）。
