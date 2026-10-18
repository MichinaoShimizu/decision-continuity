# Claude Code で確認を減らす

サブエージェントのコマンドに毎回確認が出るときは、読むだけのコマンドを `.claude/settings.json` に足す。書くコマンド（`git commit`・`git push`・`gh pr create` など）は足さない。

```json
{
  "permissions": {
    "allow": [
      "Bash(git log *)", "Bash(git show *)", "Bash(git grep *)", "Bash(git rev-parse *)",
      "Bash(git remote get-url *)", "Bash(TZ=Asia/Tokyo git log *)",
      "Bash(gh pr view *)", "Bash(gh issue view *)", "Bash(gh release view *)",
      "Bash(glab mr view *)", "Bash(glab issue view *)", "Bash(gh api repos/*)"
    ],
    "deny": [
      "Bash(gh api *-X*)", "Bash(gh api *--method*)", "Bash(gh api *-f*)",
      "Bash(gh api *-F*)", "Bash(gh api *--input*)"
    ]
  }
}
```

`gh api repos/*` は、`gh pr view` が使えない環境（GraphQL が止められているなど）で PR を REST API で読むため。書き込みになる指定は `deny` で止める。
