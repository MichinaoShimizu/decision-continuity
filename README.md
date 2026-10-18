# decision-continuity

コードのリポジトリの履歴から、何が起きたか・なぜか・何が分かっていないかを Decision log に起こす。Claude Code と Kiro で動く。

| 名前 | 種類 | すること |
|---|---|---|
| [decision-log](skills/decision-log/SKILL.md) | スキル | 本体 |
| [decision-log-planner](agents/claude/decision-log-planner.md) | サブエージェント | 候補を洗い、分担を決める |
| [decision-log-reader](agents/claude/decision-log-reader.md) | サブエージェント | 候補を並列に読む |

## Claude Code（プラグイン）

| | コマンド |
|---|---|
| 導入 | `/plugin install decision-continuity --marketplace MichinaoShimizu/decision-continuity` を Claude Code の中で実行し、範囲（user／project／local）を選ぶ |
| 更新 | `claude plugin update decision-continuity@decision-continuity` を実行し、Claude Code の中で `/reload-plugins` |
| 削除 | `claude plugin uninstall decision-continuity@decision-continuity`（project や local に入れたなら `--scope project` などを足す）。マーケットプレイスも消すなら `claude plugin marketplace remove decision-continuity` |

- 導入の 1 行は Claude Code 2.1.275 から。それより前は `/plugin marketplace add MichinaoShimizu/decision-continuity` のあと `/plugin install decision-continuity@decision-continuity`
- 自動では更新されない（公式以外のマーケットプレイスは自動更新が既定で切れている）。`/plugin` の Marketplaces タブで自動更新を入れられる
- 名前は `decision-continuity:decision-log`・`decision-continuity:decision-log-planner`・`decision-continuity:decision-log-reader` になる

## Kiro（と、プラグインを使わない Claude Code）

導入と更新は同じコマンド。リポジトリのルートで実行する。`kiro` を `claude` にすると `.claude/` に入る。版を決めるなら `--depth 1` のあとに `--branch vX.Y.Z` を足す（版は[リリース](https://github.com/MichinaoShimizu/decision-continuity/releases)）。

```sh
d=$(mktemp -d) && git clone --depth 1 https://github.com/MichinaoShimizu/decision-continuity "$d" && sh "$d/tools/install.sh" kiro
```

削除（`claude` で入れたなら `.kiro` を `.claude` に読み替える）：

```sh
rm -rf .kiro/skills/decision-log .kiro/agents/decision-log-planner.* .kiro/agents/decision-log-reader.*
```

- 導入・更新・削除のあとは Kiro の会話を開き直す（エージェントの定義は起動時に読まれる）
- ワークスペースを信頼していないと、スキルは読まれず、コマンドごとに確認が出る
- `npx skills add MichinaoShimizu/decision-continuity --skill decision-log -a kiro-cli` で入れた場合はスキルだけが入る。更新は `npx skills update decision-log`、削除は `npx skills remove decision-log`。サブエージェントは上のコマンドで入れる

## 使い方

```text
decision-log で audit して。範囲は src/payment/。
洗い出しは decision-log-planner、読むのは decision-log-reader に、1 回でまとめて並列に任せて。
```

- 既定は読むだけ（`audit`）。ファイルに書くのは `write` と頼んだときだけ（ブランチを切ってコミットし、PR を出す）
- `scope=<パス｜サブシステム｜期間>`・`depth=<数>`（差分まで読む件数。既定 20）・`lang=en` を添えられる
- サブエージェントの名前を出すと、その定義の許可で確認なしに動く（Kiro は 1 回に 4 つまで並列）

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
