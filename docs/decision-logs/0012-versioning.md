---
category: release
checked: 15e9528
---

# 版の番号を変更の断片から決め、マージでタグとリリースを出す形になった

**いま**：PR は `changes/` に断片を足し、`tools/release.sh` が版を決めてリリースの PR を作り、マージで `tag.yml` がタグとリリースを出す（[release.md:15-17][rel]、[tag.yml][tag]）。

## 起きたこと

- 2026-10-17 `CHANGELOG.md` を直さず `changes/` に断片を足す形にした。版は BREAKING なら 0.x の間は minor、Added なら minor、ほかは patch。`plugin.json` の `version` を CHANGELOG のいちばん上の版とそろえ、テストと CI が確かめる（[PR #55][pr55]）
- 2026-10-17〜18 この形で v0.2.0（[PR #57][pr57]）、v0.3.0（[PR #60][pr60]）、v0.4.0（[PR #64][pr64]）、v0.4.1（[PR #70][pr70]）、v0.5.0（[PR #75][pr75]）が出た

いずれも作成・マージ @MichinaoShimizu、レビューなし。

## 理由

記録あり：kiroku の版の付け方をそのまま持ってくる。Claude Code はプラグインの `version` で更新を見分けるので、`plugin.json` を CHANGELOG とそろえる（PR #55 の本文。AI の印あり）。

## 分かっていないこと

- kiroku の形を選んだ決め手と、ほかの案（CHANGELOG を直接書く、タグを手で打つ）と比べたか（@MichinaoShimizu に聞く）。

[pr55]: https://github.com/MichinaoShimizu/decision-continuity/pull/55
[pr57]: https://github.com/MichinaoShimizu/decision-continuity/pull/57
[pr60]: https://github.com/MichinaoShimizu/decision-continuity/pull/60
[pr64]: https://github.com/MichinaoShimizu/decision-continuity/pull/64
[pr70]: https://github.com/MichinaoShimizu/decision-continuity/pull/70
[pr75]: https://github.com/MichinaoShimizu/decision-continuity/pull/75
[rel]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/docs/release.md#L15-L17
[tag]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/.github/workflows/tag.yml#L21
