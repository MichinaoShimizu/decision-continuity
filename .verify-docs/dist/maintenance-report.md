# 保守報告

作業単位: decision-records の文書群（Decision log まわりを含む）の構造是正・重複解消・簡潔化
開始: 2026-10-17T11:46:38+0900
最終更新: 2026-10-17T11:55:00+0900
開始コミット: de897314c1b52c47a7012a2853d6cd26e8228e11

## 実行履歴

| 試行 | 実行 | スキル | 主な変更 | 最終検査 |
| ---: | --- | --- | --- | --- |
| 1 | 11:46 | 文書構造是正スキル | 設定ファイルを追加（`pathRoots` 限定、Kiro 用複製を除外）、孤立 2 件をリンク、サイズ超過 3 文書を references/ へ分割 | `--baseline` 通過（サイズ超過 2 件は基準にあった違反として次工程へ） |
| 2 | 11:49 | 文書重複解消スキル | 第1巡: adr/README.md の「考え方」を adr/guide.md へ統合しポインタ化。ほか 6 候補を保護対象として記録 | `--baseline` 通過 |
| 3 | 11:50 | 文書簡潔化スキル | 第1巡: README.md・adr/skills/decision-log/SKILL.md・adr/README.md を圧縮 | 違反 0 件 |
| 4 | 11:51 | 文書重複解消スキル・文書簡潔化スキル | 第2巡: 候補一覧が第1巡と同じで変更なし（収束） | 違反 0 件 |

## 文書構造是正スキル

開始コミット: de897314c1b52c47a7012a2853d6cd26e8228e11
基準: `.verify-docs/dist/baseline.work.json`（開始時 36 件: 重複 9・孤立 6・パス参照 17・サイズ超過 4）
検証器: verify-docs リポジトリの `scripts/document-structure-verifier.mjs` を `--root=.` で実行（本リポジトリには未配置）
確認の深さ: 18 文書すべて全文（100 文書未満のため読解単位は 1）

## パス参照（導入先リポジトリのパスを指すもの）

対応: [verify-docs.config.json](../../verify-docs.config.json) の `pathRoots` を本リポジトリに実在するパスの接頭辞（`.claude/skills/decision-record/`・`.kiro/skills/decision-record/`・`.github/`・`adr/`・`records/`）に限定。下の各項目は ADR キットの導入先リポジトリ（または例示）のパスで、本リポジトリで解決すべきものではない。

- [x] [adr/README.md](../../adr/README.md) > ADR キット > 構成・入れ方 — `scripts/`×2、`.claude/agents/`、`.kiro/agents/`、`.claude/skills/decision-log/`、`.kiro/skills/decision-log/`、`docs/decision-logs/` — 2026-10-17 / 導入先・例示のパス。`pathRoots` の限定で検査対象外
- [x] [adr/evals/scenario-tests.md](../../adr/evals/scenario-tests.md) > ケース — `src/payment/http/`×2、`docs/decision-logs/` — 2026-10-17 / 導入先・例示のパス。`pathRoots` の限定で検査対象外
- [x] [adr/skills/decision-log/SKILL.md](../../adr/skills/decision-log/SKILL.md) > 記録の置き場所・手順 — `docs/decision-logs/`、`.kiro/agents/`、`.claude/agents/` — 2026-10-17 / 導入先・例示のパス。`pathRoots` の限定で検査対象外
- [x] [adr/templates/agent-instructions.md](../../adr/templates/agent-instructions.md) — `.claude/skills/adr-guard/SKILL.md`、`.claude/skills/decision-log/SKILL.md` — 2026-10-17 / 導入先・例示のパス。`pathRoots` の限定で検査対象外
- [x] [adr/templates/kiro/adr-guard/SKILL.md](../../adr/templates/kiro/adr-guard/SKILL.md) — `.claude/skills/adr-guard/SKILL.md` — 2026-10-17 / 導入先・例示のパス。`pathRoots` の限定で検査対象外
- [x] [adr/templates/kiro/decision-log/SKILL.md](../../adr/templates/kiro/decision-log/SKILL.md) — `.claude/skills/decision-log/SKILL.md` — 2026-10-17 / 導入先・例示のパス。`pathRoots` の限定で検査対象外

## 孤立

