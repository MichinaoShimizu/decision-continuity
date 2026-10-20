# 複数のリポジトリを中央にまとめる

一覧にした複数のリポジトリの年表を、1 つのリポジトリ（中央のリポジトリ）に作る。各リポジトリには何も書かない。1 つのリポジトリだけを対象にする使い方（SKILL.md の手順）はそのまま使える。

## 置き場所

```text
<中央のリポジトリ>/
├── repos.txt                      # 対象の一覧
├── .cache/change-history/         # クローン（スクリプトが置く .gitignore で、git に入れない）
│   └── <owner>/<repo>/
└── docs/change-history/
    ├── README.md                  # 全体の年表
    └── <owner>/<repo>/
        ├── README.md              # そのリポジトリの年表（1 つのときと同じ形）
        └── YYYY-MM.md             # 主な変更の表（1 つのときと同じ形）
```

`repos.txt` は 1 行に 1 つ。GitHub の `owner/repo` か、その URL を書き、後ろに `--branch`・`--depth` を書ける。GitHub でないリポジトリは扱わない。`#` から後と空の行は読まない。

```text
pallets/click
pallets/flask --branch main --branch stable
```

## 手順

1. 作る：`python3 .claude/skills/change-history/scripts/build_many.py repos.txt docs/change-history`（Kiro は `.kiro/skills/…`、プラグインは `${CLAUDE_SKILL_DIR}/scripts/…`）。リポジトリごとに、ファイルの中身を取らない bare のクローンを作るか取り直し、`build_history.py` を回し、全体の `README.md` を作る。期間は `--since`・`--until` で絞る。出力の `== <owner>/<repo>（置き場所 …、--repo … --github-repo …）` が、そのリポジトリの書き手に渡すもの。
2. 主な変更を書く：SKILL.md の手順 2 を、リポジトリごとに回す。書き手には、出力の置き場所・`--repo`・`--github-repo`・`--branch` をそのまま渡す。返った要約は、そのリポジトリの `README.md` の表に入れる（全体の `README.md` は書かない）。クローンは git に入らないので、各リポジトリの Decision log へのリンクは PR の列に入らない。
3. 作り直す：手順 1 のコマンドを `--no-fetch` を付けて回す（取り直すと、書いている間に増えた月が混ざる）。崩れが 0 件になるまで直す。
4. 年の要点を書く：SKILL.md の手順 4 を、各リポジトリの `README.md` に回す。全体の `README.md` には、スクリプトがそれを写す。最後に `--check` で確かめる（取り直さない）。
5. 報告する：リポジトリごとの読んだブランチ、期間、件数、書いた月と年。書いたら、中央のリポジトリでブランチを切って PR を出す。

## 全体の年表

年ごとに、リポジトリごとの年の要点（各リポジトリの `README.md` から写す）と、月 × リポジトリの件数の表を並べる。件数は月の表へのリンク。変更のなかった月は `0`、リポジトリの最初の変更より前の月は空にする。どこにも変更のない月が続けば 1 行にまとめる。

```markdown
## 2024

### [pallets/click](pallets/click/README.md)

- 補完を作り直した（2024-03〜2024-05）

| 月 | pallets/click | pallets/flask |
|---|---|---|
| 2024-05 | [12](pallets/click/2024-05.md) | 0 |
```

## 気をつけること

- 非公開のリポジトリは、中央で回す環境の git（clone と fetch）と `gh`（PR とコミットのアカウント）に、読む権限が要る。
- 全体の年表を読める人は、全部のリポジトリの変更の概要と Author のアカウント名を読める。中央のリポジトリの公開範囲は、対象のうちいちばん狭いものに合わせる。
- クローンは `.cache/change-history/` に残り、次からは差分だけを取る。GitHub から取った PR も、クローンの中に覚えておく。置き場所は `--cache` で変えられる。
