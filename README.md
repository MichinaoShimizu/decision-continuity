# decision-continuity

コードのリポジトリの履歴から、いつ・何が変わったか（change-history）と、なぜか・何が分かっていないか（decision-log）を起こす。Claude Code と Kiro で動く。

## Claude Code

シェルで実行する。次に起動したときから効く。

```sh
# 導入
claude plugin install decision-continuity --marketplace MichinaoShimizu/decision-continuity

# 更新
claude plugin update decision-continuity@decision-continuity

# 削除
claude plugin uninstall decision-continuity@decision-continuity
```

## Kiro

リポジトリのルートで実行する。導入と更新は同じ。終わったら会話を開き直す。

```sh
# 導入・更新
d=$(mktemp -d) && git clone --depth 1 https://github.com/MichinaoShimizu/decision-continuity "$d" && sh "$d/tools/install.sh" kiro

# 削除
rm -rf .kiro/skills/decision-log .kiro/skills/change-history .kiro/agents/decision-log-planner.* .kiro/agents/decision-log-reader.* .kiro/agents/change-history-writer.*
```

スキルの前書きの `allowed-tools`（確認なしで通すコマンド）は Claude Code 向けで、Kiro は読まない（Kiro の文書にない項目）。Kiro で確認なしに通るのは、サブエージェントの定義（`.kiro/agents/`）に書いた読むだけのコマンドだけ。メインの会話で回すコマンド（索引のスクリプトなど）は、確認が出たら内容を見て許す。

## 使い方

まず change-history で流れをつかみ、「なぜ」まで要るテーマを decision-log で起こし、以後は変える前に check、決めたら record。回し方は[判断を途切れさせない回し方](docs/ai-workflow.md)。どちらも既定は下書きを返すだけで、ファイルに書くのは頼んだときだけ。履歴は手元の git から読むので、浅いクローンなら先に `git fetch --unshallow` する。

### 年表を作る（change-history）

`docs/change-history/` に、月ごとの主な変更の表（`YYYY-MM.md`。日付・概要・PR・Author）と、年表を兼ねた索引（`README.md`）を作る。タグやリリースがなくてもよい。月ごとの表は change-history-writer が受け持ち、12 か月ずつの回に分けて並べて書く。

```text
change-history で、いつどんな変更をしてきたかを月ごとにまとめて、年表まで作って。
change-history で、2024-01 からの分だけまとめて、年表まで作って。
```

#### 複数のリポジトリの年表を中央にまとめる

一覧にしたリポジトリの年表を、1 つのリポジトリ（中央のリポジトリ）にまとめて作ることもできる。各リポジトリには何も書かない。上の、いまのリポジトリを対象にする使い方はそのまま使える。

中央にするリポジトリに入れ（Claude Code はプラグインのまま、Kiro は中央のリポジトリのルートで上の導入のコマンド）、ルートに `repos.txt` を置く。1 行に 1 つ、`owner/repo` か clone できる URL を書き、後ろに `--branch` を書ける。

```text
pallets/click
pallets/flask --branch main --branch stable
https://gitlab.example.com/team/api.git
```

```text
change-history で、repos.txt のリポジトリの年表を中央にまとめて作って。
```

`docs/change-history/<owner>/<repo>/` に各リポジトリの年表（形は 1 つのときと同じ）を、`docs/change-history/README.md` に、年ごとのリポジトリ別の要点と月 × リポジトリの件数の表を作る。クローンは `.cache/change-history/` に置き（git には入れない）、次からは差分だけを取る。非公開のリポジトリは、回す環境の git と `gh` に読む権限が要る。全体の年表を読める人は全部のリポジトリの変更の概要を読めるので、中央のリポジトリの公開範囲に気をつける。詳しくは [複数のリポジトリを中央にまとめる](skills/change-history/references/many-repos.md)。

### Decision log を作る（decision-log）

`docs/decision-logs/` に、大事な変更ごとに、なぜ（記録にある範囲で）、いまのステータス、分かっていないことを書く。範囲を言わなければリポジトリ全体から、言えばそのパスや期間だけから、大事なものを洗い出す。

```text
decision-log で audit して。
decision-log で audit して。範囲は src/payment/。
decision-log で audit して。期間は 2024 年。
decision-log で write して。範囲は指定しない。
```

洗い出しは decision-log-planner、読むのは decision-log-reader が受け持つ。候補は大事な順に 20 件ずつの回に分け、全部の回を終えるまで続ける。読み手 1 つに渡すのは 5 件まで（30 ファイルか 1000 行を超える大きな PR は 1 件だけ。置き場所ごとに判断に当たるファイルから読み、読まなかったものは「読み残し」に返す）で、Decision log は 1 つずつ、節を全部埋めて書く。途中で止まったら、報告の「読み残し」にある次の回から頼み直す。

作ったあとは、変える前の照合（`check`）と、新しい判断の記録（`record`）に使う。

```text
decision-log で check して。これから src/payment/client.py のリトライの上限を変えたい。
decision-log で record して。@alice がリトライの上限を 7 にすると決めた。理由は…
```

## その他

[確認を減らす（Claude Code）](docs/claude-code-permissions.md)／[変更](CHANGELOG.md)／[リリース](docs/release.md)／[このリポジトリの経緯](docs/decision-logs/README.md)／[MIT License](LICENSE)