- [x] [adr/agents/claude/decision-log-reader.md](../../adr/agents/claude/decision-log-reader.md) — 2026-10-17 / [adr/README.md](../../adr/README.md) の構成表からリンク
- [x] [adr/agents/kiro/decision-log-reader.md](../../adr/agents/kiro/decision-log-reader.md) — 2026-10-17 / `excludePaths` で検査対象外（Kiro 用の複製）。[adr/README.md](../../adr/README.md) の構成表からもリンク
- [x] [adr/templates/agent-instructions.md](../../adr/templates/agent-instructions.md) — 2026-10-17 / [adr/README.md](../../adr/README.md) の構成表からリンク
- [x] [adr/templates/kiro/adr-guard/SKILL.md](../../adr/templates/kiro/adr-guard/SKILL.md) — 2026-10-17 / `excludePaths` で検査対象外（Kiro 用の複製）。[adr/README.md](../../adr/README.md) の構成表からもリンク
- [x] [adr/templates/kiro/decision-log/SKILL.md](../../adr/templates/kiro/decision-log/SKILL.md) — 2026-10-17 / `excludePaths` で検査対象外（Kiro 用の複製）。[adr/README.md](../../adr/README.md) の構成表からもリンク
- [x] [adr/templates/kiro/decision-record/SKILL.md](../../adr/templates/kiro/decision-record/SKILL.md) — 2026-10-17 / `excludePaths` で検査対象外（Kiro 用の複製）。[adr/README.md](../../adr/README.md) の構成表からもリンク

## 重複

- [x] [.kiro/skills/decision-record/SKILL.md](../../.kiro/skills/decision-record/SKILL.md) > decision-record（8行目） ↔ [adr/templates/kiro/decision-record/SKILL.md](../../adr/templates/kiro/decision-record/SKILL.md) — 2026-10-17 / Kiro 用の複製。`adr/templates/kiro/`・`adr/agents/kiro/` を `excludePaths` に追加。正本との一致は [adr/evals/test_agent_eval.py](../../adr/evals/test_agent_eval.py) の KiroTemplateTests・ReaderAgentTests が検査する
- [x] [adr/agents/claude/decision-log-reader.md](../../adr/agents/claude/decision-log-reader.md)（7・15・16・17・21・22・23・28行目の 8 段落） ↔ [adr/agents/kiro/decision-log-reader.md](../../adr/agents/kiro/decision-log-reader.md) — 2026-10-17 / Kiro 用の複製。`adr/templates/kiro/`・`adr/agents/kiro/` を `excludePaths` に追加。正本との一致は [adr/evals/test_agent_eval.py](../../adr/evals/test_agent_eval.py) の KiroTemplateTests・ReaderAgentTests が検査する

## サイズ超過

- [x] [.claude/skills/decision-record/SKILL.md](../../.claude/skills/decision-record/SKILL.md) — 21620 バイト — 2026-10-17 / 見出し単位で references/ の [capture-and-write.md](../../.claude/skills/decision-record/references/capture-and-write.md)・[amend.md](../../.claude/skills/decision-record/references/amend.md)・[store.md](../../.claude/skills/decision-record/references/store.md)・[record-format.md](../../.claude/skills/decision-record/references/record-format.md) へ移動し、SKILL.md に「読むもの」表を置いた → 5288 バイト
- [x] [adr/skills/decision-log/SKILL.md](../../adr/skills/decision-log/SKILL.md) — 13890 バイト — 2026-10-17 / 分類を [categories.md](../../adr/skills/decision-log/references/categories.md)、手順 0〜3 を [investigation.md](../../adr/skills/decision-log/references/investigation.md)、手順 4 を [save.md](../../adr/skills/decision-log/references/save.md) へ移動 → 7236 バイト。残り 236 バイトは tighten-docs へ引き継ぎ（基準にある違反）
- [x] [adr/skills/decision-log/references/writing.md](../../adr/skills/decision-log/references/writing.md) — 7926 バイト — 2026-10-17 / 「索引」節を [save.md](../../adr/skills/decision-log/references/save.md) へ移動 → 6582 バイト
- [x] [README.md](../../README.md) — 7219 バイト — 2026-10-17 / 219 バイト超過。分割せず tighten-docs へ引き継ぎ（基準にある違反）

### 最終検査結果

実行: 2026-10-17T11:51+0900 `node scripts/document-structure-verifier.mjs --root=.`（verify-docs リポジトリの検証器）→「文書構造: すべて通過」（文書 21 件）

