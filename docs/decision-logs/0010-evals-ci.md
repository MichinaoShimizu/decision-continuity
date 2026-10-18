---
kind: log
category: engineering
keywords: [evals, test.yml, markdownlint, verify-docs, run.py, MD013, MD041, 評価]
checked: fbc765a
---

# [decision-continuity] 評価と CI が、旧キット向けのものから decision-log 向けに作り直された

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- C1 2026-10-15 履歴のみ：評価の固定データから `config.yaml` の写しを消した。履歴：[PR #11](https://github.com/MichinaoShimizu/decision-continuity/pull/11) ／ 現在：`config.yaml` も `adr/evals/` も基準のコミットにない（[PR #45](https://github.com/MichinaoShimizu/decision-continuity/pull/45) で削除）
- C2 2026-10-17 履歴のみ：`verify-docs.config.json` を足し、大きい SKILL.md を `references/` に分けた。履歴：[PR #35](https://github.com/MichinaoShimizu/decision-continuity/pull/35) ／ 現在：`references/` の分割は残る。`verify-docs.config.json` は PR #45 で削除された
- C3 2026-10-17 いまも同じ：markdownlint の指摘を 0 件にし、MD013 と MD041 を無効にした。履歴：[PR #36](https://github.com/MichinaoShimizu/decision-continuity/pull/36) ／ 現在：[`.markdownlint-cli2.jsonc`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/.markdownlint-cli2.jsonc)
- C4 2026-10-17 いまも同じ：評価を E01〜E07 に作り直し、CI に Python 3.10 と 3.13、リンク、frontmatter、markdownlint を足した。履歴：[PR #47](https://github.com/MichinaoShimizu/decision-continuity/pull/47) ／ 現在：[`.github/workflows/test.yml`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/.github/workflows/test.yml)、[`evals/decision-log/cases.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/evals/decision-log/cases.md)
- C5 2026-10-17 いまも同じ：評価を `evals/decision-log/` に移し、スキルとエージェントが増える前提の README にした。履歴：[PR #48](https://github.com/MichinaoShimizu/decision-continuity/pull/48) ／ 現在：[`run.py`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/evals/decision-log/run.py)
- C6 2026-10-17 いまも同じ：検査を `skills/*/SKILL.md` と `agents/` の全件に広げた。履歴：[PR #49](https://github.com/MichinaoShimizu/decision-continuity/pull/49) ／ 現在：[`tests/test_docs.py`](https://github.com/MichinaoShimizu/decision-continuity/blob/e0231f72a9bd278c99bf958a086a4cfceb148b24/tests/test_docs.py)
- C7 2026-10-17 いまも同じ：実際のエージェントで評価を回し、落ちた 2 件の原因を直し、評価の目安を最後の応答だけで取るようにした。履歴：[PR #50](https://github.com/MichinaoShimizu/decision-continuity/pull/50) ／ 現在：`run.py`

## 理由

記録あり（本文・AI）：

- C1：ルートの写しで、放っておくと内容がずれる（PR #11 本文）。
- C2：文書構造の違反を解消するため（PR #35 本文）。
- C3：日本語の段落を 1 行で書くため MD013 は折り返すと余計な空白が出る。サブエージェントの指示や断片が見出しで始まらないため MD041 を外す（PR #36 本文）。
- C4：精査で見つかった課題をまとめて直す。評価は合成の履歴で人が読んで判定する（PR #47 本文）。
- C5：スキルとエージェントを組み合わせ、今後も増やすため（PR #48 本文）。
- C6：新しいスキルが検査に入らなかった（PR #49 本文）。
- C7：照合がツールの結果まで照らしてすべて当たっていた（PR #50 本文）。

## 関わった人

PR の記録から。決めた人とは限らない。いずれも承認は見えない。

- PR #11：作成 @MichinaoShimizu、マージ @MichinaoShimizu（2026-10-15）
- PR #35・#36・#47・#48・#49・#50：作成 @MichinaoShimizu、マージ @MichinaoShimizu（いずれも 2026-10-17）。PR #50 には作成者本人の回し直しのコメントがある

## 分かっていないこと

- PR #47・#50 の本文は、判定が同じモデル系統の読みで独立ではないとする。別系統や人が読み直す予定はあるか。
- verify-docs の検査を PR #45 以降も使うか。

## 関係する記録

- DL-1、DL-4

---

## 追記 2026-10-18（Claude）

PR #53 以降の変化。評価を初めて実際のエージェント（Claude Code 2.1.302）で 8 件回し、そこで見つかったものを直した、と PR #68 の中のコミット `a98c49c` と PR #69 の本文にある。

- C8 2026-10-18 いまも同じ：合成の履歴に、理由がコードのコメントにだけある #21 と、ケース E08 を足した。履歴：[PR #67](https://github.com/MichinaoShimizu/decision-continuity/pull/67) ／ 現在：[`evals/decision-log/cases.md`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/evals/decision-log/cases.md)
- C9 2026-10-18 いまも同じ：E05 の書いたファイルを正解表（`ANSWERS`）と照らし、足りない事実を `missing_facts` に残すようにした。履歴：[PR #68](https://github.com/MichinaoShimizu/decision-continuity/pull/68) ／ 現在：[`evals/decision-log/run.py`](https://github.com/MichinaoShimizu/decision-continuity/blob/f54494031bc571248825a61557e34f3b9f75da34/evals/decision-log/run.py)
- C10 2026-10-18 いまも同じ：E07 を、最後の応答の言葉ではなく、応答の記録のサブエージェントの呼び出しで判定するようにした（`missing_agents`）。理由は記録あり（本文・AI）：reader を実際に呼んでいても、最後の応答に名前が出ないと「足りない」になっていた（PR #69 本文）。履歴：[PR #69](https://github.com/MichinaoShimizu/decision-continuity/pull/69) ／ 現在：`run.py`

## 追記 2026-10-18（Claude、再確認）

**再確認**（2026-10-18、fbc765a）
**いま**：評価は E01〜E10。キーワードは最後の応答で、書いたファイルは正解表で、サブエージェントは呼び出しで判定する。CI は Python 3.10 と 3.13、リンク、frontmatter、markdownlint。

- C4：いまも同じ → 一部置き換え済み。評価が E01〜E07 から E01〜E10 になった（[PR #67][pr67] で E08、[PR #72][pr72] で E09、[PR #73][pr73] で E10。1 日後）
- C3・C5・C6・C7・C8・C9・C10 はいまも同じ

[pr67]: https://github.com/MichinaoShimizu/decision-continuity/pull/67
[pr72]: https://github.com/MichinaoShimizu/decision-continuity/pull/72
[pr73]: https://github.com/MichinaoShimizu/decision-continuity/pull/73
