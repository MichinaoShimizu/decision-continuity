#!/bin/sh
# decision-log のスキルとサブエージェントを、別のリポジトリに入れる。入れ直すと上書きして更新する。
#   sh tools/install.sh <claude|kiro> [<入れ先のリポジトリ（既定はいまのディレクトリ）>]
#
# claude：skills/decision-log/ → .claude/skills/decision-log/、agents/claude/*.md → .claude/agents/
# kiro：  skills/decision-log/ → .kiro/skills/decision-log/、agents/kiro/*.json と *.md → .kiro/agents/（CLI は JSON、IDE は Markdown を読む）
set -eu

die() { printf 'install: %s\n' "$*" >&2; exit 1; }

[ $# -ge 1 ] && [ $# -le 2 ] || die "usage: sh tools/install.sh <claude|kiro> [<repository>]"
src=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)
dest=${2:-.}
[ -d "$dest" ] || die "$dest is not a directory"
dest=$(CDPATH= cd -- "$dest" && pwd -P)
[ "$dest" != "$src" ] || die "install into another repository, not decision-continuity itself"

case $1 in
  claude) dir=.claude; set -- "$src"/agents/claude/*.md ;;
  kiro) dir=.kiro; set -- "$src"/agents/kiro/*.json "$src"/agents/kiro/*.md ;;
  *) die "unknown target: $1 (claude or kiro)" ;;
esac

skill=$dest/$dir/skills/decision-log
mkdir -p "$dest/$dir/skills" "$dest/$dir/agents"
# 前の版で消えたファイルが残らないよう、スキルは入れ替える
rm -rf "$skill"
cp -R "$src/skills/decision-log" "$skill"
rm -rf "$skill/scripts/__pycache__"
cp "$@" "$dest/$dir/agents/"

echo "installed into $dest/$dir:"
echo "  skills/decision-log/"
for f in "$@"; do echo "  agents/${f##*/}"; done
