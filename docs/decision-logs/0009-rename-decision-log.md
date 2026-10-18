---
category: compatibility
checked: 15e9528
---

# スキルの名前が reverse-adr から decision-log になった

**いま**：スキルの名前は `decision-log`（[SKILL.md:2][s2]）。`reverse-adr` はどこにも残っていない。

## 起きたこと

- 2026-10-16 `reverse-adr` を `decision-log` に改名した（スキル、テンプレート、README、評価）。`adr/` と `adr-guard` はこのときは残した（[PR #25][pr25]。作成・マージ @MichinaoShimizu、レビューなし）

## 理由

記録あり：スキルが書くのは Decision log で、ADR や決定ではなく、名前が逆の印象を与えていた（PR #25 の本文。AI の印あり）。

## 分かっていないこと

- `adr/` と `adr-guard` を改名のときに残した理由（どちらも PR #45 で消えた。@MichinaoShimizu に聞く）。

[pr25]: https://github.com/MichinaoShimizu/decision-continuity/pull/25
[s2]: https://github.com/MichinaoShimizu/decision-continuity/blob/15e95285ce29f297cca4ea408e8e1c21bb3d3e16/skills/decision-log/SKILL.md#L2
