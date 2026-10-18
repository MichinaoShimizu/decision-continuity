# decision-continuity

Claude Code と Kiro のスキル（`skills/`）とサブエージェント（`agents/`）を配るリポジトリ。

## 確かめるコマンド

- テスト：`python3 -m unittest discover -s tests`
- 文書：`npx --yes markdownlint-cli2@0.18.1 "**/*.md"`
- Decision log：`python3 skills/decision-log/scripts/build_index.py docs/decision-logs --check`
- 実際のエージェントでの評価：`evals/decision-log/cases.md`

## 決まり

- `agents/kiro/` の `.md` と `.json` は、`agents/claude/` の同じ名前の本文と同じにする（テストが確かめる）。
- 利用者に見える変更は `changes/` に断片を足す。`CHANGELOG.md` は直さない（`docs/release.md`）。

## 判断の照合と記録

- 値・境界・方針など振る舞いを変える前に、decision-log の check で docs/decision-logs/ を照合する。
- Active の判断と食い違うときは、進める前に人に確かめる。理由が「不明」の判断は、知っていそうな人に聞く。
- 人が判断を決めたら、decision-log の record で、変更と同じ PR に記録を足す。
