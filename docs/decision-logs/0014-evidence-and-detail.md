---
kind: log
category: product
keywords: [pulls/comments, 行のコメント, 記録あり（差分）, Documented (diff), 一部置き換え済み, 値の前後, claim_problems, --check]
---

# [decision-continuity] 理由の証拠を広く読み、起きたことに値の前後や置き換えまでの日数を書く形になった

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-18 いまも同じ：reader が、行に付いたレビューのコメント（`pulls/<N>/comments`）、PR の中のコミットのメッセージ、本文・コメント・コミットから参照された issue とそのコメント（1 段だけ）を読むようにした。差分の中のコードのコメントや CHANGELOG を出典にする「記録あり（差分）」を足した。`gh` で読めない外部のリンクは開かず、「元の場所」に未読として挙げる。履歴：[PR #67](https://github.com/MichinaoShimizu/decision-continuity/pull/67) ／ 現在：[`agents/claude/decision-log-reader.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/agents/claude/decision-log-reader.md)
- C2 2026-10-18 いまも同じ：「起きたこと」に、値の前後（`3 から 5`）、同じ変更でテストやドキュメントが変わったか、置き換わったものは何日後かを書くことにした。状態に「一部置き換え済み」を足した（DL-7 ですでに使われていた）。履歴：[PR #68](https://github.com/MichinaoShimizu/decision-continuity/pull/68) ／ 現在：[`skills/decision-log/references/writing.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/skills/decision-log/references/writing.md)
- C3 2026-10-18 いまも同じ：`build_index.py --check` が「起きたこと」の各行（状態の語、「履歴：」と「現在：」の両方、C の番号の重なり）を確かめるようにした。この時点の既存の 10 件はすべて通った。履歴：[PR #68](https://github.com/MichinaoShimizu/decision-continuity/pull/68) ／ 現在：[`skills/decision-log/scripts/build_index.py`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/skills/decision-log/scripts/build_index.py)

## 理由

記録あり（本文・AI）：

- C1：このリポジトリの Decision log 10 件を読み直すと、理由はほぼ PR の本文からしか取れていなかった。行のコメントは `gh pr view --json reviews,comments` に入らず、`--first-parent` ではマージコミットしか見ない（PR #67 本文）。
- C2・C3：出力の情報を増やし、崩れを機械で捕まえ、精度を数字で追えるようにする（PR #68 本文）。

## 関わった人

PR の記録から。決めた人とは限らない。いずれもレビューとコメントはなく、承認は見えない。

- PR #67・#68：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-18）

## 分かっていないこと

- C1 の読み取り（行のコメント、参照された issue）は、評価の合成リポジトリでは `gh` が使えないので試されていない。実際のリポジトリで理由の取れる割合は上がったか。
- 「記録あり（差分）」のコードのコメントは、コメントだけ古いまま残ることがある。現在のコードと食い違うときの扱いは決まっていない。

## 関係する記録

- DL-6、DL-7、DL-8、DL-15

---

## 追記 2026-10-18（Claude、再確認）

**再確認**（2026-10-18、fbc765a）
**いま**：reader は行のコメント、PR の中のコミット、参照された issue も読む。「起きたこと」には値の前後と置き換えまでの日数を書く。

- C1・C2・C3 はいまも同じ（writing.md と build_index.py は [PR #73][pr73] で変わったが、ここに書いた決まりと検査は残っている）

[pr73]: https://github.com/MichinaoShimizu/decision-continuity/pull/73
