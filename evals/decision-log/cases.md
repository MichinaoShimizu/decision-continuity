# decision-log の評価のケース

[run.py](run.py) が、ケースごとに合成の履歴を持つリポジトリ（`payment-api`）を作り、スキルとサブエージェントを入れてエージェントを動かす。ネットワークには触れない。

## 合成の履歴

| PR | 件名 | 中身 | 確かめること |
|---|---|---|---|
| #12 | `Merge pull request #12 from example/fix-typo`（本文「Fix typo in README」） | README の誤字と、`TIMEOUT` 5 → 30 | 件名がブランチ名、タイトルと中身が違う |
| #13 | Bump retry count | `MAX_RETRIES` 3 → 5。本文なし | 理由が分からない |
| #14 | Lower webhook timeout to 3s | `TIMEOUT` 10 → 3。本文に理由と AI の印 | AI が書いた本文 |
| #15 | Use UUIDv7 for idempotency keys | 本文に決定の言葉と決めた人、他の案 | 決定の候補 |
| #16 | Update button padding | CSS の余白だけ | 見た目の変更 |
| #17 | Extend session | `SESSION_TTL_HOURS` 24 → 48。本文なし | 認証まわりの値の変更 |
| #18 | Keep logs longer | `retention_days` 30 → 90。本文なし | 小文字の設定 |
| #19 | Rotate webhook secret | `SECRET_NAME` を足した。本文なし | 秘密情報まわりの変更 |
| #20 | Refactor helper | 新しいファイル（`result = sum(values)`）。本文なし | ふつうのコードの変更は、差分の洗い出しに当たらない |
| #21 | Cap batch size | `BATCH_LIMIT = 100`。本文なし。理由は差分の中のコードのコメントにある | 理由が差分にだけ書かれている |
| #22 | `Merge pull request #22 from example/db-pool`（本文「Raise DB pool size」） | `POOL_SIZE` 10 → 20。理由は PR の中のコミットのメッセージにだけある | `--first-parent` では見えない理由 |

## ケース

| ID | 頼むこと | 期待 | 起きてはいけない |
|---|---|---|---|
| E01 | 全体を audit | #12 を候補に残す（タイトルではなく差分で）。理由は不明 | タイトルを見て「ふつうの修正」として落とす／理由を作る |
| E02 | `src/payment/webhook/` を audit | 理由を「記録あり（本文・AI）」とし、人の判断と合っているかの問いを足す | 人の書いた理由として扱う |
| E03 | `src/payment/idempotency.py` を audit | 報告の「決定の候補」に挙げ、Decision log の出典にする | 決定を作る／有効にする |
| E04 | `src/web/` を audit | Decision log にしない | CSS の余白を Decision log にする |
| E05 | `src/payment/http/` を `docs/decision-logs/` に write | Decision log を書き、`build_index.py` で索引を作る（`index_check` が真）。#12・#13、値の前後（3 から 5、5 から 30）、分類 reliability、理由は不明が入っている（`missing_facts` が空） | 索引を手で書く／理由を作る |
| E06 | 既存の DL-1 に口頭の答えが付いた | DL-1 に「**分かった**」の追記（答え・答えた人・「元の場所なし」）。本文は変えない（`rewritten_existing` が空） | DL-1 の本文を書き換える／決定にする |
| E07 | 全体を audit | 洗い出しを `decision-log-planner` に任せ、分類ごとに `decision-log-reader` へ分ける（応答の記録の呼び出しで数え、`missing_agents` が空） | 自分で全部を順に読む |
| E08 | `src/payment/batch.py` を audit | 理由を「記録あり（差分）」とし、コードのコメントを出典にする | 「不明」にする／PR 本文の理由として扱う |
| E09 | `src/db/pool.py` を audit | 理由を「記録あり（本文）」とし、PR の中のコミットのメッセージ（2025-03-18 の夜間バッチ）を出典にする。値の前後（10 から 20）を書く | 「不明」にする |

## 動かす

```sh
python3 -I evals/decision-log/run.py \
  --agent-version 'AGENT_AND_MODEL_VERSION' \
  --agent-argv-json '["claude","-p","--output-format","stream-json","--verbose","--allowedTools","Read","Grep","Glob","Skill","Agent","Write","Edit","Bash(git log:*)","Bash(git show:*)","Bash(git grep:*)","Bash(git rev-parse:*)","Bash(git remote get-url:*)","Bash(python3 .claude/skills/decision-log/scripts/build_index.py:*)"]' \
  --skills-loaded \
  --output /tmp/decision-log-eval
```

- `--skills-loaded` は、スキルが実際に読み込まれたことを人が確かめた、という申告。付けないと結果はすべて INCONCLUSIVE。`stream-json` で出すと、`<ID>.response.txt` に `Skill` の呼び出しが残るので、それで確かめる。
- キーワードの照合は、最後の応答（`<ID>.final.txt`）だけに対して行う。ツールの結果（読んだ手順書など）には当てない。
- `--case E03` のように一つずつ動かせる。

## 判定

ケースごとに入力・応答・標準エラーと、`manifest.json`（キーワードの照合、E05・E06 の書いたファイルの検査、E05 の正解表 `ANSWERS` との照合）を残す。どれも目安で、自動では PASS にしない。人が応答を読み、上の表で PASS / FAIL をつける。同じモデルが書いて採点するのは独立した評価ではないので、FAIL は別の人が確かめ直す。
