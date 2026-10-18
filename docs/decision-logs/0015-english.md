---
category: product
checked: 15e9528
---

# 頼まれたら Decision log を英語で書けるようになった

**いま**：頼んだ人の言葉で書き、英語を求められたら（頼まれた、`CLAUDE.md` などの指示）英語で書く（[format.md:37][f37]）。`build_index.py` は両方の言語を読み、索引の言語はいまの索引か多いほうに合わせる（[build_index.py:257][bi]）。

## 起きたこと

- 2026-10-17 `lang=en` と頼むか、リポジトリの指示が英語を求めるときに英語で書くようにした。形は日本語と同じで、決まった言葉だけを置き換える。`build_index.py` は両方の言語を読む（[PR #56][pr56]）
- 2026-10-18 `lang=en` の指定をなくし、「リポジトリが英語なら英語」にした（[PR #79][pr79] の最初のコミット）。評価で、英語の README を見て英語で書いたため、同じ PR の中で「頼んだ人の言葉で書く」に直した（[PR #79][pr79]）

いずれも作成・マージ @MichinaoShimizu、レビューなし。

## 理由

記録あり：kiroku のように文書が英語のリポジトリで使えるように（PR #56 の本文。AI の印あり）。日本語で頼んだのに英語で書くのを避ける（PR #79 の中のコミット `dae70ef` のメッセージ。AI の印あり）。

## 分かっていないこと

- 英語で書いた Decision log を、実際のリポジトリ（kiroku など）で使ったか（@MichinaoShimizu に聞く）。

[pr56]: https://github.com/MichinaoShimizu/decision-continuity/pull/56
[pr79]: https://github.com/MichinaoShimizu/decision-continuity/pull/79
[f37]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/references/format.md#L37
[bi]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/scripts/build_index.py#L257
