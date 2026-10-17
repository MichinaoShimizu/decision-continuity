---
kind: log
category: product
keywords: [statusCheckRollup, headRefOid, テストの証拠, 検証済み, 未検証, 根拠なし]
---

# [decision-continuity] CI の結果をテスト証拠に数えたが、約 40 分後にテストの確認自体をやめた

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-16 置き換え済み：CI の成功も、条件を満たせばテスト証拠として数えるようにした（「テストの証拠」節、`headRefOid`・`statusCheckRollup` の取得）。履歴：[PR #20](https://github.com/MichinaoShimizu/decision-continuity/pull/20) ／ 現在：[PR #22](https://github.com/MichinaoShimizu/decision-continuity/pull/22) が取り消した。基準のコミットに `statusCheckRollup` はない
- C2 2026-10-16 いまも同じ：テストの確認をやめた。状態は 6 つから 4 つ（いまも同じ／置き換え済み／競合／履歴のみ）になり、証拠は履歴と現在の 2 種類になった。履歴：[PR #22](https://github.com/MichinaoShimizu/decision-continuity/pull/22) ／ 現在：[`investigation.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/references/investigation.md) に「テストの成否は調べない」と 4 状態の表がある

## 理由

記録あり（本文・AI）：PR #22 の本文に「This reverses #20.」とあり、テスト証拠の確認は最も重く、Decision log の役目（何が起き、なぜか）に比べて効果が小さい、とある。PR #20 の本文は、自分で走らせたテストしか数えず、CI で試験済みでも未検証のままだったことを挙げる。

## 関わった人

PR の記録から。決めた人とは限らない。いずれも承認は見えず、レビューはない。

- PR #20：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-16）
- PR #22：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-16）

## 分かっていないこと

- PR #20 を入れて約 40 分後に PR #22 で外した間に、何が分かったか。
- テスト確認を戻す条件はあるか。

## 関係する記録

- DL-7
