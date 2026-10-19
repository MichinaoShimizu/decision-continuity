---
category: product
checked: eff793b
---

# 履歴を、1 つのブランチではなく長く続くブランチ全部から読むことにした

## ステータス

Active：change-history の `build_history.py` は、`--branch` を言わなければ `main`・`master`・`develop`・`development`・`dev`・`production`（`origin/` にあればそちら、なければ手元のもの）を全部読み、同じコミットを 1 件にし、ブランチ間のマージに「（<元> から取り込み）」の印を付ける（`skills/change-history/scripts/build_history.py` の `LONG_LIVED`・`changes`）。`decision-log-planner` も、同じ名前のブランチをそれぞれ読む。

## 起きたこと

- 2026-10-19 change-history と decision-log-planner が、いまのブランチ（`HEAD`）の `--first-parent` だけでなく、長く続くブランチそれぞれの `--first-parent` を読むようにした。手元のブランチは古いことがあるので `origin/` のものを先に使う。`--branch` を足し、索引に読んだブランチを書く（ブランチ change-history-branches。作成 @MichinaoShimizu）。DL-18 の「（リリース）」の印はそのまま使い、ブランチ間のマージにも主な変更に書かない印を足した

## 理由

記録あり：「開発本流ブランチ、本番適用ブランチで、機能修正とリリース作業に二分されるのが一般的。単一のブランチへのPRのみをみてしまい取りこぼすことないようにして」（@MichinaoShimizu、会話 2026-10-19）。`main` だけを `--first-parent` で読むと、develop に入った機能の PR がリリースのマージ 1 件に隠れ、develop だけを読むと main への緊急の修正が抜ける。

ほかの案：`--first-parent` をやめて全部のマージを読む案は取らなかった（作業ブランチの中のコミットまで並び、PR の単位が崩れる）。ブランチを人に毎回聞く案も取らなかった（既定で取りこぼさないことを求められた）。

## 分かっていないこと

- 名前の一覧に入らないブランチ（`staging`・`release/2.x`・`hotfix/*` を長く残す運用など）は、`--branch` で言わないと読まれない。ほかに足すべき名前があるか（@MichinaoShimizu に聞く）。
- リリースの PR を squash で main に入れる運用では、2 つ目の親がなく、ブランチ間のマージと見分けられない（件名が版の形なら「（リリース）」になる）。実際のリポジトリで外れが出ないか。

## 追記 2026-10-19（マージの中身）

- 2026-10-19 `--first-parent` だけでは、マージコミットの件名と変えたファイルしか見えず、PR の中のコミットや、読んでいないブランチ（`release/1.2` など）でマージされた PR が見えなかった。change-history の `--list` は、マージコミットの下に、取り込んだ側の `--first-parent` のコミットを字下げで出すようにし、主な変更の表はその中の PR やコミットを指せるようにした。読んだブランチどうしのマージの下には出さない（中身は元のブランチの行に出る）。decision-log の調べ役も、読んでいないブランチからのマージの中の PR を候補にする（ブランチ follow-merges。作成 @MichinaoShimizu）。理由：「マージコミットの件名からPRを追うようにしないと実際の改修内容は見えないよ」（@MichinaoShimizu、会話 2026-10-19）
Superseded：`build_history.py` の `inside` がマージコミットの `<1 つ目の親>..<2 つ目の親>` を `--first-parent` で読み、`--list` と表の参照に使う（`skills/change-history/scripts/build_history.py`）。`agents/claude/decision-log-planner.md` の手順 3 が、読んでいないブランチからのマージの中の PR を候補にする
