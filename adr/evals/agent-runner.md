# ケースを実際のエージェントで動かす

[agent_eval.py](agent_eval.py) は、[19 のケース](scenario-tests.md) を、ケースごとに新しい作業フォルダーと新しいプロセスで動かす。エージェントも、その認証も同梱しない。動かすのは手元の CLI。

## 動かす

```sh
python3 -I adr/evals/agent_eval.py \
  --revision "$(git rev-parse HEAD)" \
  --checkout . --install-kit \
  --agent-version 'AGENT_AND_MODEL_VERSION' \
  --agent-argv-json '["claude","-p","--allowedTools","Read","Grep","Glob","Skill","Bash(python3 .claude/skills/decision-record/records.py:*)","--disallowedTools","Edit","Write","WebFetch","WebSearch"]' \
  --skills-loaded \
  --output /tmp/decision-continuity-results
```

- `--checkout . --install-kit`：指定したコミットのこのリポジトリから、[README の入れ方](../README.md#入れ方) のとおりにキットを空のリポジトリに入れる（`.claude/skills/` と `CLAUDE.md`）。ケースのリポジトリ名（`payment-api` など）が `CLAUDE.md` に入る。
- 記録は `DR_SNAPSHOT` で [fixtures/records.json](fixtures/records.json) を指す。`records.py` はそれを読み、書き込みはしない。S08 だけは存在しないファイルを指し、「読めなかった」を確かめる。
- `--skills-loaded` は、スキルが実際に読み込まれたことを人が確かめた、という申告。確かめられないときは付けない。付けないと結果はすべて INCONCLUSIVE。
- `--case S03` のように一つずつ動かせる。

## 結果

ケースごとに、入力・応答・標準エラーと、`manifest.json`（コミット、エージェント、キーワード照合の目安）を書き出す。成功した実行は REVIEW_REQUIRED、失敗や申告なしは INCONCLUSIVE。PASS / FAIL は人が [ケースの表](scenario-tests.md) と照らしてつける。

作業フォルダーの分離はプロセスの単位だけ。CLI が自分のメモリや認証を読むなら、完全には分離されていない。本番に書き込める権限のないアカウントで動かす。秘密情報や個人情報を含む応答を外に出さない。
