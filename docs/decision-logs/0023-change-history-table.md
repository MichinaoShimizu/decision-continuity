---
category: product
checked: cfb2cf6
---

# change-history の月のファイルを主な変更の表だけにし、Author をアカウント名で出すことにした

## ステータス

Active：`build_history.py` は月のファイルに見出しと「## 主な変更」だけを書き、全変更は `--list YYYY-MM` で出す。主な変更は分類ごとの `| 日付 | 概要 | PR | Author |` の表で、日付・Author・PR のリンクと分類の説明をスクリプトが入れ、PR の列の参照がその月の変更にあるかを確かめる（`skills/change-history/scripts/build_history.py` の `tidy`・`problems`）。Author は GitHub の noreply のメールから取るアカウント名で、取れなければ `—`。

## 起きたこと

- 2026-10-19 月のファイルから「## 一覧」と見出しの直下の件数の文を、`README.md` から見出しの直下の文（件数と読んだブランチ）をなくした。全変更は `--list` で標準出力に出す。主な変更を「- 概要（#12）」の行から 4 列の表に変え、日付と Author をスクリプトが PR から埋め、以前の行は表に移す。分類の見出しの直下に、format.md の「見出し：中身」をスクリプトが入れる（年の要点も）。人の名前を出さない決まり（DL-18）を、Author の列にだけアカウント名を出す形に変えた（ブランチ change-history-table。作成 @MichinaoShimizu）

## 理由

記録あり：「年表、主な変更、だけでいいのでは？主な変更は表でいいのでは？（日付、概要、PR、Authorの。h1直下の文章は不要。カテゴリ直下には説明を」（@MichinaoShimizu、会話 2026-10-19）。DL-18 と食い違う Author の列は、アカウント名で出す・列を作らない・オプションで出す、の 3 案から @MichinaoShimizu がアカウント名で出すを選んだ。一覧は、消す・残すの 2 案から消すを選んだ。分類の説明は、format.md の定義を決まった文で入れる・その月の流れを AI が書く、の 2 案から決まった文を選んだ（会話 2026-10-19）。

ほかの案：Author に git の author 名を書く案は取らなかった（DL-18 で名前を出さないと決めたまま）。日付と Author を AI に書かせる案も取らなかった（推測が入りうる。PR から機械で決まる）。

## 分かっていないこと

- noreply のメールを使わないリポジトリでは、Author がほとんど `—` になる。アカウント名を `gh` で引く（ネットワークを使う）ことまでするか（@MichinaoShimizu に聞く）。
- PR を作った人として、マージコミットは取り込んだ側の先頭のコミット、squash はそのコミットの author を使う。PR を作った人と違うことがある（ほかの人のコミットを積んだ PR など）。
- 一覧をなくしたので、主な変更に入らなかった変更はファイルからは見えない。あとから全変更を見たい人がいるか。

## 追記 2026-10-19

- 2026-10-19 `README.md` の表の「主な変更」を、月の表の 1 行目を写すのをやめ、その月の主な変更をまとめた要約の 1 文を人か AI が書く形にした。作り直しても残り、月の主な変更を書いたのに要約がなければ形の崩れとして出す。目立った変更なしの月は、その文をスクリプトが入れる（ブランチ change-history-table。作成 @MichinaoShimizu）。理由：「Readmeの主な変更は、複数の主な変更がある場合も要約した文章にして」（@MichinaoShimizu、会話 2026-10-19）

## 追記 2026-10-19（.mailmap）

**分かった**（2026-10-19）：「noreply のメールを使わないリポジトリでは、Author がほとんど `—` になる。アカウント名を `gh` で引く（ネットワークを使う）ことまでするか（@MichinaoShimizu に聞く）。」

`gh` は使わない。change-history は手元の git だけを読む作りのまま、Author のメールを git の `.mailmap` に通すようにした（`%ae` から `%aE` へ）。社内のメールを noreply のメールに対応させれば、アカウント名が出る（ブランチ open-items。作成 @MichinaoShimizu）。@MichinaoShimizu が「適切に対応」と Claude に任せ、ネットワークを使わない案を Claude が選んだ（会話 2026-10-19）
Superseded：`build_history.py` は Author を `.mailmap` を通したメール（`%aE`）から取る（`skills/change-history/scripts/build_history.py` の `first_parent`・`changes`）

## 追記 2026-10-19（PR の作成者）

- 2026-10-19 `--github` を付けたときだけ、Author を GitHub の PR の作成者にすることにした。`gh api --paginate repos/<owner>/<repo>/pulls?state=closed&per_page=100` で番号と作成者を取り、PR の番号がある変更（マージの中の PR も）に使う。取れない変更や `gh` が使えないときは、noreply のメール（`.mailmap` を通す）から取る（ブランチ pr-authors。作成 @MichinaoShimizu）。理由：社内のメールで commit するリポジトリでは Author がほとんど `—` になり、「Prの作成者をとればよいかと」（@MichinaoShimizu、会話 2026-10-19）。change-history は手元の git だけを読む作りだったので、ネットワークに出るのは `--github` のときだけにした（Claude の案）
Superseded：`build_history.py` は `--github` のとき `pr_authors` で PR の作成者を取り、`by_pr` で Author にする（`skills/change-history/scripts/build_history.py`）。SKILL.md は `gh` が使えれば毎回 `--github` を付けるとする

