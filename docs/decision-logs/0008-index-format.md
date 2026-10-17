---
kind: log
category: compatibility
keywords: [build_index.py, FILE_RE, DL-, 索引, 理由不明, 日付順, frontmatter, 起きたこと]
---

# [decision-continuity] Decision log の形と索引の作り方が、手書きの表からスクリプト生成の日付順の一覧になった

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-16 一部置き換え済み：YAML を `kind`・`category`・`repos`・`paths`・`keywords` に絞り、「関わった人」節を新設した。履歴：[PR #16](https://github.com/MichinaoShimizu/decision-continuity/pull/16) ／ 現在：frontmatter は `kind`・`category`・`keywords` だけ（[`writing.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/references/writing.md)）
- C2 2026-10-16 いまも同じ：索引を表から 1 行の一覧にした。追記の印「分かった」を足した。履歴：[PR #21](https://github.com/MichinaoShimizu/decision-continuity/pull/21) ／ 現在：`writing.md` の「追記の印」
- C3 2026-10-16 いまも同じ：「主張と証拠」を「起きたこと」に統合し、1 行を `C<番号> <日付> <状態>：…。履歴：… ／ 現在：…` にした。履歴：[PR #23](https://github.com/MichinaoShimizu/decision-continuity/pull/23) ／ 現在：`writing.md` の「起きたこと」
- C4 2026-10-17 いまも同じ：索引の並びを番号順から、「起きたこと」の最古の日付順にした。履歴：[PR #26](https://github.com/MichinaoShimizu/decision-continuity/pull/26) ／ 現在：[`build_index.py`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/scripts/build_index.py)
- C5 2026-10-17 いまも同じ：索引の 1 行を `日付 [番号](ファイル) 何が変わったか` とし、理由が不明のときだけ `・理由不明` を付ける形にした。履歴：[PR #28](https://github.com/MichinaoShimizu/decision-continuity/pull/28) ／ 現在：`build_index.py`
- C6 2026-10-17 一部置き換え済み：記録の参照を `#42` ではなく `DL-17` の形にした（GitHub が issue・PR へのリンクにするため）。履歴：[PR #29](https://github.com/MichinaoShimizu/decision-continuity/pull/29) ／ 現在：`DL-` は残る。DR・DF・Q の接頭辞は `records.py` とともに PR #45 で消えた
- C7 2026-10-17 いまも同じ：SKILL.md を核、`references/writing.md`、`scripts/build_index.py` に分けた。履歴：[PR #30](https://github.com/MichinaoShimizu/decision-continuity/pull/30) ／ 現在：[`SKILL.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/SKILL.md)
- C8 2026-10-17 いまも同じ：`build_index.py` が `DL-1.md` のような名前も読み、受けないファイル名は `--check` で終了コード 1 にする。履歴：[PR #38](https://github.com/MichinaoShimizu/decision-continuity/pull/38) ／ 現在：`build_index.py`

## 理由

記録あり（本文・AI）：

- C1：`records.py` も adr-guard も `claims` などを読まないので外す。役割は推測しない（PR #16 本文）。
- C2：理由が分かっても決定が伴わない場合に記録する手段がなかった。2 つのブランチが README を作り直すと衝突する（PR #21 本文）。
- C3：「主張と証拠」は他の節と重複していた（PR #23 本文）。
- C4：後から掘り起こした履歴では、番号の順は変化の時期を表さない（PR #26 本文）。
- C5：履歴から見つけた変更は理由が書かれていないことが多く、要約が不明ばかりになる。理由があっても要約で確かさと出典が落ちる（PR #28 本文）。
- C6：このリポジトリに PR #12〜#28 があり、記録の `#17` が間違った先を指した（PR #29 本文）。
- C7：Agent Skills の指針（本体は小さく、詳細は references に、決まった処理は scripts に）に合わせる（PR #30 本文）。
- C8：`FILE_RE` が `0001.md` と `0001-英小文字.md` しか拾わず、合わないファイルを黙って飛ばしていた（PR #38 本文）。

## 関わった人

PR の記録から。決めた人とは限らない。いずれも承認は見えず、レビューはない。

- PR #16・#21・#23：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-16）
- PR #26・#28・#29・#30・#38：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-17）

## 分かっていないこと

- PR #16 で `repos`・`paths` を frontmatter に残したのに、いまの例にないのはいつ、なぜ外れたか（読み手の確認では経緯が見つからなかった）。
- C8 で、ファイル名の `DL-` を読めるのに `--check` は終了コード 1 にする二重の扱いは意図どおりか。

## 関係する記録

- DL-1
