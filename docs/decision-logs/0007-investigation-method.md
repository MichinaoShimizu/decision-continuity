---
kind: log
category: product
keywords: [depth, first-parent, -G, resume, 洗い出し, 定数, 設定ファイル, 候補]
---

# [decision-continuity] 候補の絞り込みが、タイトルとファイル名から、差分の洗い出しを含む形になった

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-16 いまも同じ：履歴を手元の git で 1 回取り、パスで候補を絞り、候補だけネットワークで取る形にした。`depth=`（既定 20）を新設した。履歴：[PR #15](https://github.com/MichinaoShimizu/decision-continuity/pull/15) ／ 現在：[`SKILL.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/SKILL.md)、[`investigation.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/references/investigation.md)
- C2 2026-10-17 いまも同じ：`resume` を廃止し、人が指定したパスを置き場所の筆頭にした。履歴：[PR #31](https://github.com/MichinaoShimizu/decision-continuity/pull/31) ／ 現在：`SKILL.md` のモード表に `resume` はない
- C3 2026-10-17 一部置き換え済み：候補をタイトルとファイル名だけで選ばず、全件の差分も言葉で洗う（`git log -i -G`）ようにした。マージコミットの本文 1 行目を PR のタイトルとして読む。履歴：[PR #42](https://github.com/MichinaoShimizu/decision-continuity/pull/42) ／ 現在：C4 で 3 つに分かれた
- C4 2026-10-17 いまも同じ：洗い出しを 3 つに分けた（言葉は `-i` あり、定数は `-i` なし、設定ファイルの変更）。履歴：[PR #49](https://github.com/MichinaoShimizu/decision-continuity/pull/49) ／ 現在：`investigation.md` の手順 1
- C5 2026-10-17 いまも同じ：分類に `engineering` と `cost` を足し、重なりを直した。索引の見出しの下に分類の中身を書く。履歴：[PR #43](https://github.com/MichinaoShimizu/decision-continuity/pull/43) ／ 現在：[`categories.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/references/categories.md)

## 理由

記録あり（本文・AI）：

- C1：大きなリポジトリでは PR を 1 件ずつネットワークで取り、全差分と全ログを読むので遅い（PR #15 本文）。
- C2：`audit` は何も書かないので `resume` で再開するものがない。ユーザー指定のパスが 2 番目だったため、キットを入れていると書き込みが無視された（PR #31 本文）。
- C3：「fix typo」という名前でタイムアウトを変えた変更や、`settings.py` の値の変更を取りこぼしうる（PR #42 本文）。
- C4：`-i` が定数部分にも効き、小文字の代入に当たって候補があふれた（PR #49 本文）。
- C5：分類が重なっていた（PR #43 本文）。

## 関わった人

PR の記録から。決めた人とは限らない。いずれも承認は見えず、レビューはない。

- PR #15：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-16）
- PR #31・#42・#43・#49：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-17）

## 分かっていないこと

- 定数の正規表現に当たらない言語の慣習（camelCase の定数など）をどう扱うか。
- 分類の `other` が増えたときの見直しの基準はあるか。

## 関係する記録

- DL-5、DL-6

---

## 追記 2026-10-18（Claude、再確認）

**再確認**（2026-10-18、fbc765a）
**いま**：候補は手元の git で洗い、3 つの洗い出し（言葉・定数・設定ファイル）を合わせる。洗い出しは [PR #59][pr59] から `decision-log-planner` が行う（DL-13）。

- C1・C2・C4・C5 はいまも同じ（手順の中身は同じで、[PR #59][pr59] で planner の定義にも同じ手順が書かれた）

[pr59]: https://github.com/MichinaoShimizu/decision-continuity/pull/59
