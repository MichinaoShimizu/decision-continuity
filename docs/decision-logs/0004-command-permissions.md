---
kind: log
category: security
keywords: [allowed-tools, allowedCommands, permissions, gh api, TZ=, env, 1 回に 1 コマンド, 信頼できない本文]
---

# [decision-continuity] 確認なしで通すコマンドが、読むだけのものに絞られていった

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-17 いまも同じ：Kiro 用 reader の許可を `git show|log|grep|rev-parse`、`TZ=Asia/Tokyo git log`、`gh pr view` に絞り、`for` ループと `;`・`&&`・`|` を禁じた。`glab` は外した。履歴：[PR #40](https://github.com/MichinaoShimizu/decision-continuity/pull/40) ／ 現在：[`agents/kiro/decision-log-reader.json`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/agents/kiro/decision-log-reader.json)
- C2 2026-10-17 いまも同じ：スキルの `allowed-tools` を `Bash(git:*)`・`gh:*`・`glab:*` から、読むだけのコマンドに絞った。履歴：[PR #46](https://github.com/MichinaoShimizu/decision-continuity/pull/46) ／ 現在：[`SKILL.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/SKILL.md) の frontmatter
- C3 2026-10-17 いまも同じ：評価で、索引スクリプトを絶対パスや `;` でつないで呼んで許可に当たらなかった例が出たため、「守ること」に「コマンドは 1 回に 1 つ、ルートからの相対パス」を足した。履歴：[PR #50](https://github.com/MichinaoShimizu/decision-continuity/pull/50) ／ 現在：`SKILL.md` の「守ること」10
- C4 2026-10-17 いまも同じ：GraphQL が止められた環境のため、REST の GET（`gh api repos/…`）で読む手順を足し、Kiro CLI 2.x の許可と README の例に加えた。履歴：[PR #51](https://github.com/MichinaoShimizu/decision-continuity/pull/51) ／ 現在：`agents/kiro/decision-log-reader.json`、[`README.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/README.md)
- C5 2026-10-17 いまも同じ：`TZ=` は `env` を付けずに先頭へ書く、PR の一覧に `gh pr list` を使わない、と手順に足した。履歴：[PR #52](https://github.com/MichinaoShimizu/decision-continuity/pull/52) ／ 現在：[`investigation.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/references/investigation.md) の手順 0

## 理由

記録あり（本文・AI）：

- C1：PR 本文にコマンドを仕込まれると確認なしで実行されうる。`for n in .*` と `gh .*` が広すぎた（PR #40 本文）。
- C2：実行中に `git push` や `gh pr merge` まで確認なしで通っていた。信頼できない PR の本文を読むため（PR #46 本文）。
- C3：評価 E06 が確認なしの許可に当たらない呼び方をして索引が古いままだった（PR #50 本文）。
- C4：reader が許可のないコマンドで 11 回拒否され、6 件の「いまの姿」を確かめられなかった。GraphQL が止められた環境で `gh pr view` が使えなかった（PR #51 本文）。
- C5：メインのエージェントが `env TZ=…` と `gh pr list` で確認待ちになった。`gh pr list` は GraphQL を使うので許可しても失敗する（PR #52 本文）。

## 関わった人

PR の記録から。決めた人とは限らない。いずれも承認は見えず、レビューはない。

- PR #40・#46・#50・#51・#52：作成 @MichinaoShimizu、マージ @MichinaoShimizu（いずれも 2026-10-17）。PR #50 には作成者本人の回し直しのコメントがある

## 分かっていないこと

- Kiro V3 の glob の `*` が `;` や `-X` まで当たるかは Kiro 側の照合しだいと PR #40・#51 の本文にある。その後確かめたか。
- Kiro V3 で REST の GET を毎回の確認なしで許可する方法は見つかったか。

## 関係する記録

- DL-3

---

## 追記 2026-10-18（Claude）

**分かった**（2026-10-18）：「Kiro V3 で REST の GET を毎回の確認なしで許可する方法は見つかったか。」
reader の `permissions` に `gh api repos/*` を allow で足し、書き込みになる指定（`-X`・`--method`・`-f`・`-F`・`--raw-field`・`--input`）を deny で止める。Kiro 3.x は deny が allow に勝つ、という公式ドキュメントの説明による。答えたのは PR の記録で、作成 @MichinaoShimizu。元の場所：[PR #69](https://github.com/MichinaoShimizu/decision-continuity/pull/69)。PR の本文は Kiro 3.x の実機では確かめていないとする。

## 追記 2026-10-18（Claude、PR #53 以降の変化）

PR #53 以降の変化。

- C6 2026-10-18 いまも同じ：新しい `decision-log-planner` の定義に、手順 0〜1 の git のコマンドだけの許可を入れた。Kiro 2.x 向けの正規表現は、記号を一重引用符の中だけ許す形にした。履歴：[PR #59](https://github.com/MichinaoShimizu/decision-continuity/pull/59) ／ 現在：[`agents/kiro/decision-log-planner.json`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/agents/kiro/decision-log-planner.json)
- C7 2026-10-18 いまも同じ：`git -C <パス>` を付けない、引数の記号は一重引用符で囲む、と手順に書いた。理由は記録あり（本文・AI）：評価で reader と planner が `git -C /…/repo show …` と書いて許可に当たらず拒否されていた（PR #68 の中のコミット `a98c49c` のメッセージ）。PR #53 の本文にも、`git -C` で確認待ちや拒否になったとある。履歴：[PR #68](https://github.com/MichinaoShimizu/decision-continuity/pull/68) ／ 現在：[`skills/decision-log/references/commands.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/skills/decision-log/references/commands.md)

## 追記 2026-10-18（Claude、再確認）

**再確認**（2026-10-18、fbc765a）
**いま**：確認なしで通すのは読むだけのコマンド。Kiro 3.x では REST の GET も許し、書き込みの指定は deny で止める。コマンドの書き方は `references/commands.md` にまとまった。

- C1：いまも同じ → 一部置き換え済み。[PR #69][pr69] で、Kiro 3.x の許可に `gh api repos/*` の allow と、書き込みの指定の deny が足された（1 日後）
- C3 はいまも同じ（守ること 10 は [PR #69][pr69] で短くなり、中身は `references/commands.md` に移った）
- C4 はいまも同じ（README の設定例は [PR #66][pr66] で `docs/claude-code-permissions.md` に移った）
- C2・C5・C6・C7 はいまも同じ

[pr66]: https://github.com/MichinaoShimizu/decision-continuity/pull/66
[pr69]: https://github.com/MichinaoShimizu/decision-continuity/pull/69
