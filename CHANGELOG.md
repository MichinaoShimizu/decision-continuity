# Changelog

decision-continuity の主な変更。[Keep a Changelog](https://keepachangelog.com/) の形で書く。変更は `changes/` の断片に書き（[changes/README.md](changes/README.md)）、リリースのときに版の節にまとめる。版は中身から決まり（[Semantic Versioning](https://semver.org/)、`sh tools/next-version.sh`）、各版の節がそのまま GitHub のリリースノートになる。手順は [docs/release.md](docs/release.md)。

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
