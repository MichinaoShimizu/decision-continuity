---
category: product
checked: 15e9528
---

# 記録の本文は書き換えず、追記で育てる形になった

**いま**（15e9528）：決まりは「書いた本文は書き換えない。後の変化は追記で足す」（[SKILL.md:22][s22]）。追記は末尾の `## 追記 YYYY-MM-DD` で、分類と `checked` だけはフロントマターを直す（[format.md:36][f36]）。確かめ直しも、変わったものに追記して `checked` を進める（[SKILL.md:38][s38]）。

## 起きたこと

- 2026-10-03 記録の本文を書き換えず、結果も崩れた前提も Discussions のコメントで追記する形にした。置き換えは、古い記録に新しい番号をコメントして閉じる。`discussion` ワークフローから `update` を外した（[PR #8][pr8]。作成・マージ @MichinaoShimizu、レビューなし）。このワークフローは [PR #45][pr45] で削除された
- 2026-10-16 追記を Discussions のコメントから、ファイル末尾の `## 追記 YYYY-MM-DD` に替えた（[PR #13][pr13]。作成・マージ @MichinaoShimizu、レビューなし）。`records.py` は PR #45 で削除された
- 2026-10-17 Discussions と `records/` をやめたあとも、決まりとして「本文は書いたあと書き換えない。訂正と後の変化は追記で足す」が SKILL.md の守ること 6 に残った（[PR #45][pr45]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 確かめ直した結果を「再確認」の追記で足す recheck を足した（本文は書き換えない）（[PR #73][pr73]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 守ること 6 に「フロントマターは直してよい」を足し、分類と確かめたコミット（`category`・`checked`）はフロントマターで直す形にした。追記の印は「分かった」「終了」の 2 つにした（[PR #78][pr78]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 recheck と「再確認」の追記をやめ、確かめ直しは変わったものに追記して `checked` を進める形にした。決まりは「書いた本文は書き換えない。後の変化は追記で足す」（決まり 4）に縮んだ（[PR #79][pr79]。作成・マージ @MichinaoShimizu、レビューなし）

## 理由

記録あり：PR #8 の本文に、Actions のトークンでは `updateDiscussion` が "Resource not accessible by integration" で失敗するとある（PR #8 の本文。AI の印あり）。追記だけにする理由がこの失敗だけなのか、書き換えられない記録を求めたのかは、本文からは分からない。

## 分かっていないこと

- 追記だけにする方針は、トークンの制約への対処か、書き換えられない記録を求める意図が先にあったか（@MichinaoShimizu に聞く）
- PR #8 の理由は AI の印のある本文にある。人の判断と合っているか（@MichinaoShimizu に聞く）

[pr8]: https://github.com/MichinaoShimizu/decision-continuity/pull/8
[pr13]: https://github.com/MichinaoShimizu/decision-continuity/pull/13
[pr45]: https://github.com/MichinaoShimizu/decision-continuity/pull/45
[pr73]: https://github.com/MichinaoShimizu/decision-continuity/pull/73
[pr78]: https://github.com/MichinaoShimizu/decision-continuity/pull/78
[pr79]: https://github.com/MichinaoShimizu/decision-continuity/pull/79
[s22]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/SKILL.md#L22
[s38]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/SKILL.md#L38
[f36]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/references/format.md#L36
