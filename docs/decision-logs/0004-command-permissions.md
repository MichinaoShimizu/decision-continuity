---
category: security
checked: 15e9528
---

# 確認なしで通すコマンドが、読むだけのものに絞られていった

**いま**（15e9528）：スキルの `allowed-tools` は読むだけのコマンドと索引のスクリプトだけ（[SKILL.md:4][s4]）で、コマンドは 1 回に 1 つ、`;`・`&&`・`|`・`cd`・`git -C` を使わず記号は一重引用符で囲む（[SKILL.md:25][s25]）。Kiro の reader は REST の GET（`gh api repos/*`）を許し、書き込みの指定は deny で止める（[decision-log-reader.json:39][kj39]、[decision-log-reader.json:46][kj46]）。

## 起きたこと

- 2026-10-17 Kiro 用 reader の許可を `git show|log|grep|rev-parse`、`TZ=Asia/Tokyo git log`、`gh pr view` に絞り、`for` ループと `;`・`&&`・`|` を禁じた。`glab` は外した（[PR #40][pr40]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 スキルの `allowed-tools` を `Bash(git:*)`・`gh:*`・`glab:*` から、読むだけのコマンドに絞った（[PR #46][pr46]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 「守ること」10 に「コマンドは 1 回に 1 つ、ルートからの相対パス」を足した（[PR #50][pr50]。作成・マージ @MichinaoShimizu、レビューなし。作成者本人の回し直しのコメントあり）
- 2026-10-17 GraphQL が止められた環境のため、REST の GET（`gh api repos/…`）で読む手順を足し、Kiro CLI 2.x の許可と README の例に加えた（[PR #51][pr51]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 `TZ=` は `env` を付けずに先頭へ書く、PR の一覧に `gh pr list` を使わない、と investigation.md の手順 0 に足した（[PR #52][pr52]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 新しい `decision-log-planner` の定義に、手順 0〜1 の git のコマンドだけの許可を入れた。Kiro 2.x 向けの正規表現は、記号を一重引用符の中だけ許す形にした（[PR #59][pr59]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 README の許可の設定例を `docs/claude-code-permissions.md` に移した（[PR #66][pr66]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 `git -C <パス>` を付けない、引数の記号は一重引用符で囲む、と手順に書いた（[PR #68][pr68]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 Kiro 3.x の reader の `permissions` に `gh api repos/*` の allow と、書き込みになる指定（`-X`・`--method`・`-f`・`-F`・`--raw-field`・`--input`）の deny を足した。守ること 10 を短くし、中身を `references/commands.md` に移した（[PR #69][pr69]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 `references/commands.md` を削除し、SKILL.md の決まり 7 に「1 回に 1 つ、`;`・`&&`・`|`・`cd`・`git -C` を使わず、引数の記号は一重引用符」だけを残した。`env TZ=…` にしない、`gh pr list` を使わない、の文はなくなった（[PR #79][pr79]。作成・マージ @MichinaoShimizu、レビューなし）

## 理由

記録あり：信頼できない PR の本文を読むので、仕込まれたコマンドが確認なしで通らないようにし、評価や実行で許可に当たらず止まった呼び方を直した（PR #40・#46・#50・#51・#52・#69 の本文と、PR #68 の中のコミット `a98c49c` のメッセージ。AI の印あり）。

- PR #40：PR 本文にコマンドを仕込まれると確認なしで実行されうる。`for n in .*` と `gh .*` が広すぎた。
- PR #46：実行中に `git push` や `gh pr merge` まで確認なしで通っていた。信頼できない PR の本文を読むため。
- PR #50：評価 E06 が索引スクリプトを絶対パスや `;` でつないで呼び、確認なしの許可に当たらず索引が古いままだった。
- PR #51：reader が許可のないコマンドで 11 回拒否され、6 件の「いまの姿」を確かめられなかった。GraphQL が止められた環境で `gh pr view` が使えなかった。
- PR #52：メインのエージェントが `env TZ=…` と `gh pr list` で確認待ちになった。`gh pr list` は GraphQL を使うので許可しても失敗する。
- PR #68：評価で reader と planner が `git -C /…/repo show …` と書いて許可に当たらず拒否されていた（コミット `a98c49c`）。[PR #53][pr53] の本文にも、`git -C` で確認待ちや拒否になったとある。
- PR #69：Kiro 3.x は deny が allow に勝つ、という公式ドキュメントの説明による。

## 分かっていないこと

- Kiro V3 の glob の `*` が `;` や `-X` まで当たるかは Kiro 側の照合しだいと PR #40・#51 の本文にある。その後確かめたか（@MichinaoShimizu に聞く）
- PR #69 の本文は Kiro 3.x の実機では確かめていないとする。deny で書き込みが止まることを実機で確かめたか（@MichinaoShimizu に聞く）
- PR #79 で `env TZ=…`・`gh pr list` の注意を外したのは、不要になったからか、短くするためか（@MichinaoShimizu に聞く）
- 理由は AI の印のある本文やコミットにある。人の判断と合っているか（@MichinaoShimizu に聞く）

[pr40]: https://github.com/MichinaoShimizu/decision-continuity/pull/40
[pr46]: https://github.com/MichinaoShimizu/decision-continuity/pull/46
[pr50]: https://github.com/MichinaoShimizu/decision-continuity/pull/50
[pr51]: https://github.com/MichinaoShimizu/decision-continuity/pull/51
[pr52]: https://github.com/MichinaoShimizu/decision-continuity/pull/52
[pr53]: https://github.com/MichinaoShimizu/decision-continuity/pull/53
[pr59]: https://github.com/MichinaoShimizu/decision-continuity/pull/59
[pr66]: https://github.com/MichinaoShimizu/decision-continuity/pull/66
[pr68]: https://github.com/MichinaoShimizu/decision-continuity/pull/68
[pr69]: https://github.com/MichinaoShimizu/decision-continuity/pull/69
[pr79]: https://github.com/MichinaoShimizu/decision-continuity/pull/79
[s4]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/SKILL.md#L4
[s25]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/SKILL.md#L25
[kj39]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/agents/kiro/decision-log-reader.json#L39
[kj46]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/agents/kiro/decision-log-reader.json#L46
