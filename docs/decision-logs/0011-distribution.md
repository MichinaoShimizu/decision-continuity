---
category: release
checked: 15e9528
---

# 入れ方が、ファイルを写すだけから、プラグインと install.sh の 1 行になった

**いま**：Claude Code はプラグインとして `claude plugin install` で、Kiro は `tools/install.sh` を呼ぶ 1 行で入れる（[README.md:8-27][readme]、[install.sh][install]）。

## 起きたこと

- 2026-10-17 リポジトリをそのまま Claude Code のプラグインとマーケットプレイスにし、npx skills でもスキルを入れられるようにした。入れ方は「写す」の 1 つから 3 つになった（[PR #54][pr54]）
- 2026-10-18 README に、npx skills で入るのは `main` の最新で、タグで版を決められると書いた（[PR #58][pr58]）。PR #66 で README から npx skills の記載がなくなった
- 2026-10-18 README を 7,415 から 2,754 バイトに縮めた（[PR #62][pr62]）
- 2026-10-18 `tools/install.sh` を足し、Kiro でスキルとサブエージェントを 1 つのコマンドで入れ直せるようにした（[PR #63][pr63]）
- 2026-10-18 README に入れ方ごとの導入・更新・削除のコマンドを並べた（[PR #65][pr65]）。PR #66 で注記を削り、シェルのコマンド 3 つと Kiro の 2 行（1,463 バイト）にした（[PR #66][pr66]）
- 2026-10-18 `install.sh` が `CDPATH` を設定した環境でパスを壊していたのを直した（[PR #76][pr76]）

いずれも作成・マージ @MichinaoShimizu、レビューなし。

## 理由

記録あり：似た道具の多くは 1 行で入り、写すだけでは見つけてもらいにくい（PR #54 の本文。AI の印あり）。Kiro は npx skills でスキルしか入らず、サブエージェントを写し忘れると確認が出続けていた（PR #63 の本文。AI の印あり）。

README を縮めた理由と、npx skills の記載を消した理由は書かれていない。

## 分かっていないこと

- README を縮め続け、npx skills の記載を消したのは、勧めない入れ方にしたからか（@MichinaoShimizu に聞く）。
- `claude plugin install … --marketplace …` は Claude Code 2.1.292 以降が要るが、README からその条件は消えた。古い版の人をどう扱うか。

[pr54]: https://github.com/MichinaoShimizu/decision-continuity/pull/54
[pr58]: https://github.com/MichinaoShimizu/decision-continuity/pull/58
[pr62]: https://github.com/MichinaoShimizu/decision-continuity/pull/62
[pr63]: https://github.com/MichinaoShimizu/decision-continuity/pull/63
[pr65]: https://github.com/MichinaoShimizu/decision-continuity/pull/65
[pr66]: https://github.com/MichinaoShimizu/decision-continuity/pull/66
[pr76]: https://github.com/MichinaoShimizu/decision-continuity/pull/76
[readme]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/README.md#L8-L27
[install]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/tools/install.sh#L1-L5
