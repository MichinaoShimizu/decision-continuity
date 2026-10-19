---
category: product
checked: 51b209e
---

# change-history の主な変更を、行の数を決めずに分類ごとに書くことにした

## ステータス

Active：change-history の SKILL.md は、月の主な変更と年の要点を `### <分類>` の下に書き、行の数を決めない。分類は decision-log と同じ 11 種で、行のある分類だけを書く（`skills/change-history/SKILL.md` の手順 2・4）。`build_history.py` は中身をそのまま残し、表には最初の行を入れる。2 つのスキルの分類が揃っていることは `tests/test_docs.py` が確かめる。

## 起きたこと

- 2026-10-19 月の主な変更と年の要点を「3〜5 行」から、行の数を決めない分類ごとの書き方に変えた。分類は decision-log の `format.md` の 11 種と同じにした（ブランチ change-history-categories。作成 @MichinaoShimizu）

## 理由

記録あり：「主な変更は3から5行である必要はない。カテゴリ別にだしたい」（@MichinaoShimizu、会話 2026-10-19）。分類は、decision-log と同じもの・機能や修正で分けるもの・置き場所で分けるものの 3 案から、@MichinaoShimizu が decision-log と同じものを選んだ（会話 2026-10-19）。2 つのスキルで分類がそろい、「なぜ」まで要るテーマを同じ分類のまま decision-log に回せる。

## 分かっていないこと

- 行の数を決めないと、変更の多い月で主な変更が長くなりすぎないか。実際のリポジトリで確かめる。

## 追記 2026-10-19（年表の分類）

- 2026-10-19 年表（`README.md` の年の要点）の分類を、decision-log と同じ 11 種から、機能改善・運用改善・バグ対応の 3 つに変えた。見出しの直下には、それぞれの説明（`YEAR_DESCRIPTIONS`）をスクリプトが入れる。月の主な変更は 11 種のまま（ブランチ change-history-table。作成 @MichinaoShimizu）。理由：「年表のカテゴライズは、機能改善、運用改善、バグ対応にしようか」（@MichinaoShimizu、会話 2026-10-19）。3 つの説明の文は Claude の案で、@MichinaoShimizu が決めた文ではない
Superseded：`build_history.py` は年の要点の分類を `YEAR_DESCRIPTIONS` の 3 つで確かめ、月の主な変更は `CATEGORIES` の 11 種で確かめる（`skills/change-history/scripts/build_history.py` の `problems`）

## 追記 2026-10-19（年表の分類の説明）

**分かった**（2026-10-19）：「3 つの説明の文」

機能改善・運用改善・バグ対応の説明の文は、@MichinaoShimizu が「適切に対応」と Claude に任せ、Claude の案のまま採用した（会話 2026-10-19）

## 追記 2026-10-19（月の分類）

- 2026-10-19 月の主な変更の分類も、decision-log と同じ 11 種から、年表と同じ機能改善・運用改善・バグ対応の 3 つに変えた。目立った不具合の修正は `バグ対応` に書く。decision-log の分類は 11 種のまま（ブランチ month-categories。作成 @MichinaoShimizu）。理由：「年表の各月毎のファイルも、機能改善、運用改善、バグ解消に分類したい」（@MichinaoShimizu、会話 2026-10-19）。名前は年表で使っていた「バグ対応」に揃えた（Claude の判断。「バグ解消」にするかは @MichinaoShimizu に聞く）。途中で「やっぱりカテゴリは一般的なCHANGELOやリリースノートに登場する分類が良いかな」として Keep a Changelog の 6 つ（`Added`・`Changed`・`Deprecated`・`Removed`・`Fixed`・`Security`）を試したが、「いや、やっぱり機能改善・運用改善・バグ対応の方がわかりやすいか」で 3 つに戻した（@MichinaoShimizu、会話 2026-10-19）。互換を壊す変更を行の頭の `BREAKING:` で示す案は Claude が挙げただけで、入れていない。最初に 11 種を選んだ理由（「なぜ」まで要るテーマを同じ分類のまま decision-log に回せる）は、この変更で失われる
Superseded：`build_history.py` は月と年の両方を `DESCRIPTIONS` の 3 つで確かめる（`skills/change-history/scripts/build_history.py`）。SKILL.md の手順 2 は、分類を機能改善・運用改善・バグ対応の 3 つとする
