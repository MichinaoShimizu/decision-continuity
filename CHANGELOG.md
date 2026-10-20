# Changelog

decision-continuity の主な変更。[Keep a Changelog](https://keepachangelog.com/) の形で書く。変更は `changes/` の断片に書き（[changes/README.md](changes/README.md)）、リリースのときに版の節にまとめる。版は中身から決まり（[Semantic Versioning](https://semver.org/)、`sh tools/next-version.sh`）、各版の節がそのまま GitHub のリリースノートになる。手順は [docs/release.md](docs/release.md)。

## v0.14.0 - 2026-10-20

### Changed

- BREAKING: change-history: GitHub でデフォルトブランチにマージされた PR と、PR を通さない直接のコミットから年表を作る。日付・PR・Author は GitHub の値をそのまま使い、git の件名やメールから推測しない。`gh` が要り、GitHub でないリポジトリは扱わない
  - `--no-github` をなくし、`build_history.py` に `--github-repo OWNER/REPO` を足した。`build_many.py` の `repos.txt` は GitHub の `owner/repo` か、その URL だけを受け付ける
  - 年表の件数は、その月の PR と直接のコミットの数になった（マージの中身や保守ブランチの取り込みの中は数えない）
  - `--check`・`--list` は GitHub に問い合わせず、書き出したときに覚えた分を使う
  - 書き手は主な変更を `- #12、#13：概要` の行で書き、スクリプトが表にする（前の表の形もそのまま読む）

### Removed

- change-history: 主な変更の表の PR の列に、Decision log へのリンクを添えるのをやめた（v0.13.0 で足したもの）。`--decision-logs` もなくした。前に入ったリンクは、次に作り直すときに外れる

## v0.13.1 - 2026-10-20

### Changed

- change-history・decision-log: 読むブランチを推測しない。言われなければデフォルトブランチ（`origin/HEAD` の先）だけを読み、`develop`・`production` などは `--branch` で言われたときだけ読む
  - change-history は、`origin/HEAD` がなければ `gh` で GitHub のデフォルトブランチを聞く。それでも分からなければ止まる。`git remote set-head origin --auto` で覚えさせるか、`--branch` で言う

### Fixed

- change-history: 主な変更の表の PR の列に、全角の `＃12`、PR の URL、`#` のない数字だけ（`12、13`）、PR から入ったコミットのハッシュを書いた行は、PR として読めず、日付・Author が空で PR もリンクにならないまま残っていた。どれも PR として読み、日付・リンク・Author を入れる

## v0.13.0 - 2026-10-20

### Added

- change-history: 主な変更の表の PR の列に、その PR を挙げた Decision log（`docs/decision-logs/`）へのリンクを、PR の後ろに添える（`[#12](…)、[DL-3](…)`）
  - 置き場所は `--decision-logs` で変えられる。複数のリポジトリを中央にまとめるときは添えない
- change-history: 一覧（`repos.txt`）にした複数のリポジトリの年表を、1 つのリポジトリ（中央のリポジトリ）にまとめて作る `build_many.py` を足した。各リポジトリは `.cache/change-history/` に bare のクローン（`--filter=blob:none`）を作って取り直し、`docs/change-history/<owner>/<repo>/` に 1 つのときと同じ形の年表を、`docs/change-history/README.md` に年ごとのリポジトリ別の要点と月 × リポジトリの件数の表を書く。手順は `skills/change-history/references/many-repos.md`。いまのリポジトリを対象にする使い方は変わらない
- change-history: `build_history.py` に、いまのディレクトリでないリポジトリを読む `--repo` と、コミットの件名・本文と変えたファイルを出す `--show` を足した（author の名前とメールは出さない）
- change-history: 月ごとの主な変更の表を書くサブエージェント `change-history-writer` を足した。12 か月ずつの回に分けて並べて呼び、書き手は月のファイルだけを書いて要約の 1 文を返す（年表にはメインの会話が入れる）。Kiro では、`--list` と `git show` を確認なしで通し、書き込みを `docs/change-history/*.md` に限る
- change-history: 書き手は月のファイルを相対パスのまま読んでから書き、読み直して確かめる（長い絶対パスを写し間違えて別の場所に書き、「書いた」と返すことがあった）。作り直しのたびに「主な変更をまだ書いていない月」を出し、メインの会話はその月だけ書き手に頼み直す

### Changed

- change-history: 書き手（`change-history-writer`）は、変えたファイルを `git show --stat` ではなく `build_history.py --show` で見る。`--repo` を受け取ったら `--list` と `--show` に付ける。Kiro の書き手は `docs/change-history/<owner>/<repo>/*.md` にも確認なしで書ける
- change-history: 月の主な変更と年の要点を分類（機能改善・運用改善・バグ対応）に分けず、月は日付の順の 1 つの表、年は「- 」の行にする
  - 前の形の分類の見出しと説明の文は、次に作り直すときにスクリプトが外し、月の表は 1 つにまとめ直す
- change-history: GitHub から取った PR（作成者・PR を入れたコミット・タイトル）を `.git/decision-continuity-prs.json` に覚えておき、2 回目からは更新の新しい PR だけを取る。`--list`（書き手が月ごとに呼ぶ）は問い合わせず、覚えておいた分を使う。PR が数万件のリポジトリで、作り直しや書き手のたびに全部の PR を取り直していた
- change-history: 件名に PR の番号がないコミット（Rebase and merge など）も、GitHub の PR を入れたコミットから PR の番号とタイトルを付ける
- change-history: `--until YYYY-MM` で、書く月の終わりを決められる。年表には、その期間の月と、前から年表にある月を載せる
- change-history: `Merge pull request from GHSA-…` のような番号のないマージも、本文の 1 行目をタイトルにする
- change-history: 月の表の行を日付の順に並べる。書くもののない月は、理由を問わず `- 目立った変更なし（依存の更新のみ）` のように書ける（以前は取り込みとリリースの 3 通りだけ）
- change-history: メインの会話は `--list` を読まない（書き手が読む）と SKILL.md に書いた。本物のエージェントで回すと、メインも書き手も同じ月を読んでいた
- change-history: 1 行の PR の列は 5 件までにし、超える行を形の崩れとして知らせる。同じ種類の変更が多いときは、代表を書いて件数を概要に書く（翻訳 98 件を 1 行に並べて、表が読めなくなっていた）。文書・翻訳・CI は運用改善と書き手の決まりに書いた
- change-history: `gh` で PR の作成者を取れないとき、フォークからのマージの件名（`Merge pull request #12 from alice/fix`）から Author を取るようにした。同じメールの PR を通さない変更にも使う。前に `—` と書いた Author は、取れるようになった名前に替わる
- change-history: 年表の件数を、PR の中のコミットを数えず、保守ブランチ（`Merge branch '8.1.x'` など）でマージされてから取り込まれた PR と直接のコミットまで数える形にした。中で別の PR をマージした PR は、その PR も数える。ブランチ間のマージは元のブランチで数える（pallets/click の 2023-07 は 7 件と出ていたが、実際は 32 件）
- change-history: 変更のなかった月も年表に `| 2024-01〜2024-02 | 0 | 変更なし |` の行で載せ、空いた期間が分かるようにした（続いた月は 1 行。月のファイルは作らない）。変更のなかった年は、年の要点を「変更なし」にする
- change-history: 依存の更新（`Bump requests from 2.31 to 2.32`・`build(deps): …`・`chore(deps): …`・`Update dependency …`・`[pre-commit.ci] pre-commit autoupdate`）に「（依存の更新）」の印を付ける。依存の更新・リリース・ブランチ間の取り込みだけの終わった月は、スクリプトが `- 目立った変更なし（依存の更新のみ）` のように書き、書き手を呼ばない
- change-history: `--list` は、1 コミットだけの PR の中のコミットを、マージの行と同じタイトルならもう出さない（pallets/click で字下げした行の 2 割がこれだった）

### Fixed

- change-history: その月の変更にない PR を書いた行や、決まりにない分類の見出しの下の行は、Author が空で PR もリンクにならないまま残っていた。全部の月の変更から探して日付・リンク・Author を入れ（どこにもない PR も、リンクと GitHub から取れた Author は入れる）、崩れとしては今までどおり知らせる
- change-history: PR の列に同じ PR を 2 度書くと、後ろの読めない参照が消えていた。どこにもないコミットのハッシュは、作り直すたびに 7 文字に切り詰められ、リンク先まで変わっていた

## v0.12.0 - 2026-10-19

### Changed

- BREAKING: change-history の月の主な変更の分類を、年表と同じ機能改善・運用改善・バグ対応の 3 つにした
  - 以前の 11 種（`security`・`reliability` など）で書いた月の主な変更は、形の崩れとして出るので書き直す
  - 目立った不具合の修正は `バグ対応` に書く（依存の更新や小さな修正は今までどおり書かない）
  - decision-log の分類は 11 種のまま

### Fixed

- change-history: `--since` を付けると、それより前の月の年表の行と要約が消えていた。`--since` は書き直す月だけを絞り、年表は全部の月から作る。`--list` は `--since` に関わらずその月を出す
- change-history: 月はブランチに入った日（コミットの日）で分ける。rebase や cherry-pick で入った変更が、書いた日の月に出ていた
- change-history: `gh` が使えるかどうかで `--check` の結果が変わっていた。GitHub から Author が取れないときは、表に書いてある Author を残す
- change-history: 読めない前の形の行（`- 概要（#99）`）が表を崩していた。表の行にして「この月の変更にない」と知らせる
- change-history: コミットのないリポジトリで git のエラーを出して止まっていた
- decision-log: 調べ役が読んでいないブランチからのマージの中の PR を拾うコマンドの範囲が誤っていて、何も拾えていなかった（`<コミット>^1..<コミット>^2` に直した）
- インストール：前の版で消えたサブエージェントが、入れ先に残らないようにした

## v0.11.3 - 2026-10-19

### Changed

- change-history: `gh` が使えれば、`--github` を付けなくても Author を GitHub の PR の作成者にする。問い合わせを止めるなら `--no-github`。`gh` がないときは黙ってメールから取り、`gh` が失敗したときは理由を出す
- change-history: PR の作成者はページを数えて 100 件ずつ取る（`--paginate` が次のページに使う `repositories/<ID>/…` の形を通さない中継があったため）。途中で失敗しても、取れた分は使う

## v0.11.2 - 2026-10-19

### Changed

- change-history: `--list` は、マージコミットの下に、取り込んだ側のコミット（PR の中のコミットや、`release/1.2` などの読んでいないブランチでマージされた PR）を字下げして出す。主な変更の表は、その中の PR やコミットを指してよい（日付は読んだブランチに入った日）
- decision-log: 調べ役は、読んでいないブランチからのマージ（`Merge branch 'release/1.2'` など）の中の PR も候補にする
- change-history: `--github` を付けると、Author を GitHub の PR の作成者にする（`gh api` で閉じた PR を 100 件ずつ取る。読むだけ）。取れない変更は、今までどおり noreply のメール（`.mailmap` を通す）から取る

## v0.11.1 - 2026-10-19

### Changed

- change-history: Author のメールを git の `.mailmap` に通すようにした。社内のメールを noreply のメール（`1+alice@users.noreply.github.com`）に対応させれば、アカウント名が出る

## v0.11.0 - 2026-10-19

### Changed

- BREAKING: change-history の月のファイルを、主な変更の表だけにした
  - 主な変更は分類ごとの `| 日付 | 概要 | PR | Author |` の表になる。AI が書くのは概要と PR だけで、日付・Author・PR のリンクはスクリプトがその月の変更から埋める
  - Author は GitHub のアカウント名（noreply のメールから取る `@alice`）。取れなければ `—`。名前（git の author 名）は今までどおり出さない
  - 分類の見出しの直下に、分類の説明（format.md の表の「見出し：中身」）をスクリプトが入れる。年の要点には 3 つの分類の説明を入れる
  - 月のファイルの「## 一覧」と、見出しの直下の件数の文、`README.md` の見出しの直下の文をなくした。全変更は `build_history.py <フォルダー> --list YYYY-MM` で出す
  - 以前の `- 概要（#12）` の行は、作り直すと表の行に移る
- BREAKING: change-history の年表（`README.md` の年の要点）の分類を、機能改善・運用改善・バグ対応の 3 つにした
  - 月の主な変更の分類は、今までどおり decision-log と同じ 11 種
  - 以前の分類で書いた年の要点は、形の崩れとして出るので書き直す
- change-history: `README.md` の表の「主な変更」は、その月の主な変更をまとめた要約の 1 文にした（人か AI が書き、作り直しても残る）。以前は表の 1 行目を写していた

## v0.10.3 - 2026-10-19

### Fixed

- decision-log: 大きな PR の扱いを直した
  - 調べ役は大きさを範囲で絞らずに、ファイルの数と行の数で測る。少ないファイルで何千行も変える PR や、範囲の外で大きい PR にも印が付く
  - 読み手は行のコメントと issue のコメントを `--paginate` で全部読む（30 件で切れていた）。Kiro の読み手の許可に `gh api repos/… --paginate` を足した
  - 読み手は `gh pr view` で変えたファイルの一覧を取らず、`git show` で見る。コメントが多いときは、決める言葉のあるものから読む

## v0.10.2 - 2026-10-19

### Fixed

- decision-log: 大きな PR（30 ファイルか 1000 行を超えるもの）で読み手が途中で止まらないようにした
  - 調べ役が大きな PR に印を付け、読み手 1 つに 1 件だけ渡す
  - 読み手は差分を一度に出さず、置き場所ごとに判断に当たるファイルから読み、読まなかったものを「読み残し」として返す

## v0.10.1 - 2026-10-19

### Changed

- decision-log: 候補を大事なものから 20 件で切らず、大事な順に 20 件ずつの回に分けて、全部の回を終えるまで読んで書くようにした。読み手（`decision-log-reader`）1 つに渡すのは 5 件までで、多い分類は分ける。Decision log は 1 つずつ、形の節を全部埋めてから次へ進み、数が多くても短くしたり「ほか N 件」で省いたりしない。途中で止まったら、報告に次の回を書く

## v0.10.0 - 2026-10-19

### Added

- change-history: `build_history.py` が、AI か人が書く月の主な変更と年の要点の形を確かめるようにした。`### <分類>`（decision-log と同じ 11 種、同じ分類は 1 度）の下に「- 」の行を書き、月の行の末尾には PR かコミット、年の行の末尾には `（YYYY-MM）` か `（YYYY-MM〜YYYY-MM）` を書く。`5 月`・`05-02` のような略した日付は書かない。崩れていれば、ファイルと行と中身を出し、作り直しでも `--check` でも終了コード 1 を返す。分類の見出しのない以前の要点は、崩れとして出るので書き直す

## v0.9.1 - 2026-10-19

### Changed

- decision-log: 版を上げるだけの定型のリリース（`Release v1.2.0`・`Bump version to 1.2.0`・`chore(release): 1.2.0`・`v1.2.0` の形の件名）を、change-history と同じく書かないようにした。`decision-log-planner` は、版の番号の書き換えが設定ファイルの洗い出しに当たっても候補から落とす
- change-history: 月の主な変更と年の要点を、3〜5 行に限らず、分類ごとの `### <分類>` の下に書くようにした。分類は decision-log と同じ 11 種（`architecture`・`data`・`security`・`privacy`・`compatibility`・`reliability`・`release`・`engineering`・`cost`・`product`・`other`）で、行のある分類だけを書く。いちばん大事な変更を最初の分類の 1 行目に書き、`README.md` の表に入る

## v0.9.0 - 2026-10-19

### Changed

- change-history: 既定で、長く続くブランチ（`main`・`master`・`develop`・`development`・`dev`・`production`。`origin/` にあればそちら、なければ手元のもの）を全部読むようにした。開発の本流（develop）への機能の修正と、本番の適用先（main）へのリリースや緊急の修正の両方が一覧に入る。どちらにも入ったコミットは 1 件にし、行の末尾に入ったブランチを書く。ブランチ間のマージには「（develop から取り込み）」の印を付け、主な変更に書かない。`--branch` で読むブランチを指定でき、読んだブランチは索引に出る
- decision-log: 調べ役（`decision-log-planner`）が、長く続くブランチをそれぞれ読み、ブランチ間のマージではなく中身の PR を候補にするようにした
- BREAKING: change-history: 年表の `timeline.md` をやめ、索引の `README.md` が年表を兼ねるようにした。年ごとの要点と、月ごとの件数・主な変更の 1 行目（まだなら「まだ」）を並べる。以前の `timeline.md` は、次に `build_history.py` を回したとき、年の要点を `README.md` に移して消す。`timeline.md` へのリンクは `README.md` に直す
- change-history: 日付を `YYYY-MM-DD`、月を `YYYY-MM` にそろえた。一覧の行は `- 2024-05-02 …`、表の月は `[2024-05](2024-05.md)`、年の要点の期間は `（2024-03〜2024-06）` と書く

## v0.8.1 - 2026-10-19

### Changed

- change-history: 索引（`README.md`）の表の列名を「主な変更」から「主な変更を書いたか」にした。中身は「あり／まだ」だけで、年表の「主な変更」（各月の 1 行目）と取り違えやすかったため。いまの索引は、次に `build_history.py` を回したときに作り直される
- change-history: 版を上げるだけの定型のリリース（`Release v1.2.0`・`Bump version to 1.2.0`・`chore(release): 1.2.0`・`v1.2.0`）に一覧で「（リリース）」の印を付け、月の主な変更に書かないようにした
- change-history: 一覧に作成者の名前を書き出さないようにした。主な変更と年の要点にも人の名前を書かない。いまの一覧は、次に `build_history.py` を回したときに作り直される

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
