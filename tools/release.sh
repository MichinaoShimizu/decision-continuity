#!/bin/sh
# リリースの PR を手元で用意する。push もタグ付けもしない（PR をマージすると tag.yml がタグを打ってリリースする）。
#   sh tools/release.sh
#   DC_RELEASE_REMOTE=<リモートかパス>   # origin の代わりに、そこの main から作る（スクリプトを試すとき）
#   DC_RELEASE_TRAILER=<行>             # 「Release vX.Y.Z」のコミットの最後に、この行を足す（例: Co-Authored-By: ...。エージェントが作るときに使う）
#
# 流れ:
#   1. 作業ツリーに変更があれば止まる（コミットするか、別のブランチに置いてから。素の git stash は使わない）
#   2. origin の main を取ってきて、tools/next-version.sh で次の版 vX.Y.Z を決め、そこから claude/release-vX.Y.Z を作る
#   3. tools/changelog.sh --release で、changes/ の断片と「## Unreleased」を「## vX.Y.Z - <今日（UTC）>」にまとめる
#   4. .claude-plugin/plugin.json の version を X.Y.Z にする（Claude Code はこの値で更新を見分ける）
#   5. テストと sh tools/release-notes.sh vX.Y.Z を回し、コミットして、次にすること（push と PR）を出す
#
# 中身はすべて main の中にあり、いちばん最後の行で呼ぶ（途中で git switch がこのファイルを書き換えても、読み終えたものを動かす）。
set -eu

die() { printf 'release: %s\n' "$*" >&2; exit 1; }

main() {
  [ $# -eq 0 ] || die "usage: sh tools/release.sh"
  root=$(git rev-parse --show-toplevel) || die "run this inside the decision-continuity repository"
  cd "$root"

  # 1. 作業ツリー
  if [ -n "$(git status --porcelain --untracked-files=normal)" ]; then
    git status --short >&2
    die "the working tree has changes. Commit them or move them to another branch first (don't use a bare \"git stash\")"
  fi

  # 2. 版とブランチ
  remote=${DC_RELEASE_REMOTE:-origin}
  echo "== fetching main from $remote"
  git fetch --quiet --tags "$remote" main
  # ブランチを作る前に止まったら、もとのブランチに戻す
  orig=$(git symbolic-ref --quiet --short HEAD || git rev-parse HEAD)
  back() {
    git switch --quiet "$orig" 2>/dev/null || git switch --quiet --detach "$orig"
    die "$1"
  }
  git switch --quiet --detach FETCH_HEAD
  v=$(sh tools/next-version.sh) || back "nothing to release (no fragments in changes/ and no \"## Unreleased\" in CHANGELOG.md)"
  printf '%s\n' "$v" | grep -Eq '^v[0-9]+\.[0-9]+\.[0-9]+$' || back "next-version.sh printed \"$v\""
  branch=claude/release-$v
  if git show-ref --verify --quiet "refs/heads/$branch"; then
    back "the branch $branch already exists. Delete it (git branch -D $branch) or finish that release"
  fi
  if git ls-remote --exit-code --heads "$remote" "$branch" >/dev/null 2>&1; then
    back "$remote already has the branch $branch; finish that pull request first"
  fi
  if git ls-remote --exit-code --tags "$remote" "refs/tags/$v" >/dev/null 2>&1; then
    back "the tag $v already exists on $remote"
  fi
  git switch --quiet -c "$branch"
  echo "== $branch (from main of $remote, $(git rev-parse --short HEAD))"

  # 3. CHANGELOG
  today=$(date -u +%Y-%m-%d)
  sh tools/changelog.sh --release "$v" --date "$today"
  want=$(sh tools/next-version.sh "$v")
  [ "$want" = "$v" ] || die "the merged section says $want, not $v (sh tools/next-version.sh $v)"

  # 4. プラグインの版
  plugin=.claude-plugin/plugin.json
  grep -Eq '^  "version": "[0-9]+\.[0-9]+\.[0-9]+",$' "$plugin" || die "no \"version\" line to update in $plugin"
  sed "s/^  \"version\": \"[0-9.]*\",\$/  \"version\": \"${v#v}\",/" "$plugin" > "$plugin.tmp"
  cat "$plugin.tmp" > "$plugin" # cat で書く（mv だと、もとの権限が変わることがある）
  rm -f "$plugin.tmp"

  # 5. テスト、リリースノート、コミット
  echo "== python3 -I -m unittest discover -s tests"
  python3 -I -m unittest discover -s tests -p 'test_*.py' || die "the tests failed. Fix it on $branch, commit, and continue from the next steps in docs/release.md"
  echo "== sh tools/release-notes.sh $v"
  notes=$(sh tools/release-notes.sh "$v")
  printf '%s\n' "$notes"

  git add -A -- CHANGELOG.md changes "$plugin"
  if [ -n "${DC_RELEASE_TRAILER:-}" ]; then
    git commit --quiet -m "Release $v" -m "$DC_RELEASE_TRAILER"
  else
    git commit --quiet -m "Release $v"
  fi
  echo
  echo "== committed $(git rev-parse --short HEAD) on $branch:"
  git show --stat --format='   %s' HEAD | sed 's/^/  /'
  cat <<EON

Next steps (this script pushes and tags nothing):
  1. Read the diff: git show HEAD
  2. Push:          git push -u $remote $branch
  3. Open the pull request to main, titled "Release $v", with the release notes above as its body:
                    sh tools/release-notes.sh $v | gh pr create --base main --title "Release $v" --body-file -
  4. When it is merged, .github/workflows/tag.yml tags $v and publishes the GitHub release.
EON
}

main "$@"
