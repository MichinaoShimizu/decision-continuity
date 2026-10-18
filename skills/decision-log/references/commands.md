# コマンドの書き方（decision-log）

確認なしで通る許可（Claude Code の `allowed-tools`、Kiro のエージェントの定義）は、`git show …` のように決まった形で始まるコマンドにだけ当たる。外れると、そのたびに確認が出るか、止められる。

- 1 回に 1 つだけ実行する。`;`・`&&`・`|`・`cd` でつながない。ループも使わない。
- リポジトリのルートで実行し、パスは相対で書く。`git -C <パス>` やリポジトリの絶対パスを付けない。
- 引数の中の記号は一重引用符で囲む（`--format='%h %s'`、`-G 'retr(y|ies)'`）。囲まないと `|` などがつなぎと見なされる。二重引用符は使わない。
- `TZ=` は先頭にそのまま書く（`TZ=Asia/Tokyo git log …`）。`env TZ=…` にしない。
- PR の一覧は git の履歴から作る。`gh pr list` は GraphQL を使うので、止められた環境では許可しても失敗する。
- GitHub の REST は GET だけを使う（`gh api repos/<owner>/<repo>/…`）。`-X`・`--method`・`-f`・`-F`・`--input` は付けない。
- 索引のスクリプトは相対パスで呼ぶ（`python3 .claude/skills/decision-log/scripts/build_index.py <置き場所>`。Kiro なら `.kiro/skills/…`）。
- サブエージェントの終わりを `sleep` やファイルの監視で待たない。結果は呼び出しの戻りで受け取る。
