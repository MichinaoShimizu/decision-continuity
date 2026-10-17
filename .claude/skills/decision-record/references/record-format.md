# 本文と記録データの型（decision-record）

## 本文の書き方

`--body-file` に渡すファイルは、先頭に記録データのフロントマター、その下に本文を書く。`records.py create` がフロントマターをファイルの先頭に、タイトルをその下に置く。本文は、読む人のために決めたことを一行目に置く。

````markdown
---
（下の「記録データの型」）
---

**（決めたこと：一文）**

| 決めた人 | 決済チームのチームリード |
|---|---|
| 承認 | セキュリティ責任者 |
| 使った決め方 | DF-12 |
| 影響範囲 | チーム内・すぐ戻せる |
| 決めた日 | 2026-10-03 |

**なぜ**
（理由。重い判断なら他の案、反対意見、リスクを引き受けた人も）

**前提（崩れたら見直す）**
- （前提）

**元の場所**：（リンク）
````

- 表の値は人が読む言葉で書く（`config.yaml` の roles の表示名、「部署横断・戻すのに手間」など）。分からない値は「不明」。
- 空の行（承認がない、決め方を使っていない）は省く。
- 拾った記録（`entry: auto`）は一行目の下に「> 拾った内容です。元の場所と合わせて読んでください。」と添える。

## 記録データの型

フロントマターの中身。トップレベルの `key: value` を 1 行ずつ書き、リストは 1 行の `[a, b]` で書く（`records.py` はこの形だけを読む）。前の形（本文の最後の ```` ```yaml ```` ブロック）も読めるが、新しく書くときはフロントマターにする。

```yaml
kind: decision            # decision | flow（誰が決める・承認するかの決め方）
status: accepted          # proposed | accepted（終了の追記の後は superseded | retired）
approved_via: null        # 通った決め方の番号（例：DF-12）
superseded_by: null
entry: explicit           # explicit: 人が追加 | auto: 仕組みや AI が拾った
decided_at: null          # YYYY-MM-DD
decided_by: []            # 最終的に決めた役割 [{role, org, delegated_by?}]。複数なら全員で決めた。この件だけ任されたなら delegated_by: {role, org}
approved_by: []           # 決める前に承認した役割 [{role, org}]（承認した順）
domain: technology        # technology | product | organization | business
scope: team               # team | multi_team | cross_department | company
reversibility: easy       # easy | costly | irreversible
touches_sensitive: false  # セキュリティ・個人情報・権限・監視や通知・ログに触れる
repos: []                 # 縛るコードのリポジトリ名。全リポジトリなら [all]。コードに関係しなければ空
paths: []                 # 関係するパス（前方一致）
keywords: []              # 決定の文に出てこないのに変更に出てくる言葉（コードの識別子、言い換え）
decision: ""
premises: []              # [text] 崩れたら追記する
sources: []               # [{type, url}] type: chat|meeting|pr|ticket|approval|asked|manual
unconfirmed: []           # 元に書かれていなかった項目のキー
```

既存の ADR は `entry: explicit` で取り込める（Context→本文、Decision→`decision`、Status→状態、Consequences→後の追記、ADR 索引のパスとキーワード→`paths`・`keywords`、置き場所のリポジトリ→`repos`）。Accepted でない ADR は `status: proposed` で取り込む。
