---
kind: log
category: release
keywords: [plugin.json, marketplace.json, npx skills, install.sh, CLAUDE_SKILL_DIR, .agents/skills, 入れ方]
---

# [decision-continuity] 入れ方が、ファイルを写すだけから、プラグインと install.sh の 1 行になった

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-17 いまも同じ：リポジトリをそのまま Claude Code のプラグインとマーケットプレイスにし、npx skills でもスキルを入れられるようにした。入れ方は「写す」の 1 つから 3 つになった（テストも追加）。履歴：[PR #54](https://github.com/MichinaoShimizu/decision-continuity/pull/54) ／ 現在：[`.claude-plugin/plugin.json`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/.claude-plugin/plugin.json)
- C2 2026-10-18 置き換え済み：README に、npx skills で入るのは `main` の最新で、タグを付ければ版を決められると書いた。履歴：[PR #58](https://github.com/MichinaoShimizu/decision-continuity/pull/58) ／ 現在：[PR #66](https://github.com/MichinaoShimizu/decision-continuity/pull/66) で README から npx skills の記載がなくなった（0 日後）
- C3 2026-10-18 いまも同じ：`tools/install.sh` を足し、Kiro ではスキルとサブエージェントを 1 つのコマンドで入れ直せるようにした（テストも追加）。README の入れ方はこれを使う形に替わり、版を固定するときは `git clone --branch` を使う。履歴：[PR #63](https://github.com/MichinaoShimizu/decision-continuity/pull/63) ／ 現在：[`tools/install.sh`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/tools/install.sh)、[`README.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/README.md)
- C4 2026-10-18 置き換え済み：README を 7,415 から 2,754 バイトに縮めた（流れの図、古い版の入れ方、許可の説明を削った）。履歴：[PR #62](https://github.com/MichinaoShimizu/decision-continuity/pull/62) ／ 現在：[PR #66](https://github.com/MichinaoShimizu/decision-continuity/pull/66) でさらに縮み、基準のコミットで 1,463 バイト（0 日後）
- C5 2026-10-18 置き換え済み：README に、入れ方ごとの導入・更新・削除のコマンドを並べた（Claude Code のコマンドは公式ドキュメントで確かめたと本文にある）。履歴：[PR #65](https://github.com/MichinaoShimizu/decision-continuity/pull/65) ／ 現在：[PR #66](https://github.com/MichinaoShimizu/decision-continuity/pull/66) で注記が削られ、シェルのコマンド 3 つと Kiro の 2 行だけになった（0 日後）。Claude Code の許可の例は `docs/claude-code-permissions.md` に移った

## 理由

記録あり（本文・AI）：

- C1：似た道具の多くは 1 行で入る。写す入れ方だけでは、見つけてもらいにくく、入れてもらいにくかった（PR #54 本文）。
- C3：Kiro は npx skills でスキルしか入らず、サブエージェントを写し忘れると確認が出続けていた（PR #63 本文）。
- C2・C4・C5：本文にあるのは何を変えたかだけで、なぜ縮めたか、なぜ npx skills の記載を消したかは書かれていない。

## 関わった人

PR の記録から。決めた人とは限らない。いずれもレビューとコメントはなく、承認は見えない。

- PR #54：作成 @MichinaoShimizu（2026-10-17）、マージ @MichinaoShimizu（2026-10-17）
- PR #58・#62・#63・#65・#66：作成 @MichinaoShimizu、マージ @MichinaoShimizu（いずれも 2026-10-18）

## 分かっていないこと

- README を短くし続けた理由と、npx skills の記載を消したのは、勧めない入れ方にしたからか（@MichinaoShimizu に聞く）。CHANGELOG の v0.1.0 には npx skills で入れられるとある。
- README の導入のコマンド（`claude plugin install … --marketplace …`）は Claude Code 2.1.292 以降が要るが、README からその条件は削られた。古い版の利用者をどう扱うつもりか。
- PR #54 の「まだ確かめていないこと」（GitHub からのインストール、プラグインで入れたときに reader を名前で呼べるか）は、その後確かめたか。

## 関係する記録

- DL-3、DL-12
