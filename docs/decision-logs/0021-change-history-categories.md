---
category: product
checked: 51b209e
---

# change-history の主な変更を、行の数を決めずに分類ごとに書くことにした

## ステータス

Active：change-history の SKILL.md は、月の主な変更と年の要点を `### <分類>` の下に書き、行の数を決めない。分類は decision-log と同じ 11 種で、行のある分類だけを書く（`skills/change-history/SKILL.md` の手順 2・4）。`build_history.py` は中身をそのまま残し、表には最初の行を入れる。2 つのスキルの分類が揃っていることは `tests/test_docs.py` が確かめる。

## 起きたこと

- 2026-10-19 月の主な変更と年の要点を「3〜5 行」から、行の数を決めない分類ごとの書き方に変えた。分類は decision-log の `format.md` の 11 種と同じにした（ブランチ change-history-categories。作成 @MichinaoShimizu）

## 理由

記録あり：「主な変更は3から5行である必要はない。カテゴリ別にだしたい」（@MichinaoShimizu、会話 2026-10-19）。分類は、decision-log と同じもの・機能や修正で分けるもの・置き場所で分けるものの 3 案から、@MichinaoShimizu が decision-log と同じものを選んだ（会話 2026-10-19）。2 つのスキルで分類がそろい、「なぜ」まで要るテーマを同じ分類のまま decision-log に回せる。

## 分かっていないこと

- 行の数を決めないと、変更の多い月で主な変更が長くなりすぎないか。実際のリポジトリで確かめる。
