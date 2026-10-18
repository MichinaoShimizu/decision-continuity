---
kind: log
category: product
keywords: [lang=en, English, What happened, Documented, CATEGORIES_EN, index_lang]
---

# [decision-continuity] 頼まれたら Decision log を英語で書けるようになった

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-17 いまも同じ：`lang=en` と頼むか、リポジトリの指示（`CLAUDE.md`・`AGENTS.md` など）が英語を求めるときに、本文を英語で書くようにした。形は日本語と同じで、決まった言葉だけを置き換える。`build_index.py` は両方の言語を読み、索引の言語は `--lang`、いまの索引、多いほうの順に決める（テストも追加）。履歴：[PR #56](https://github.com/MichinaoShimizu/decision-continuity/pull/56) ／ 現在：`writing.md` の「英語で書くとき」、[`skills/decision-log/references/categories.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/skills/decision-log/references/categories.md) の英語の表

## 理由

記録あり（本文・AI）：kiroku のように文書が英語のリポジトリで使えるように（PR #56 本文）。

## 関わった人

PR の記録から。決めた人とは限らない。いずれもレビューとコメントはなく、承認は見えない。

- PR #56：作成 @MichinaoShimizu（2026-10-17）、マージ @MichinaoShimizu（2026-10-17）

## 分かっていないこと

- 英語で書いた Decision log を、実際のリポジトリ（kiroku など）で使ったか。

## 関係する記録

- DL-8、DL-14
