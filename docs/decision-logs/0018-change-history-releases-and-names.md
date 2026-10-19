---
category: privacy
checked: 58ce5ad
---

# change-history の一覧から人の名前を外し、定型のリリースを主な変更に入れないことにした

## ステータス

Active：`build_history.py` は一覧に作成者を書き出さず、版を上げるだけのリリース（`Release v1.2.0`・`Bump version to 1.2.0`・`chore(release): 1.2.0`・`v1.2.0`）に「（リリース）」の印を付ける（`skills/change-history/scripts/build_history.py` の `RELEASE_RE`）。SKILL.md は、印の付いたものを主な変更に書かず、人の名前をどこにも書かないとする。

## 起きたこと

- 2026-10-19 一覧の各行から作成者（git の author 名。マージコミットは取り込んだ側の先頭のコミットの author）を外し、定型のリリースに「（リリース）」の印を付けた。SKILL.md に、印の付いたものを主な変更に書かないことと、人の名前を一覧・主な変更・年の要点に書かないことを足した（ブランチ change-history-release-names。作成 @MichinaoShimizu）

## 理由

記録あり：「定型的なリリースが主な変更内容として入らないようにしたい。個人名が出力されないようにしたい。」（@MichinaoShimizu、会話 2026-10-19）。

ほかの案：作成者を GitHub のアカウント名に変えて残す案は取らなかった（名前を出さないという求めに合わない）。リリースを一覧から消す案も取らなかった（一覧はマージされた全変更を並べるもので、件数が合わなくなる）。

## 分かっていないこと

- 人の名前を出さない理由は何か（公開・共有する先の都合か、評価に使われるのを避けるためか）。decision-log は人をアカウント名で書くので、そちらも同じにすべきか（@MichinaoShimizu に聞く）。
- PR やコミットのタイトルそのものに入った名前（`Revert "…" by alice` など）は残る。そこまで消す必要があるか（@MichinaoShimizu に聞く）。
- リリースの見分けは件名の形だけで決める。`Release automation for v2.0` のように版の番号を含む別の変更にも印が付きうる。実際のリポジトリで外れが出ないか。

## 追記 2026-10-19

- 2026-10-19 decision-log でも、版を上げるだけの定型のリリース（`Release v1.2.0`・`Bump version to 1.2.0`・`chore(release): 1.2.0`・`v1.2.0` の形の件名）を書かず、`decision-log-planner` の候補からも落とすことにした。版の番号の書き換えは設定ファイルの洗い出しに当たるが、それでも落とす。4 つの形が change-history の `build_history.py` と 2 つの SKILL.md・planner で揃うことは `tests/test_docs.py` が確かめる（ブランチ change-history-categories。作成 @MichinaoShimizu）。理由：「定型的なリリース、バージョンアップは年表に書かない点はデシジョンログと同じにしたい」（@MichinaoShimizu、会話 2026-10-19）

## 追記 2026-10-19（Author の列）

- 2026-10-19 change-history の主な変更を表にし、Author の列にだけ GitHub のアカウント名（noreply のメールから取る `@alice`。取れなければ `—`）を出すことにした。名前（git の author 名）は今までどおり出さない（DL-23）（ブランチ change-history-table。作成 @MichinaoShimizu）。理由：表に Author を入れたいという求めに、この判断と食い違うことを示し、@MichinaoShimizu がアカウント名で出す案を選んだ（会話 2026-10-19）
Superseded：`build_history.py` は主な変更の表の Author の列にアカウント名を書く（`skills/change-history/scripts/build_history.py` の `account`）。SKILL.md の決まり 5 は、人をアカウント名で Author の列にだけ書くとする
