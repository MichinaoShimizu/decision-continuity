---
kind: log
category: release
keywords: [changes/, CHANGELOG.md, next-version.sh, release.sh, tag.yml, release-check, kiroku, plugin.json version]
---

# [decision-continuity] 版の番号を変更の断片から決め、マージでタグとリリースを出す形になった

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-17 いまも同じ：PR は `CHANGELOG.md` を直さず `changes/` に断片を足し、`tools/release.sh` が版（BREAKING → 0.x は minor、Added → minor、ほか → patch）を決めてリリースの PR を作り、マージで `tag.yml` がタグとリリースを出す形にした。`plugin.json` の `version` を CHANGELOG のいちばん上の版と揃える（テストと CI が確かめる）。履歴：[PR #55](https://github.com/MichinaoShimizu/decision-continuity/pull/55) ／ 現在：[`docs/release.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/docs/release.md)、[`.github/workflows/tag.yml`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/.github/workflows/tag.yml)
- C2 2026-10-17 いまも同じ：この形で v0.2.0・v0.3.0・v0.4.0・v0.4.1 の 4 回のリリースが出た（v0.2.0 だけ 2026-10-17、ほかは 2026-10-18）。履歴：[PR #57](https://github.com/MichinaoShimizu/decision-continuity/pull/57)、[PR #60](https://github.com/MichinaoShimizu/decision-continuity/pull/60)、[PR #64](https://github.com/MichinaoShimizu/decision-continuity/pull/64)、[PR #70](https://github.com/MichinaoShimizu/decision-continuity/pull/70) ／ 現在：[`CHANGELOG.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/CHANGELOG.md)

## 理由

記録あり（本文・AI）：kiroku の版の付け方をそのまま持ってくる。Claude Code はプラグインの `version` で更新を見分けるので、`plugin.json` の版を CHANGELOG と揃える（PR #55 本文）。ビルドする物がないので、kiroku の `release.yml` やスクリーンショットは持ってこなかった。

kiroku の形を選んだ理由（同時に開く PR の衝突を避けるためか、ほかの案と比べたか）は、本文に書かれていない。

## 関わった人

PR の記録から。決めた人とは限らない。いずれもレビューとコメントはなく、承認は見えない。

- PR #55・#57：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-17）
- PR #60・#64・#70：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-18）

## 分かっていないこと

- kiroku の形を選んだ決め手と、ほかの案（CHANGELOG を直接書く、タグを手で打つ）を比べたか（@MichinaoShimizu に聞く）。

## 関係する記録

- DL-10、DL-11
