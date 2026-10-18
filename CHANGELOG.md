# Changelog

decision-continuity の主な変更。[Keep a Changelog](https://keepachangelog.com/) の形で書く。変更は `changes/` の断片に書き（[changes/README.md](changes/README.md)）、リリースのときに版の節にまとめる。版は中身から決まり（[Semantic Versioning](https://semver.org/)、`sh tools/next-version.sh`）、各版の節がそのまま GitHub のリリースノートになる。手順は [docs/release.md](docs/release.md)。

## v0.8.0 - 2026-10-18

### Added

- decision-log: 変える前に関係する判断を照らす `check` と、人が決めた判断を変更と同じ PR に記録する `record` を足した。`build_index.py --related <パス>… --words <言葉>` が、パスと言葉で関係する Decision log を挙げる。回し方は `docs/ai-workflow.md`

## v0.7.1 - 2026-10-18

### Fixed

- change-history: PR を通さないブランチの取り込み（`Merge branch …`）に一覧で印を付け、月の主な変更の 1 行目にしないようにした。取り込みしかない月は「目立った変更なし」と書く

## v0.7.0 - 2026-10-18

### Added

- change-history: マージされた変更を月ごとに並べ、月ごとの主な変更と年表（`timeline.md`）をまとめる新しいスキル。タグやリリースのないリポジトリで、いつ・どんな変更をしてきたかを読めるようにする。`tools/install.sh` は skills/ の全部を入れる

## v0.6.1 - 2026-10-18

### Changed

- decision-log: 「いま」の行を「## ステータス」の節に移し、`Active`（いまも有効）・`Superseded`（置き換わった）・`Removed`（なくなった）のどれかで始めるようにした。起きたこと（変更の履歴）と、いまのステータスを混ぜないため。行の中のハッシュもやめた（基準のコミットは `checked` とリンクにある）。前の形（`**いま**：…`）も読む

## v0.6.0 - 2026-10-18

### Changed

- BREAKING: decision-log: スキルと Decision log の形を、ぎりぎりまで簡素にした
  - 指示は SKILL.md と `references/format.md` の 2 つだけ（合計で 54KB から 14KB）。モードは `audit` と `write`
  - Decision log は「いま」の 1 行、起きたこと（`- YYYY-MM-DD <何が変わったか>（PR と関わった人）`）、理由、分かっていないことの 4 つ。フロントマターは `category` と `checked`
  - 行ごとの番号（`C1`）・状態の語・「履歴：／現在：」・関わった人の節・「分類を更新」と「再確認」の追記をやめた。分類と `checked` はフロントマターを直す
  - `--stale` は「いま」の行のリンクを見る。前の形の Decision log も読む（「分類を更新」と「再確認」の追記だけは読まないので、使っていたらフロントマターに写す）

### Fixed

- `build_index.py --stale`：ほかのリポジトリへのリンクを数えない。`checked` のあとに行がずれても、リンクの行を写してから比べる。git の出力を UTF-8 で読む
- `build_index.py`：空の `checked:` などで次の行を値として読んでいた。`origin` がないときの索引のリポジトリ名を、リポジトリのフォルダー名にする（`docs` になっていた）
- `tools/install.sh`：`CDPATH` を設定していると、パスが壊れていた

## v0.5.0 - 2026-10-18

### Added

- decision-log: `recheck` モード。`build_index.py --stale` で「現在」のリンク先が確かめたあとに変わった Decision log を挙げ（行の範囲があればその範囲の変更だけを数える）、確かめ直した結果を「**再確認**」の追記で足す（`references/recheck.md`）

### Changed

- decision-log: 新しく書く Decision log は、フロントマターに `checked`（基準のコミット）、本文の最初に「**いま**」の 1 行を置き、リンクは参照の定義として本文の最後にまとめる。作成とマージが同じ人でレビューのない PR は「関わった人」を 1 行にまとめる。追記に足すのは印の付くものと 3 行までの後の変化にし、それを超えたら新しい Decision log にする
  - `--check` は、`checked` のある Decision log の「いま」の行と、「再確認」の追記の 1 行目を確かめる。`checked` のない既存の Decision log はそのまま通る

## v0.4.1 - 2026-10-18

### Changed

- decision-log: 理由の証拠を広く読む。行に付いたレビューのコメント、PR の中のコミットのメッセージ、差分の中のコードのコメントや CHANGELOG（「記録あり（差分）」を新設）、本文・コメント・コミットから参照された issue とそのコメント（1 段だけ）。`gh` で読めない外部のリンクは「元の場所」に未読として挙げ、作成者への問いにする
- decision-log: 「起きたこと」に値の前後（`3 から 5`）、同じ変更でテストやドキュメントが変わったか、置き換わったものは何日後かを書く。状態に「一部置き換え済み」を足す
- `build_index.py --check` が「起きたこと」の各行を確かめる：状態の語、「履歴：」と「現在：」の両方、C の番号の重なり
- decision-log・reader・planner: `git -C <パス>` を付けない、引数の記号は一重引用符で囲む、と手順に書く。評価で reader が `git -C /…/repo show` と書いて許可に当たらず拒否されていた

### Fixed

- Kiro 3.x の decision-log-reader：`gh api repos/*`（REST の GET）を確認なしで通し、書き込みになる指定（`-X`・`--method`・`-f`・`-F`・`--raw-field`・`--input`）は deny で止める。行のコメントや参照された issue を読むたびに確認が出ていた
- decision-log: サブエージェントの終わりを `sleep` で待たない、と手順に書く。コマンドの書き方を `references/commands.md` にまとめる

## v0.4.0 - 2026-10-18

### Added

- `tools/install.sh`：スキルとサブエージェントを 1 つのコマンドで Kiro（`.kiro/`）か Claude Code（`.claude/`）に入れる。入れ直すと更新する

## v0.3.0 - 2026-10-18

### Added

- decision-log-planner：decision-log の範囲と候補を手元の git で洗い、読み手への分担を返すサブエージェント。Kiro では、その許可で手順 0〜1 のコマンドが確認なしで通る

### Changed

- decision-log: 手順 0〜1 の洗い出しを decision-log-planner に任せ、候補は件数によらず decision-log-reader に読ませる。Kiro でメインの会話に `git log` などの確認が出続けていたため（エージェントの定義の許可は、そのサブエージェントの中でだけ効く）
  - 既存の Decision log の `category` と `keywords` は、シェルの `grep` ではなくエージェントの読む・探す道具で読む
  - サブエージェントを入れていなければ、これまでどおり自分で回す
  - reader は 1 回の応答でまとめて呼ぶ（Kiro は 1 回に 4 つまでなので、分類が多ければまとめて 4 つ以内にする）。1 つずつ順に呼んでいた

## v0.2.0 - 2026-10-17

### Added

- decision-log: Decision log を英語で書ける。`lang=en` と頼むか、リポジトリの指示（`CLAUDE.md` など）が英語を求めるときに英語で書く。形は日本語と同じで、決まった言葉だけが英語になる（`references/writing.md` の「英語で書くとき」）
  - 索引のスクリプトは日本語と英語の両方の Decision log を読み、索引の言語はいまの索引に合わせる（新しく作るときは多いほうの言語。`--lang` で指定もできる）

## v0.1.0 - 2026-10-17

### Added

- decision-log: コードのリポジトリの履歴（PR・issue・コミット・コード）から、何が起きたか・なぜか・何が分かっていないかを Decision log に起こすスキル。既定は読むだけ（`audit`）で、書くのは `write` と頼んだときだけ
- decision-log-reader: decision-log の候補を分類ごとに並行に読み、決まった形で返すサブエージェント（Claude Code 用と、Kiro 用の JSON と Markdown）
- Claude Code のプラグイン（`/plugin install decision-continuity --marketplace MichinaoShimizu/decision-continuity`）と npx skills で入れられる