| 観点 | 検査・保証内容 | 検査根拠 | 結果 |
| --- | --- | --- | --- |
| 参照整合性 | Markdownリンク・断片リンク、`pathRoots` に一致するバッククォート内のパスが解決できる | `node scripts/document-structure-verifier.mjs` | リンク違反0件 |
| 孤立文書 | 入口文書または他の検査対象文書から到達できる | `node scripts/document-structure-verifier.mjs` | 孤立違反0件 |
| 文書サイズ | `maxDocBytes`（7000）以下。文書サイズ例外なし | `node scripts/document-structure-verifier.mjs` | サイズ違反0件 |
| 機械的重複 | 完全一致の段落重複を検出・是正済みである | `node scripts/document-structure-verifier.mjs` | 重複違反0件 |

基準にあった違反: 36 件（重複 9・孤立 6・パス参照 17・サイズ超過 4）。完了時に残った違反: 0 件。

## 文書重複解消スキル

実行モード: 自律正本化
開始コミット: de897314c1b52c47a7012a2853d6cd26e8228e11（verify-docs の基準を共用）
確認の深さ: 検査対象 21 文書すべて全文。`document-structure-extractor.mjs --format=pairs` の候補 10 組も原文で照合
対象外: `adr/templates/kiro/`・`adr/agents/kiro/`（`excludePaths`。Kiro 用の複製）

## 機械的重複

- [x] verify-docs 工程の後、`[重複]`・`[準一致重複]` なし — 2026-10-17

## 候補

- [x] [adr/README.md](../../adr/README.md) > 考え方 ↔ [adr/guide.md](../../adr/guide.md) > 記録の種類・探し方 — Decision log と DR の比較表、「マージされた PR は…証拠ではない」、「索引のファイルは持たない」が重複 — 2026-10-17 / 統合。正本は [adr/guide.md](../../adr/guide.md)（詳しい側）。README の比較表・箇条を 1 段落の定義とポインタに置換し、README だけにあった「フォルダー」行を guide の表へ、「分からない理由は Unknown のまま残し、後から理由を作らない」を guide の記録の種類へ移した。「状態は 3 つ」の表し方は [decision-record の SKILL.md](../../.claude/skills/decision-record/SKILL.md) の「状態」と guide の探し方の表にある。リスク: README だけを読む人は状態の表し方を guide か decision-record で読む必要がある
- [x] [adr/agents/claude/decision-log-reader.md](../../adr/agents/claude/decision-log-reader.md) > 読み方・返す形 ↔ [adr/skills/decision-log/SKILL.md](../../adr/skills/decision-log/SKILL.md) > 守ること 2・4 ／ [references/investigation.md](../../adr/skills/decision-log/references/investigation.md) > 1（`gh pr view`・`git show --stat`） — 2026-10-17 / 保護対象。サブエージェントは別の文脈で動き、スキル本体を読まない前提の自己完結した指示。Kiro 版と同一であることを test_agent_eval.py が検査する
- [x] [adr/skills/decision-continuity-contract.md](../../adr/skills/decision-continuity-contract.md) > 決まり 1 ↔ [adr/skills/decision-log/SKILL.md](../../adr/skills/decision-log/SKILL.md) > 守ること 1 — 2026-10-17 / 保護対象。decision-log は「このフォルダーだけで、どのリポジトリでも動く」配布単位で、共通の決まりの文書は同梱されない。共通規則と運用手順で層も違う
- [x] [adr/skills/adr-guard/SKILL.md](../../adr/skills/adr-guard/SKILL.md) > いつ使うか ↔ [adr/templates/agent-instructions.md](../../adr/templates/agent-instructions.md) — 2026-10-17 / 保護対象。agent-instructions.md は導入先の `CLAUDE.md` に写す指示で、スキルを読む前に判断に使う。層が違う
- [x] [.claude/skills/decision-record/references/store.md](../../.claude/skills/decision-record/references/store.md) > 番号・番号の書き方 ↔ [records/README.md](../../records/README.md) > ファイル ／ [adr/skills/decision-log/references/writing.md](../../adr/skills/decision-log/references/writing.md) > ファイルの形 — 2026-10-17 / 保護対象。records/README.md は人が PR で直接書くためのガイド、store.md はエージェント用の参照、writing.md は単独配布の decision-log 用。読者と配布単位が違う
- [x] [adr/guide.md](../../adr/guide.md) > 読めなかったとき・限界 ↔ [adr/skills/decision-continuity-contract.md](../../adr/skills/decision-continuity-contract.md) > 決まり 3・4 ↔ [adr/skills/adr-guard/SKILL.md](../../adr/skills/adr-guard/SKILL.md) > 手順 1 — 2026-10-17 / 保護対象。guide は人向けの説明、contract は共通規則、adr-guard は手順。層が違い、いずれも 1〜2 文
- [x] [records/README.md](../../records/README.md) > 追記だけで育てる（印の表・状態図） ↔ [.claude/skills/decision-record/references/amend.md](../../.claude/skills/decision-record/references/amend.md) ／ [adr/skills/decision-log/references/writing.md](../../adr/skills/decision-log/references/writing.md) > 追記の印 — 2026-10-17 / 保護対象。records/README.md は人向けの一覧と図、各スキルは書き方の手順。層が違う

