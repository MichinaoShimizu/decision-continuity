---
category: engineering
checked: 15e9528
---

# 評価と CI が、旧キット向けのものから decision-log 向けに作り直された

**いま**（15e9528）：評価は E01〜E10（[cases.md][cases]）。キーワードは最後の応答で、書いたファイルは正解表で、サブエージェントは呼び出しで判定する（[run.py][run]）。CI は Python 3.10 と 3.13、markdownlint などを回す（[test.yml][ci]）。

## 起きたこと

- 2026-10-15 評価の固定データから `config.yaml` の写しを消した（[PR #11][pr11]）。`adr/evals/` ごと PR #45 で消えた
- 2026-10-17 `verify-docs.config.json` を足し、大きい SKILL.md を `references/` に分けた（[PR #35][pr35]）。`verify-docs.config.json` は PR #45 で消えた
- 2026-10-17 markdownlint の指摘を 0 件にし、MD013 と MD041 を無効にした（[PR #36][pr36]、[.markdownlint-cli2.jsonc][lint]）
- 2026-10-17 評価を E01〜E07 に作り直し、CI に Python 3.10 と 3.13、リンク、frontmatter、markdownlint を足した（[PR #47][pr47]）
- 2026-10-17 評価を `evals/decision-log/` に移した（[PR #48][pr48]）。検査を `skills/*/SKILL.md` と `agents/` の全件に広げた（[PR #49][pr49]）
- 2026-10-17 実際のエージェントで評価を回して落ちた 2 件を直し、キーワードを最後の応答だけで照らすようにした（[PR #50][pr50]）
- 2026-10-18 理由がコードのコメントにだけある #21 と E08 を足した（[PR #67][pr67]）。E05 の書いたファイルを正解表（`ANSWERS`）と照らすようにした（[PR #68][pr68]）
- 2026-10-18 E07 を、最後の応答の言葉ではなくサブエージェントの呼び出しで判定するようにした（[PR #69][pr69]）。E09（[PR #72][pr72]）と E10（[PR #73][pr73]）を足した
- 2026-10-18 評価の種と正解表を新しい形に合わせた（[PR #78][pr78]、[PR #79][pr79]）

いずれも作成・マージ @MichinaoShimizu、レビューなし。

## 理由

記録あり：PR ごとの本文にある（いずれも AI の印あり）。

- 写しは放っておくとずれる（PR #11）。文書構造の違反を解消する（PR #35）。日本語の段落は 1 行で書くので MD013 を、断片が見出しで始まらないので MD041 を外す（PR #36）。
- 精査で見つかった課題をまとめて直す。評価は合成の履歴で人が読んで判定する（PR #47）。スキルとエージェントが増える前提（PR #48・#49）。照合がツールの結果まで照らして全部当たっていた（PR #50）。
- reader を呼んでいても、最後の応答に名前が出ないと「足りない」になっていた（PR #69）。

## 分かっていないこと

- 判定は同じモデル系統の読みで独立ではない（PR #47・#50 の本文）。別系統や人が読み直す予定はあるか（@MichinaoShimizu に聞く）。

[pr11]: https://github.com/MichinaoShimizu/decision-continuity/pull/11
[pr35]: https://github.com/MichinaoShimizu/decision-continuity/pull/35
[pr36]: https://github.com/MichinaoShimizu/decision-continuity/pull/36
[pr47]: https://github.com/MichinaoShimizu/decision-continuity/pull/47
[pr48]: https://github.com/MichinaoShimizu/decision-continuity/pull/48
[pr49]: https://github.com/MichinaoShimizu/decision-continuity/pull/49
[pr50]: https://github.com/MichinaoShimizu/decision-continuity/pull/50
[pr67]: https://github.com/MichinaoShimizu/decision-continuity/pull/67
[pr68]: https://github.com/MichinaoShimizu/decision-continuity/pull/68
[pr69]: https://github.com/MichinaoShimizu/decision-continuity/pull/69
[pr72]: https://github.com/MichinaoShimizu/decision-continuity/pull/72
[pr73]: https://github.com/MichinaoShimizu/decision-continuity/pull/73
[pr78]: https://github.com/MichinaoShimizu/decision-continuity/pull/78
[pr79]: https://github.com/MichinaoShimizu/decision-continuity/pull/79
[cases]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/evals/decision-log/cases.md#L25-L34
[run]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/evals/decision-log/run.py#L213
[ci]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/.github/workflows/test.yml#L17
[lint]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/.markdownlint-cli2.jsonc#L4-L6
