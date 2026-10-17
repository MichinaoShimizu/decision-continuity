# decision-continuity

コードのリポジトリの履歴から、何が起きたか・なぜか・何が分かっていないかを Decision log に起こすスキル。Claude Code と Kiro で動く。

## 流れ

```mermaid
flowchart TD
    H[("PR・issue・コミット・コード")] --> L["decision-log<br>候補を絞る"]
    L -- "候補が 5 件を超える" --> R["decision-log-reader<br>分類ごとに並行に読む"]
    R --> V
    L --> V["主張ごとに確かめる<br>履歴（PR・差分）と現在（基準のコミット）"]
    V --> D[("Decision log<br>起きたこと・理由・分かっていないこと")]
    D -- "理由が不明" --> Q["知っていそうな人に聞く"]
    Q -- "分かった（追記）" --> D
```

## 入れ方

| 写すもの | Claude Code | Kiro |
|---|---|---|
| [skills/decision-log/](skills/decision-log/SKILL.md) | `.claude/skills/decision-log/` | `.kiro/skills/decision-log/` |
| [agents/](agents/) の decision-log-reader | `claude/` の `.md` を `.claude/agents/` | `kiro/` の `.json` と `.md` を両方 `.kiro/agents/` |

使うときは「認証まわりがなぜこうなったか、履歴から起こして」のように頼む。既定は読むだけ（`audit`）で、書くのは `write` と頼んだときだけ。

### Claude Code で確認を減らす

スキルの `allowed-tools` がサブエージェント（decision-log-reader）にも効くかは、公式ドキュメントに書かれていない。reader のコマンドに毎回確認が出るときは、読むだけのコマンドを `.claude/settings.json` に足す（メインの会話とサブエージェントの両方に効く）。書くコマンド（`git commit`・`git push`・`gh pr create` など）は足さない。

```json
{
  "permissions": {
    "allow": [
      "Bash(git log *)", "Bash(git show *)", "Bash(git grep *)", "Bash(git rev-parse *)",
      "Bash(git remote get-url *)", "Bash(TZ=Asia/Tokyo git log *)",
      "Bash(gh pr view *)", "Bash(gh issue view *)", "Bash(gh release view *)",
      "Bash(glab mr view *)", "Bash(glab issue view *)"
    ]
  }
}
```

Kiro は、`agents/kiro/` の定義に読むだけのコマンドの許可が入っている。

## 確かめる

- テスト：`python3 -I -m unittest discover -s tests`
- 実際のエージェントでの評価：[evals/cases.md](evals/cases.md)

[MIT License](LICENSE)
