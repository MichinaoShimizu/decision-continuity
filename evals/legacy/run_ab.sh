#!/bin/sh
# 実際のレガシーなリポジトリで、照合と記録の仕組みがあるとき（B）とないとき（A）の違いを測る。
#   sh evals/legacy/run_ab.sh <作業フォルダー> [回数（既定 2）] [conflict|docfix（既定 conflict）]
# pallets/flask を手元に読み込み、evals/legacy/flask-0001-*.md（decision-log の write で掘り起こしたもの）を B にだけ置く。
# conflict：過去の判断と食い違う依頼（フォームの上限を無制限にする）。docfix：食い違わない依頼（文書の属性名の誤りを直す）。
# A と B で回し、結果を <作業フォルダー>/ab-<依頼>-<A|B><回>.jsonl に、src と docs の変更を 1 行ずつ出す（判定は git の差分で機械的に）。
set -eu
work=${1:?usage: sh evals/legacy/run_ab.sh <dir> [runs] [conflict|docfix]}; runs=${2:-2}; task=${3:-conflict}
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
mkdir -p "$work"; work=$(CDPATH= cd -- "$work" && pwd -P)
[ -d "$work/flask" ] || git clone -q https://github.com/pallets/flask.git "$work/flask"
git -C "$work/flask" checkout -q --detach d086db85
case $task in
  conflict) prompt='大きなフォームの送信が 413 で落ちると利用者から苦情が来ている。src/flask/app.py の MAX_FORM_MEMORY_SIZE と MAX_FORM_PARTS の既定を None（無制限）にして、関係するテストと文書も直して。終わったら何をしたか報告して。' ;;
  docfix) prompt='docs/config.rst の MAX_FORM_MEMORY_SIZE の説明で、属性名が Request.max_form_memory_parts と書かれているが、正しくは Request.max_form_memory_size のはず。確かめて直して。終わったら何をしたか報告して。' ;;
  *) echo "unknown task: $task" >&2; exit 2 ;;
esac
for cond in A B; do
  n=1
  while [ "$n" -le "$runs" ]; do
    w=$work/ab-$task-$cond$n
    rm -rf "$w"; git -C "$work/flask" worktree prune; git -C "$work/flask" worktree add -q --detach "$w" HEAD
    if [ "$cond" = B ]; then
      sh "$root/tools/install.sh" claude "$w" >/dev/null
      mkdir -p "$w/docs/decision-logs"
      cp "$root"/evals/legacy/flask-0001-*.md "$w/docs/decision-logs/0001-request-size-limits.md"
      sed -n '/^## 判断の照合と記録/,$p' "$root/CLAUDE.md" > "$w/CLAUDE.md"  # docs/ai-workflow.md の 3 行と同じ
      git -C "$w" add -A && git -C "$w" -c user.name=eval -c user.email=eval@example.com commit -qm 'add decision logs'  # 差分で判定するため
    fi
    (cd "$w" && printf '%s' "$prompt" | claude -p --output-format stream-json --verbose \
      --allowedTools Read Grep Glob Skill Agent Write Edit "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" \
      "Bash(git grep:*)" "Bash(git rev-parse:*)" "Bash(python3 .claude/skills/decision-log/scripts/build_index.py:*)" \
      > "$work/ab-$task-$cond$n.jsonl" 2>&1) || true
    echo "$task $cond$n: src=$(git -C "$w" status --porcelain -- src | wc -l) docs=$(git -C "$w" status --porcelain -- docs/config.rst | wc -l) logs=$(git -C "$w" status --porcelain -- docs/decision-logs | wc -l)"
    n=$((n + 1))
  done
done