## 保護内容の照合

- [x] `node check-preserved-content.mjs --root=. --base=de89731` — 2026-10-17 / コードブロック 1 件（[.claude/skills/decision-record/SKILL.md](../../.claude/skills/decision-record/SKILL.md) 旧 159 行目「本文の書き方」の例）を報告。移動先 [record-format.md](../../.claude/skills/decision-record/references/record-format.md) 7〜28 行目に一字一句残っていることを diff で確認。照合器が移動先の文書で最初に現れる `---` 〜 `---` をフロントマターとして除くための誤検知

### 最終検査結果

実行: 2026-10-17T11:51+0900

| 観点 | 検査・保証内容 | 検査根拠 | 結果 |
| --- | --- | --- | --- |
| 意味的重複 | 言い換えによる同一の主張・手順・判断基準を確認した | 原文と `--format=pairs` の照合 | 1 組を統合、6 組を保護対象 |
| 正本の配置 | 統合対象は詳細度と読者に合う文書を正本にした | 正本と統合元の原文 | 是正済み（正本 adr/guide.md） |
| ポインタ | 統合元から正本への案内が解決でき、内容を重ねていない | `node scripts/document-structure-verifier.mjs` | リンク違反0件 |
| 保護内容 | 正本へ移したつもりで失われたコードブロック・コードスパン・URL がない | `node scripts/check-preserved-content.mjs --base=de89731` | 1 件報告、誤検知（上記） |

作成した文書: なし（dedupe-docs 工程）。削除した文書: なし。

## 文書簡潔化スキル

実行モード: 自律圧縮
確認の深さ: 21 文書すべて全文。典型パターン（語句・文法、重複・文体、Markdown表現、文書単位の冗長性）で一巡し、第2巡で追加の変更なし

### 変更箇所と意味変更リスク

- [x] [README.md](../../README.md) — 2026-10-17 / 冗長な語句（「そのうえで、残っていることで」「次の別の」「〜になっていきます」「〜ことがありました」「これまで」「〜するためには」など）を削り、「構成」の「書き方は records/README.md」を削除（同じリンクを「使い方」の直接書く案内で残す）。リスク: 背景の事例文を「止まりました／反対はなく」と短くし、語感がやや断定的になった
- [x] [adr/skills/decision-log/SKILL.md](../../adr/skills/decision-log/SKILL.md) — 2026-10-17 / 冒頭の「書くときだけ writing.md と save.md を読む」を削除（同じ案内を実行時点の「4. 書く」に残す。重複する参照案内）。ほか 3 文を短縮。リスク: 冒頭だけ読む読者は writing.md の中身の一覧（形、例、書き方、追記の印）を見なくなる
- [x] [adr/README.md](../../adr/README.md) — 2026-10-17 / 入れ方 1 の「（正本を指すだけの薄いファイルなので、中身を二重に持たない）」を削除（同じ説明が構成表の `templates/kiro/` 行にある。同一理由の重複）
- [x] 上記以外の 18 文書 — 2026-10-17 / 過去の PR（#21・#24 など）で簡潔化済みで、該当パターンなし。変更なし

### 変更しなかった保護対象

- コードブロック（Mermaid 図、`records.py` の例、フロントマターの型、索引の例）とコマンド、数値（7000、depth 20、終了コード 2、9 時間など）、設定値
- サブエージェントの指示（[adr/agents/claude/decision-log-reader.md](../../adr/agents/claude/decision-log-reader.md)）は Kiro 版との一致をテストが検査するため変更しない

### 最終検査結果

実行: 2026-10-17T11:51+0900

