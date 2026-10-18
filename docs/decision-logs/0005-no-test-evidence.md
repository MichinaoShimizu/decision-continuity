---
category: product
checked: 15e9528
---

# CI の結果をテスト証拠に数えたが、約 40 分後にテストの確認自体をやめた

**いま**：テストの成否を調べる指示はない。読み手が読むのは PR、コミットのメッセージ、参照された issue、差分と基準のコミットの姿である（[decision-log-reader.md:11-15][r11]）。

## 起きたこと

- 2026-10-16 CI の成功も、条件を満たせばテスト証拠として数えるようにした（「テストの証拠」節、`headRefOid`・`statusCheckRollup` の取得）（[PR #20][pr20]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-16 テストの確認をやめ、PR #20 を取り消した。状態は 6 つから 4 つ（いまも同じ／置き換え済み／競合／履歴のみ）に、証拠は履歴と現在の 2 種類になった（[PR #22][pr22]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 状態に「一部置き換え済み」を足し、4 つから 5 つにした（[PR #68][pr68]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 状態を 5 つから 3 つ（いまも同じ／置き換え済み／履歴のみ）にした。競合は状態にせず、分かっていないことと報告の先頭に書く（[PR #78][pr78]。作成・マージ @MichinaoShimizu、レビューなし）
- 2026-10-18 起きたことの行から状態の語と「履歴：／現在：」をやめ、「テストの成否は調べない」と書いていた investigation.md もなくした（[PR #79][pr79]。作成・マージ @MichinaoShimizu、レビューなし）

## 理由

記録あり：テスト証拠の確認は最も重く、Decision log の役目（何が起き、なぜか）に比べて効果が小さい（PR #22 の本文。「This reverses #20.」とある。AI の印あり）

- PR #20：自分で走らせたテストしか数えず、CI で試験済みでも未検証のままだった（PR #20 の本文。AI の印あり）
- PR #78・#79：決まりと指示が増えすぎて、書くモデルにも読む人にも重くなっていたので、精度に効かない部分を削った（PR #78・#79 の本文。AI の印あり）

## 分かっていないこと

- PR #20 を入れて約 40 分後に PR #22 で外した間に、何が分かったか（@MichinaoShimizu に聞く）
- テスト確認を戻す条件はあるか（@MichinaoShimizu に聞く）
- PR #20・#22 の本文（AI の印あり）の理由は、@MichinaoShimizu の判断と合っているか

[pr20]: https://github.com/MichinaoShimizu/decision-continuity/pull/20
[pr22]: https://github.com/MichinaoShimizu/decision-continuity/pull/22
[pr68]: https://github.com/MichinaoShimizu/decision-continuity/pull/68
[pr78]: https://github.com/MichinaoShimizu/decision-continuity/pull/78
[pr79]: https://github.com/MichinaoShimizu/decision-continuity/pull/79
[r11]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/agents/claude/decision-log-reader.md#L11-L15
