# 保守報告

作業単位: decision-records の文書群を日本語技術文書の規範で推敲する
開始: 2026-10-17T12:22:20+0900
最終更新: 2026-10-17T12:35:00+0900
開始コミット: a84d5c2fe913c3b8adb753bb115234cb047311ef

## 実行履歴

| 試行 | 実行 | スキル | 主な変更 | 最終検査 |
| ---: | --- | --- | --- | --- |
| 1 | 12:22 | 文書構造是正スキル | 軽量確認（開始時「すべて通過」） | 違反0件 |
| 2 | 12:25 | japanese-tech-writing | 第1巡: 6 文書の太字・段落の配置・事実の食い違い・用語・機構を直した | 違反0件 |
| 3 | 12:33 | 文書簡潔化スキル | 第1巡: 推敲した箇所を見直し、追加の削減なし | 違反0件 |

## 文書構造是正スキル

（軽量確認のみ）最初の検証: 12:22「文書構造: すべて通過」（21 文書）。最後の検証: 12:34「文書構造: すべて通過」（21 文書）。

## 文書重複解消スキル

（実施済み・記録なし: a84d5c2）

## 日本語技術文書の推敲（japanese-tech-writing）

開始コミット: a84d5c2fe913c3b8adb753bb115234cb047311ef
スキル: https://gist.github.com/k16shikano/fd287c3133457c4fd8f5601d34aa817d （Unlicense。リポジトリには置かない）
確認の深さ: 21 文書すべて全文。空句・翻訳調の語、二人称、イ形容詞＋です、太字の数を機械的に洗い出してから原文で判断
方針: 人向けの文書（README.md・adr/README.md・adr/guide.md・records/README.md・adr/evals/*.md）に規範を全面的に当てる。エージェント向けの SKILL.md・references・サブエージェントの指示は、命令形の簡潔な文体が目的に合うので文体は変えず、用語の一貫と事実の食い違いだけを直す

## 候補

- [x] README.md > なぜやるのか — 太字が 5 か所（規範: 一節に一、二か所） — 2026-10-17 / 箇条の見出し語 4 つの太字を外し、冒頭の主張 1 か所だけ残した
- [x] README.md > 残す意思決定 — 太字が 5 か所。「決めた人は役割と組織で書く」「記録を人の評価に使わない」の 2 段落が見出し「残さないもの」の下にあり、見出しと話題がずれている — 2026-10-17 / 表の「委譲」「合意」「上位での決定」の太字を外した（残りは「やらないと決めたこと」「役割と組織」の 2 か所）。2 段落を「残さないもの」の前（「残す意思決定」の節）へ移した
- [x] README.md > 背景 — 「反対はなく、」は誤った解釈の否定と本当の理由が一文で区別しにくい — 2026-10-17 / 「止まった理由は反対ではなく、誰の承認で決まるかが決まっていなかったことです」と、否定する解釈と本当の理由を分けた
- [x] adr/evals/scenario-tests.md — 冒頭が「16 のケース」だが表は S01〜S20 の 20 件（adr/README.md・agent-runner.md は 20） — 2026-10-17 / 表を数えて 20 件と確認し、「20 のケース」に直した
- [x] adr/evals/scenario-tests.md・adr/skills/adr-guard/SKILL.md — 記録への追記を「コメント」と書いている（正本の用語は「追記」） — 2026-10-17 / scenario-tests.md の 7 か所と adr-guard の「守ること」を「追記」に揃えた。PR のコメント・コードのコメントは別物なので変えていない
- [x] adr/guide.md > スキルと評価 — agent-runner.md（実行の手順）へのリンク名が「実行スクリプト」 — 2026-10-17 / 「実行の手順」に直した
- [x] adr/guide.md > 読めなかったとき — 「黙って進むのが一番危ないため」に機構がない — 2026-10-17 / 「黙って進むと「記録がない」と区別できず、決定とぶつかる変更を見逃すため」と機構を書いた
- [x] adr/README.md > 構成 — `references/` を「書き方」とだけ説明（分割後は分類・手順・保存と索引も入る） — 2026-10-17 / 「手順と書き方の詳細は `references/`」に直した
- [x] records/README.md > 道具 — 見出しが対象を特定しない — 2026-10-17 / 「records.py で読み書きする」に直した

### 最終検査結果

| 観点 | 検査・保証内容 | 検査根拠 | 結果 |
| --- | --- | --- | --- |
| 保護内容 | コードブロック・コードスパン・URL を同じ文書の中で減らしていない | `node scripts/check-preserved-content.mjs --base=a84d5c2 --per-file` | すべて残っている |
| 事実の一致 | ケース数を表の行数（20）と照合した | `adr/evals/scenario-tests.md` の表 | 是正済み |
| 構造 | リンク・孤立・サイズ・重複 | `node scripts/document-structure-verifier.mjs` | 違反0件 |

## 文書簡潔化スキル

実行モード: 自律圧縮

- [x] 推敲した 6 文書の変更箇所 — 2026-10-17 / 典型パターンで見直し、追加の削減なし。「止まった理由は〜ことです」は誤った解釈の否定として規範が求める形なので短くしない

### 最終検査結果

| 観点 | 検査・保証内容 | 検査根拠 | 結果 |
| --- | --- | --- | --- |
| 保護内容 | 開始時のコードブロック・コードスパン・URL が同じ文書に残っている | `node scripts/check-preserved-content.mjs --base=a84d5c2 --per-file` | すべて残っている |
| 意味変更リスク | 変更箇所ごとのリスク | 上の推敲の記録 | 簡潔化による変更なし |
| Markdown表現 | リンク・表の成立 | `node scripts/document-structure-verifier.mjs` | 通過 |

### ファイル別サイズ

| ファイル | 開始時点 | 最終 | 削減バイト数 | 開始時点からの削減率 |
| --- | ---: | ---: | ---: | ---: |
| [adr/evals/scenario-tests.md](../../adr/evals/scenario-tests.md) | 6,342B | 6,303B | 39B | 0.6% |
| [adr/skills/adr-guard/SKILL.md](../../adr/skills/adr-guard/SKILL.md) | 6,480B | 6,474B | 6B | 0.1% |
| [README.md](../../README.md) | 6,994B | 6,990B | 4B | 0.1% |
| [adr/README.md](../../adr/README.md) | 5,045B | 5,063B | -18B | -0.4% |
| [records/README.md](../../records/README.md) | 4,856B | 4,882B | -26B | -0.5% |
| [adr/guide.md](../../adr/guide.md) | 3,997B | 4,054B | -57B | -1.4% |
| 変更なし（15 文書、合計 54,403 バイト） | | | 0B | 0.0% |
| 合計（21 文書） | 88,117B | 88,169B | -52B | -0.1% |

変更のなかった文書: .claude/skills/decision-record/SKILL.md、.claude/skills/decision-record/references/amend.md、.claude/skills/decision-record/references/capture-and-write.md、.claude/skills/decision-record/references/record-format.md、.claude/skills/decision-record/references/store.md、.kiro/skills/decision-record/SKILL.md、adr/agents/claude/decision-log-reader.md、adr/evals/agent-runner.md、adr/skills/decision-continuity-contract.md、adr/skills/decision-log/SKILL.md、adr/skills/decision-log/references/categories.md、adr/skills/decision-log/references/investigation.md、adr/skills/decision-log/references/save.md、adr/skills/decision-log/references/writing.md、adr/templates/agent-instructions.md

### その他の検査

- `python3 -I -m unittest discover -s adr/evals -p 'test_agent_eval.py'` → OK
