# decision-continuity

コードのリポジトリの履歴から、何が起きたか・なぜか・何が分かっていないかを Decision log に起こすスキル。

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

テスト：`python3 -I -m unittest discover -s tests`
