---
category: compatibility
checked: 15e9528
---

# Decision log の形と索引の作り方が、手書きの表からスクリプト生成の日付順の一覧になった

## 状態

いまも同じ：索引は分類ごとに「起きたこと」の最古の日付順で `- <日付> [DL-<番号>](<ファイル>) <タイトル>` を並べ、理由が不明なら `・理由不明` を付ける（[build_index.py:221-228][b221]）。フロントマターは `category` と `checked` だけで（[format.md:5-6][f5]）、`DL-` を付けたファイル名は読むが `--check` で直すよう知らせる（[build_index.py:104-105][b104]）。

## 起きたこと

- 2026-10-16 YAML を `kind`・`category`・`repos`・`paths`・`keywords` に絞り、「関わった人」節を新設した（[PR #16][pr16]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-16 索引を表から 1 行の一覧にした。追記の印「分かった」を足した（[PR #21][pr21]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-16 「主張と証拠」を「起きたこと」に統合し、1 行を `C<番号> <日付> <状態>：…。履歴：… ／ 現在：…` にした（[PR #23][pr23]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 索引の並びを番号順から、「起きたこと」の最古の日付順にした（[PR #26][pr26]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 索引の 1 行を `日付 [番号](ファイル) 何が変わったか` とし、理由が不明のときだけ `・理由不明` を付ける形にした（[PR #28][pr28]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 記録の参照を `#42` ではなく `DL-17` の形にした（[PR #29][pr29]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 SKILL.md を核、`references/writing.md`、`scripts/build_index.py` に分けた（[PR #30][pr30]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 `build_index.py` が `DL-1.md` のような名前も読み、受けないファイル名は `--check` で終了コード 1 にした（[PR #38][pr38]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 DR・DF・Q の接頭辞が `records.py` とともに消え、`DL-` だけが残った（[PR #45][pr45]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 フロントマターに `checked`（基準のコミット）を足した（[PR #73][pr73]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 起きたことの行の番号（C1）をやめ、状態を 5 つから 3 つに、追記の印を 4 つから 2 つ（分かった／終了）にした（[PR #78][pr78]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 フロントマターを `category` と `checked` だけにし（`kind`・`keywords` をやめた）、状態の語・「履歴：／現在：」・関わった人の節・タイトルの `[repo]` をやめた。writing.md をなくし、形は `references/format.md` に書く（[PR #79][pr79]。作成・マージ @MichinaoShimizu、レビューなし）

## 理由

記録あり：変更ごとに PR の本文にある（いずれも AI の印あり）。

- PR #16：`records.py` も adr-guard も `claims` などを読まないので外す。役割は推測しない（PR #16 の本文）
- PR #21：理由が分かっても決定が伴わない場合に記録する手段がなかった。2 つのブランチが README を作り直すと衝突する（PR #21 の本文）
- PR #23：「主張と証拠」は他の節と重複していた（PR #23 の本文）
- PR #26：後から掘り起こした履歴では、番号の順は変化の時期を表さない（PR #26 の本文）
- PR #28：履歴から見つけた変更は理由が書かれていないことが多く、要約が不明ばかりになる。理由があっても要約で確かさと出典が落ちる（PR #28 の本文）
- PR #29：このリポジトリに PR #12〜#28 があり、記録の `#17` が間違った先を指した。GitHub が `#42` を issue・PR へのリンクにする（PR #29 の本文）
- PR #30：Agent Skills の指針（本体は小さく、詳細は references に、決まった処理は scripts に）に合わせる（PR #30 の本文）
- PR #38：`FILE_RE` が `0001.md` と `0001-英小文字.md` しか拾わず、合わないファイルを黙って飛ばしていた（PR #38 の本文）
- PR #78・#79：決まりと指示が増えすぎて重くなっていたので、精度に効かない部分を削った（PR #78・#79 の本文）

## 分かっていないこと

- PR #16 で `repos`・`paths` を frontmatter に残したのに、その後の例から外れたのはいつ、なぜか（読み手の確認では経緯が見つからなかった。@MichinaoShimizu に聞く）
- ファイル名の `DL-` を読めるのに `--check` は終了コード 1 にする二重の扱いは意図どおりか（@MichinaoShimizu に聞く）
- PR の本文（AI の印あり）の理由は、@MichinaoShimizu の判断と合っているか

[pr16]: https://github.com/MichinaoShimizu/decision-continuity/pull/16
[pr21]: https://github.com/MichinaoShimizu/decision-continuity/pull/21
[pr23]: https://github.com/MichinaoShimizu/decision-continuity/pull/23
[pr26]: https://github.com/MichinaoShimizu/decision-continuity/pull/26
[pr28]: https://github.com/MichinaoShimizu/decision-continuity/pull/28
[pr29]: https://github.com/MichinaoShimizu/decision-continuity/pull/29
[pr30]: https://github.com/MichinaoShimizu/decision-continuity/pull/30
[pr38]: https://github.com/MichinaoShimizu/decision-continuity/pull/38
[pr45]: https://github.com/MichinaoShimizu/decision-continuity/pull/45
[pr73]: https://github.com/MichinaoShimizu/decision-continuity/pull/73
[pr78]: https://github.com/MichinaoShimizu/decision-continuity/pull/78
[pr79]: https://github.com/MichinaoShimizu/decision-continuity/pull/79
[b104]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/scripts/build_index.py#L104-L105
[b221]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/scripts/build_index.py#L221-L228
[f5]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/references/format.md#L5-L6
