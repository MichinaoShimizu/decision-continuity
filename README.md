# decision-continuity

過去の変更から、何が起きたか・なぜか・何が分かっていないかを Decision log に起こし、決定につなげる。

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
    D -. "決定にする" .-> DR[("決定（DR）")]
    DR -. "変更を照らす" .-> G["adr-guard"]
    G -.-> H

    classDef rethink stroke-dasharray: 5 5
    class DR,G rethink
```

実線が使える部分（[decision-log](adr/skills/decision-log/SKILL.md) と [decision-log-reader](adr/agents/claude/decision-log-reader.md)）、点線が再考中の部分。
