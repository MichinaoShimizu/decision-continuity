# decision-continuity

コードのリポジトリの履歴から、何が起きたか・なぜか・何が分かっていないかを Decision log に起こす。Claude Code と Kiro で動く。

| 名前 | 種類 | すること |
|---|---|---|
| [decision-log](skills/decision-log/SKILL.md) | スキル | 本体 |
| [decision-log-planner](agents/claude/decision-log-planner.md) | サブエージェント | 候補を洗い、分担を決める |
| [decision-log-reader](agents/claude/decision-log-reader.md) | サブエージェント | 候補を並列に読む |

## 入れ方

Claude Code（全部入る）：

```text
/plugin install decision-continuity --marketplace MichinaoShimizu/decision-continuity
```

Kiro など（スキルだけ。`main` の最新が入る。固定するなら `…/decision-continuity#v0.3.0`）：

```sh
npx skills add MichinaoShimizu/decision-continuity --skill decision-log -a claude-code -a kiro-cli
```

サブエージェントは手で写す：[agents/](agents/) の `claude/*.md` → `.claude/agents/`、`kiro/*.json` と `kiro/*.md` → `.kiro/agents/`。

## 使い方

```text
decision-log で audit して。範囲は src/payment/。
洗い出しは decision-log-planner、読むのは decision-log-reader に、1 回でまとめて並列に任せて。
```

- 既定は読むだけ（`audit`）。書くのは `write` と頼んだときだけ
- サブエージェントの名前を出すと、その許可で確認なしに動く（Kiro は 1 回に 4 つまで並列）

Claude Code でサブエージェントに確認が出るときは `.claude/settings.json` に足す：

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

## 限界

- 言葉・定数・設定ファイルで候補を拾うので、言葉の出ない振る舞いの変更は拾えない。文書中心のリポジトリには向かない
- リポジトリの外の変更（インフラ、管理画面のフラグ）は見えない

## その他

テスト `python3 -I -m unittest discover -s tests`／評価 [evals/decision-log/](evals/decision-log/cases.md)／変更 [CHANGELOG.md](CHANGELOG.md)／リリース [docs/release.md](docs/release.md)／このリポジトリの経緯 [docs/decision-logs/](docs/decision-logs/README.md)／[MIT License](LICENSE)
