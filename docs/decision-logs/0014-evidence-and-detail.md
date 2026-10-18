---
category: product
checked: 15e9528
---

# 理由の証拠を広く読み、起きたことに値の前後を書く形になった

**いま**（15e9528）：reader は行のコメント、PR の中のコミット、参照された issue（1 段）、差分のコードのコメントも読む（[reader:11-14][r11]）。起きたことには値の前後を書く（[format.md:33][f33]）。置き換えまでの日数と、行ごとの形の検査はもうない。

## 起きたこと

- 2026-10-18 reader が、行のレビューのコメント（`pulls/<N>/comments`）、PR の中のコミットのメッセージ、参照された issue とそのコメント（1 段だけ）を読むようにした。コードのコメントや CHANGELOG を出典にする「記録あり（差分）」を足し、`gh` で読めない外部のリンクは「未読」として挙げるようにした（[PR #67][pr67]）
- 2026-10-18 起きたことに、値の前後（`3 から 5`）、テストやドキュメントも変わったか、置き換わるまでの日数を書くことにし、状態に「一部置き換え済み」を足した。`build_index.py --check` が各行（状態の語、「履歴：」と「現在：」、番号の重なり）を確かめるようにした（[PR #68][pr68]）
- 2026-10-18 「記録あり（差分）」を `記録あり：<要約>（<出典>）` の 1 つの形に含めた（[PR #78][pr78]）。状態の語、「履歴：／現在：」、行の番号と、その検査をやめた（[PR #79][pr79]）

いずれも作成・マージ @MichinaoShimizu、レビューなし。

## 理由

記録あり：このリポジトリの Decision log を読み直すと、理由はほぼ PR の本文からしか取れていなかった。行のコメントは `gh pr view --json reviews,comments` に入らず、`--first-parent` はマージコミットしか見ない（PR #67 の本文。AI の印あり）。出力の情報を増やし、崩れを機械で捕まえる（PR #68 の本文。AI の印あり）。

## 分かっていないこと

- 行のコメントや参照された issue を読むことは、評価では `gh` が使えず試されていない。実際のリポジトリで理由の取れる割合は上がったか（@MichinaoShimizu が確かめる）。
- コードのコメントだけが古いまま残り、いまのコードと食い違うときの扱いは決まっていない。

[pr67]: https://github.com/MichinaoShimizu/decision-continuity/pull/67
[pr68]: https://github.com/MichinaoShimizu/decision-continuity/pull/68
[pr78]: https://github.com/MichinaoShimizu/decision-continuity/pull/78
[pr79]: https://github.com/MichinaoShimizu/decision-continuity/pull/79
[r11]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/agents/claude/decision-log-reader.md#L11-L14
[f33]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/references/format.md#L33