| 観点 | 検査・保証内容 | 検査根拠 | 結果 |
| --- | --- | --- | --- |
| 保護内容 | tighten で変更した 3 文書でコードブロック・コードスパン・URL を減らしていない | `node scripts/check-preserved-content.mjs --base=de89731 --per-file` と変更箇所の原文照合 | 通過（報告 171 件は verify-docs・dedupe-docs 工程で references/ と adr/guide.md へ移した内容。tighten では decision-log の SKILL.md から重複した案内文の `write` 1 件を削除） |
| 意味変更リスク | 変更箇所ごとのリスクを記録した | 上記「変更箇所と意味変更リスク」 | 記録済み |
| 重複と文体 | 同一理由の反復、重複する参照案内を確認した | 典型パターンと原文 | 是正済み |
| Markdown表現 | リンク・表・コードブロックの成立 | `node scripts/document-structure-verifier.mjs` | 通過 |

### ファイル別サイズ

開始時点は dedupe-docs の開始前（verify-docs 工程の分割後）のサイズ。

| ファイル | 開始時点 | 最終 | 削減バイト数 | 開始時点からの削減率 |
| --- | ---: | ---: | ---: | ---: |
| [adr/README.md](../../adr/README.md) | 5,889B | 5,045B | 844B | 14.3% |
| [adr/skills/decision-log/SKILL.md](../../adr/skills/decision-log/SKILL.md) | 7,236B | 6,979B | 257B | 3.6% |
| [README.md](../../README.md) | 7,219B | 6,994B | 225B | 3.1% |
| [.claude/skills/decision-record/SKILL.md](../../.claude/skills/decision-record/SKILL.md) | 5,288B | 5,288B | 0B | 0.0% |
| [.claude/skills/decision-record/references/amend.md](../../.claude/skills/decision-record/references/amend.md) | 3,159B | 3,159B | 0B | 0.0% |
| [.claude/skills/decision-record/references/capture-and-write.md](../../.claude/skills/decision-record/references/capture-and-write.md) | 5,617B | 5,617B | 0B | 0.0% |
| [.claude/skills/decision-record/references/record-format.md](../../.claude/skills/decision-record/references/record-format.md) | 3,578B | 3,578B | 0B | 0.0% |
| [.claude/skills/decision-record/references/store.md](../../.claude/skills/decision-record/references/store.md) | 4,812B | 4,812B | 0B | 0.0% |
| [.kiro/skills/decision-record/SKILL.md](../../.kiro/skills/decision-record/SKILL.md) | 767B | 767B | 0B | 0.0% |
| [adr/agents/claude/decision-log-reader.md](../../adr/agents/claude/decision-log-reader.md) | 3,232B | 3,232B | 0B | 0.0% |
| [adr/evals/agent-runner.md](../../adr/evals/agent-runner.md) | 2,224B | 2,224B | 0B | 0.0% |
| [adr/evals/scenario-tests.md](../../adr/evals/scenario-tests.md) | 6,342B | 6,342B | 0B | 0.0% |
| [adr/skills/adr-guard/SKILL.md](../../adr/skills/adr-guard/SKILL.md) | 6,480B | 6,480B | 0B | 0.0% |
| [adr/skills/decision-continuity-contract.md](../../adr/skills/decision-continuity-contract.md) | 2,517B | 2,517B | 0B | 0.0% |
| [adr/skills/decision-log/references/categories.md](../../adr/skills/decision-log/references/categories.md) | 1,051B | 1,051B | 0B | 0.0% |
| [adr/skills/decision-log/references/investigation.md](../../adr/skills/decision-log/references/investigation.md) | 4,846B | 4,846B | 0B | 0.0% |
| [adr/skills/decision-log/references/save.md](../../adr/skills/decision-log/references/save.md) | 2,672B | 2,672B | 0B | 0.0% |
| [adr/skills/decision-log/references/writing.md](../../adr/skills/decision-log/references/writing.md) | 6,582B | 6,582B | 0B | 0.0% |
| [adr/templates/agent-instructions.md](../../adr/templates/agent-instructions.md) | 1,079B | 1,079B | 0B | 0.0% |
| [records/README.md](../../records/README.md) | 4,856B | 4,856B | 0B | 0.0% |
| [adr/guide.md](../../adr/guide.md) | 3,815B | 3,997B | -182B | -4.8% |
| 合計（21 文書） | 89,261B | 88,117B | 1,144B | 1.3% |

### その他の検査

- `python3 -I -m unittest discover -s adr/evals -p 'test_agent_eval.py'` → 11 件 OK
- `python3 -I .claude/skills/decision-record/records.py check` → 問題なし