## 追記 2026-10-19（GitHub を既定に）

- 2026-10-19 `gh` が使えれば、`--github` を付けなくても PR の作成者を取ることにし、問い合わせを止める `--no-github` を足した。noreply のメール（`.mailmap` を通す）は、取れない変更の予備として残す。PR の作成者は `--paginate` をやめ、`&page=N` でページを数えて取り、途中で失敗しても取れた分を使う（ブランチ github-default。作成 @MichinaoShimizu）。理由：「No replay mail形式で取得する意味何」という問いに、noreply は予備にすぎず会社のリポジトリではほぼ当たらないと答え、GitHub を既定にする案に @MichinaoShimizu が「そうして」と答えた（会話 2026-10-19）。`--paginate` は、このセッションの中継が次のページの `repositories/<ID>/…` を 403 で止めたため、ページを数える形にした（Claude の判断。本物の `gh` で、このリポジトリの 112 件を 2 ページで取れた）
Superseded：`build_history.py` は `--no-github` でなければ `pr_authors` で PR の作成者を取る（`skills/change-history/scripts/build_history.py`）。SKILL.md は、`gh` があれば GitHub から取り、止めるなら `--no-github` とする

## 追記 2026-10-19（覚えておく・番号のないコミット・期間の終わり）

- 2026-10-19 GitHub から取った PR を `.git/decision-continuity-prs.json` に覚えておき、更新の新しい順に取って、全部を覚えている PR のページが来たら止めることにした。`--list` は問い合わせず、覚えておいた分を使う。件名に番号のないコミットは、PR を入れたコミット（`merge_commit_sha`）から PR の番号とタイトルを付ける。`--until` を足し、年表には期間の月と前から載っている月だけを載せる（ブランチ change-history-writer。作成 @MichinaoShimizu）。理由：「高精度でフォーマットに沿った可読性の高い変更履歴年表を高速で作成可能（リポジトリ問わず）」という目標（@MichinaoShimizu、2026-10-19）に向けて、Claude が flask（本流 2,280 件）で試した。本物のエージェントは「2023-01 から 2023-12」の終わりを指定できずに止まり、PR が多いリポジトリでは書き手が月ごとに全部の PR を取り直す作りだった（Claude の判断）
Superseded：`build_history.py` は `github_prs` で PR を覚えておいた分に足し、`by_pr` で番号のないコミットを PR に結びつける（`skills/change-history/scripts/build_history.py`）

## 追記 2026-10-19（フォークからのマージ）

- 2026-10-19 `gh` で取れない変更の Author に、フォークからのマージの件名（`Merge pull request #12 from alice/fix` の `alice`。origin の持ち主と違うときだけ）を使うことにした。そのマージの先頭のコミットのメールも覚え、同じメールで PR を通さない変更にも使う。同じリポジトリのブランチからのマージにも出るメール（メンテナーが別の人の PR に足したコミットなど）と、2 人以上に当たるメールは使わない。前に `—` と書いた行は、取れるようになった名前に替える（ブランチ change-history-writer。作成 @MichinaoShimizu）。理由：「高精度でフォーマットに沿った可読性の高い変更履歴年表を高速で作成可能（リポジトリ問わず）」という目標（@MichinaoShimizu、2026-10-19）に向けて、Claude が `gh` を使えない flask の 2023 年で試すと、41 行中 38 行の Author が `—` だった。フォークの持ち主を使うと 31 行に減った（Claude の判断）
Superseded：`build_history.py` は `credit` でフォークの持ち主を Author にし、`by_pr` で覚えたメールを使う（`skills/change-history/scripts/build_history.py`）

## 追記 2026-10-20（Decision log へのリンク）

- 2026-10-20 主な変更の表の PR の列に、その PR を挙げた（`PR #12` の文か、origin の `/pull/12` の URL がある）Decision log へのリンクを、PR の後ろに番号の順に添えることにした（`[#12](…)、[DL-3](../decision-logs/0003-x.md)`）。PR の列の参照の数には数えず、作り直すたびにスクリプトが入れ直す。置き場所は既定で `docs/decision-logs/`、`--decision-logs` で変える。`--repo`（中央にまとめるとき）では、クローンが git に入らないので、言われなければ添えない（ブランチ change-history-dl-links。作成 @MichinaoShimizu）。理由：年表のつなぎ先を PR から Decision log に変える案について、Claude は、置き換えると Decision log のない行が空になり、一次の出典の PR がなくなると答えた。@MichinaoShimizu が「置き換えずに、ある場合にはデシジョンログにもリンク貼る」と決めた（会話 2026-10-20）。年の要点ではなく月の表の PR の列に、新しい列を作らずに添えるのは Claude の判断（いまの 4 列の表と形の検査をそのまま使える）
Superseded：`build_history.py` は `decision_logs` で PR を挙げた Decision log を集め、`row` で PR の列の PR の後ろにリンクを添える（`skills/change-history/scripts/build_history.py`）
