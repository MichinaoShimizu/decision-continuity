---
kind: log
category: architecture
keywords: [decision-log-planner, decision-log-reader, サブエージェント, 並列, InvokeSubagents, 1 回に 4 つ, sleep]
---

# [decision-continuity] 洗い出しと読むことをサブエージェントに任せ、メインの会話はコマンドをほとんど回さない形になった

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-18 いまも同じ：手順 0〜1 の洗い出しを新しいサブエージェント `decision-log-planner` に任せ、候補は件数によらず `decision-log-reader` に読ませるようにした。これまでは候補が 5 件を超えたときだけ reader に分けていた。planner と `investigation.md` の言葉と定数の正規表現が揃っているかを確かめるテストも足した。履歴：[PR #59](https://github.com/MichinaoShimizu/decision-continuity/pull/59) ／ 現在：[`agents/claude/decision-log-planner.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/agents/claude/decision-log-planner.md)、[`skills/decision-log/references/investigation.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/skills/decision-log/references/investigation.md)
- C2 2026-10-18 いまも同じ：reader は 1 回の応答でまとめて呼ぶ（Kiro は 1 回に 4 つまでなので、分類が多ければまとめて 4 つ以内にする）と手順に書いた。履歴：[PR #59](https://github.com/MichinaoShimizu/decision-continuity/pull/59)（中のコミット `e4d0779`） ／ 現在：`investigation.md` の「サブエージェントに分ける」
- C3 2026-10-18 いまも同じ：サブエージェントの終わりを `sleep` やファイルの監視で待たないと手順に書いた。履歴：[PR #69](https://github.com/MichinaoShimizu/decision-continuity/pull/69) ／ 現在：[`skills/decision-log/references/commands.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/skills/decision-log/references/commands.md)

## 理由

記録あり（本文・AI）：

- C1：Kiro でメインの会話に `git log` などの確認が出続けていた。エージェントの定義に書いた許可は、そのサブエージェントの中でだけ効く（PR #59 本文）。
- C2：reader を 1 つずつ順に呼んでいた（PR #59 の変更の断片）。
- C3：評価で、メインのエージェントが `sleep 60` や `until …` で終わりを待とうとして止められていた（PR #69 本文）。

## 関わった人

PR の記録から。決めた人とは限らない。いずれもレビューとコメントはなく、承認は見えない。

- PR #59・#69：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-18）

## 分かっていないこと

- Kiro の実機で、planner に任せたあとメインの会話の確認が消えたか、reader が並列（1 回に 4 つ）で動いたかを確かめたか。PR #59 の本文は「実際の Kiro での動作はまだ確認していない」とする。
- 手順が planner の定義と `investigation.md` の二か所にある。揃えているのは言葉と正規表現だけで、PR #68 では `git -C` の禁止を両方に書き足す必要があった。一か所にまとめる予定はあるか。

## 関係する記録

- DL-3、DL-4、DL-7
