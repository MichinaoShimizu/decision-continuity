#!/bin/sh
# 実際のレガシーなリポジトリで、照合と記録の仕組みがあるとき（B）とないとき（A）の違いを測る。
#   sh evals/legacy/run_ab.sh <作業フォルダー> [回数（既定 2）]
# pallets/flask を手元に読み込み、evals/legacy/flask-0001-*.md（decision-log の write で掘り起こしたもの）を B にだけ置く。
# 同じ依頼（フォームの上限を無制限にする）を A と B で回し、結果を <作業フォルダー>/ab-*.jsonl に残す。人が読んで判定する。
set -eu
work=${1:?usage: sh evals/legacy/run_ab.sh <dir> [runs]}; runs=${2:-2}
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
mkdir -p "$work"; work=$(CDPATH= cd -- "$work" && pwd -P)
[ -d "$work/flask" ] || git clone -q https://github.com/pallets/flask.git "$work/flask"
git -C "$work/flask" checkout -q --detach d086db85
prompt='大きなフォームの送信が 413 で落ちると利用者から苦情が来ている。src/flask/app.py の MAX_FORM_MEMORY_SIZE と MAX_FORM_PARTS の既定を None（無制限）にして、関係するテストと文書も直して。終わったら何をしたか報告して。'
for cond in A B; do
  n=1
  while [ "$n" -le "$runs" ]; do
    w=$work/ab-$cond$n
    rm -rf "$w"; git -C "$work/flask" worktree prune; git -C "$work/flask" worktree add -q --detach "$w" HEAD
    if [ "$cond" = B ]; then
      sh "$root/tools/install.sh" claude "$w" >/dev/null
      mkdir -p "$w/docs/decision-logs"
      cp "$root"/evals/legacy/flask-0001-*.md "$w/docs/decision-logs/0001-request-size-limits.md"
      sed -n '/^## 判断の照合と記録/,$p' "$root/CLAUDE.md" > "$w/CLAUDE.md"  # docs/ai-workflow.md の 3 行と同じ
    fi
    (cd "$w" && printf '%s' "$prompt" | claude -p --output-format stream-json --verbose \
      --allowedTools Read Grep Glob Skill Agent Write Edit "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" \
      "Bash(git grep:*)" "Bash(git rev-parse:*)" "Bash(python3 .claude/skills/decision-log/scripts/build_index.py:*)" \
      > "$work/ab-$cond$n.jsonl" 2>&1) || true
    echo "$cond$n: $(git -C "$w" status --porcelain -- src docs/decision-logs | tr '\n' ' ')"
    n=$((n + 1))
  done
done
