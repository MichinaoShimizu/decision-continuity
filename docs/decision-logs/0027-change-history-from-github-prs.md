---
category: architecture
checked: b0bc45e
---

# change-history を、手元の git の推測から、GitHub のマージ済み PR を事実として作る形に変えた

## ステータス

Active：`build_history.py` は、GitHub でデフォルトブランチ（`--branch` で言われたブランチ）にマージされた PR を `gh api` で取り、日付はマージの日、Author は PR の作成者、タイトルは PR のタイトルにする。PR を通さずにそのブランチへ入ったコミットは、手元の git の `--first-parent` から拾い、Author は GraphQL で GitHub のコミットのアカウントを取る（Rebase and merge のコミットは、GitHub が結びつける PR にまとめる）。取ったものは `.git/decision-continuity-prs.json` に覚え、`--check`・`--list` は問い合わせない。`gh` が使えない、または origin が GitHub でないときは止まる（`skills/change-history/scripts/build_history.py` の `changes`・`fetch_prs`・`fetch_commits`）。`build_many.py` は GitHub のリポジトリだけを受け付け、`--github-repo` を渡す。

## 起きたこと

- 2026-10-20 git の件名から PR の番号を拾い、メール・`.mailmap`・フォークの持ち主・覚えた PR から Author を当て、マージの中身や保守ブランチの取り込みまで数える作りをやめた。PR は GitHub のマージ済み PR から、直接のコミットは git から取る。`--no-github` をなくし、`--github-repo` を足した。年表の件数は、その月の PR と直接のコミットの数になった。書いてある Author を残す扱いもなくし、Author はいつも GitHub の値にした（ブランチ change-history-from-prs。作成 @MichinaoShimizu）
- 2026-10-20 書き手は表を書かず、`- #12、#13：概要` の行だけを書き、スクリプトが表にすることにした。Decision log へのリンクはやめた（DL-23 の追記）（ブランチ change-history-from-prs。作成 @MichinaoShimizu）。理由：この repo で作った年表を見て「使い勝手よくなった？」と聞かれ、Claude が、書き手が書いた表の行をスクリプトが読み直すところで今日の不具合が出ていたことを挙げ、直す案に @MichinaoShimizu が「はい」と答えた（会話 2026-10-20）

## 理由

記録あり：「この年表作り、そもそももっと簡単なことなんじゃないの？」という問いに、Claude は、ほしい表の日付・PR・Author は GitHub のマージ済み PR にそのまま入っていて、AI が要るのは主な変更を選んで概要を書くことだけなのに、「手元の git だけで読む」前提のために git から事実を推測で組み立て直していること、その前提は `gh` を既定で使うようにした時点でもう崩れていることを挙げた。@MichinaoShimizu が、`gh` が使えないリポジトリは「対象にしない」、PR を通さない直接のコミットは「入れる」と決めた（会話 2026-10-20）。

ほかの案：`gh` がないときに git から PR の番号だけを拾う予備の道を残す案は、対象にしないと決めたので取らなかった。表の行を AI に書かせず、選んだ PR の番号と概要だけを受け取ってスクリプトが表にする案は、はじめは取らなかったが、同じ日に取った（起きたことの 2 行目）。

## 分かっていないこと

- PR を通さない直接のコミットが何千とあるリポジトリでは、最初の作成で GraphQL を 50 件ずつ何十回も呼ぶ。実際のリポジトリで時間と GitHub の上限に収まるか。
- 保守ブランチ（`8.1.x` など）でマージされてからデフォルトブランチに取り込まれた PR は、その PR の base が保守ブランチなので、デフォルトブランチの年表には「（ブランチの取り込み）」の 1 件としてしか出ない。保守ブランチも `--branch` で読むべきリポジトリがあるか（@MichinaoShimizu に聞く）。
