---
kind: log
category: compatibility
keywords: [reverse-adr, decision-log, リネーム, Decision log]
checked: fbc765a
---

# [decision-continuity] スキルの名前が reverse-adr から decision-log になった

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-16 いまも同じ：`reverse-adr` を `decision-log` に改名した（スキル、テンプレート、README、評価）。`adr/` と `adr-guard` はこの時点では残した。履歴：[PR #25](https://github.com/MichinaoShimizu/decision-continuity/pull/25) ／ 現在：[`SKILL.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/skills/decision-log/SKILL.md) の name。基準のコミットで `reverse-adr` は見つからない

## 理由

記録あり（本文・AI）：スキルが書くのは Decision log であって ADR や決定ではなく、名前が逆の印象を与えていた（PR #25 本文）。

## 関わった人

PR の記録から。決めた人とは限らない。

- PR #25：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-16）。承認は見えず、レビューはない

## 分かっていないこと

- `adr/` と `adr-guard` を改名の時点で残した理由と、その後の扱い（PR #45 で削除）。

## 関係する記録

- DL-1

---

## 追記 2026-10-18（Claude、再確認）

**再確認**（2026-10-18、fbc765a）
**いま**：スキルの名前は decision-log のまま。

- C1 はいまも同じ
