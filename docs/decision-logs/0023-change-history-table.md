---
category: product
checked: 5101b9e
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
