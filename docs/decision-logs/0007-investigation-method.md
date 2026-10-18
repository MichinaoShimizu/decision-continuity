---
category: product
checked: 15e9528
---

# 候補の絞り込みが、タイトルとファイル名から、差分の洗い出しを含む形になった

## 状態

いまも同じ：調べ役 `decision-log-planner` が手元の git で、言葉（`-i` あり）・定数（`-i` なし）・設定ファイルの変更の 3 つを別々に洗い、大事なものから 20 件を分類に分ける（[decision-log-planner.md:13-17][p13]）。`depth=` と `resume` はなく、置き場所は言われたらそこを使う（[SKILL.md:13-15][s13]）。

## 起きたこと

- 2026-10-16 履歴を手元の git で 1 回取り、パスで候補を絞り、候補だけネットワークで取る形にした。`depth=`（既定 20）を新設した（[PR #15][pr15]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 `resume` を廃止し、人が指定したパスを置き場所の筆頭にした（[PR #31][pr31]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 候補をタイトルとファイル名だけで選ばず、全件の差分も言葉で洗う（`git log -i -G`）ようにした。マージコミットの本文 1 行目を PR のタイトルとして読む（[PR #42][pr42]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 分類に `engineering` と `cost` を足し、重なりを直した。索引の見出しの下に分類の中身を書く（[PR #43][pr43]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-17 洗い出しを 1 つから 3 つ（言葉は `-i` あり、定数は `-i` なし、設定ファイルの変更）に分けた（[PR #49][pr49]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 洗い出しを `decision-log-planner` に任せ、planner の定義にも同じ手順を書いた（DL-13）（[PR #59][pr59]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 `depth=` をやめて読む候補を 20 件に固定し、既存の Decision log の `keywords` を言葉に足すこともやめた。分類の表は categories.md から format.md に移った（[PR #79][pr79]。作成・マージ @MichinaoShimizu、レビューなし）

## 理由

記録あり：変更ごとに PR の本文にある（いずれも AI の印あり）。

- PR #15：大きなリポジトリでは PR を 1 件ずつネットワークで取り、全差分と全ログを読むので遅い（PR #15 の本文）
- PR #31：`audit` は何も書かないので `resume` で再開するものがない。ユーザー指定のパスが 2 番目だったため、キットを入れていると書き込みが無視された（PR #31 の本文）
- PR #42：「fix typo」という名前でタイムアウトを変えた変更や、`settings.py` の値の変更を取りこぼしうる（PR #42 の本文）
- PR #43：分類が重なっていた（PR #43 の本文）
- PR #49：`-i` が定数部分にも効き、小文字の代入に当たって候補があふれた（PR #49 の本文）
- PR #79：指示を SKILL.md と format.md の 2 つに絞り、54KB から 14KB にする（PR #79 の本文）。`depth=` をやめた理由そのものは書かれていない

## 分かっていないこと

- 定数の正規表現に当たらない言語の慣習（camelCase の定数など）をどう扱うか（@MichinaoShimizu に聞く）
- 分類の `other` が増えたときの見直しの基準はあるか（format.md は「多ければ分類を見直す」とだけ書く。@MichinaoShimizu に聞く）
- 読む候補を 20 件に固定し、`depth=` で変えられなくしたのはなぜか（@MichinaoShimizu に聞く）
- PR の本文（AI の印あり）の理由は、@MichinaoShimizu の判断と合っているか

[pr15]: https://github.com/MichinaoShimizu/decision-continuity/pull/15
[pr31]: https://github.com/MichinaoShimizu/decision-continuity/pull/31
[pr42]: https://github.com/MichinaoShimizu/decision-continuity/pull/42
[pr43]: https://github.com/MichinaoShimizu/decision-continuity/pull/43
[pr49]: https://github.com/MichinaoShimizu/decision-continuity/pull/49
[pr59]: https://github.com/MichinaoShimizu/decision-continuity/pull/59
[pr79]: https://github.com/MichinaoShimizu/decision-continuity/pull/79
[p13]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/agents/claude/decision-log-planner.md#L13-L17
[s13]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/SKILL.md#L13-L15
