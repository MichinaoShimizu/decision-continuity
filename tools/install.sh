#!/bin/sh
# スキル（skills/ の全部）とサブエージェントを、別のリポジトリに入れる。入れ直すと上書きして更新する。
#   sh tools/install.sh <claude|kiro> [<入れ先のリポジトリ（既定はいまのディレクトリ）>]
#
# claude：skills/<名前>/ → .claude/skills/<名前>/、agents/claude/*.md → .claude/agents/
# kiro：  skills/<名前>/ → .kiro/skills/<名前>/、agents/kiro/*.json と *.md → .kiro/agents/（CLI は JSON、IDE は Markdown を読む）
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

mkdir -p "$dest/$dir/skills" "$dest/$dir/agents"
echo "installed into $dest/$dir:"
for s in "$src"/skills/*/; do
  name=$(basename "$s")
  skill=$dest/$dir/skills/$name
  # 前の版で消えたファイルが残らないよう、スキルは入れ替える
  rm -rf "$skill"
  cp -R "$s" "$skill"
  rm -rf "$skill/scripts/__pycache__"
  echo "  skills/$name/"
done
# 前の版で消えたサブエージェントが残らないよう、このキットのもの（decision-log-*・change-history-*）は入れ替える
rm -f "$dest/$dir/agents"/decision-log-* "$dest/$dir/agents"/change-history-*
cp "$@" "$dest/$dir/agents/"
for f in "$@"; do echo "  agents/${f##*/}"; done
