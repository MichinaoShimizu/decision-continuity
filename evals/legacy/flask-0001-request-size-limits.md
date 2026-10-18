---
category: reliability
checked: d086db85
---

# リクエストの大きさの上限（MAX_CONTENT_LENGTH、MAX_FORM_MEMORY_SIZE、MAX_FORM_PARTS）

## ステータス

Active：3 つの設定とも config にある。`MAX_CONTENT_LENGTH` は `None`（上限なし）、`MAX_FORM_MEMORY_SIZE` は 500_000、`MAX_FORM_PARTS` は 1_000（[app.py:225-227][c-app]）。3 つともリクエストごとに上書きできる（[wrappers.py:55-143][c-wrap]）。

## 起きたこと

- 2010-07-14 `MAX_CONTENT_LENGTH` を config に新設。既定は `None`。読み取り専用の `Request.max_content_length` が config を返し、超えると 413（実際に弾くのは Werkzeug）（[b1790cca][b1790cca]。作成・コミット Armin Ronacher（git の author・committer）。レビューの記録なし）
- 2010-07-15 アップロードの文書を、`Request` をサブクラス化して `max_form_memory_size = 16 * 1024 * 1024` を置く方法から、`app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024` に差し替え、Flask-Uploads を案内（[54ebd88f][54ebd88f]。同じ人）
- 2019-08-24 文書の例の値が `16 * 1000 * 1000` になった（[db061cf7][db061cf7]。PR #3332 のマージ。誰がどう変えたかは未確認）
- 2024-11-02 `MAX_FORM_MEMORY_SIZE`（500_000）と `MAX_FORM_PARTS`（1_000）を config に新設。3 つとも `Request` の setter でリクエストごとに上書き可能にし、優先順位はリクエストの値、config、（`current_app` がなければ）Werkzeug の値の順。`MAX_CONTENT_LENGTH` の既定 `None` は変えず、以前の読み取り専用から設定可能になった。セキュリティの文書に "Resource Use" の節を追加（[PR #5626][pr5626]。作成 @davidism、マージは GitHub 経由で個人は git から不明、承認の記録なし）

## 理由

記録あり：リソース上限をリクエストごとに設定できるようにし、config を足し、セキュリティのページに文書を足す（CHANGES.rst の項目。`:issue:5625` を参照）。docs/web-security.rst は DoS 対策として説明し、1000 パート × 500kB でフォームが最大約 500MB を占めうるという見積もりを載せ、アプリやビューごとに適切な値に設定するよう促している。2010 年の変更は、受信データ量を制限できるようにするため（CHANGES と docs/config.rst）。いずれも、既定値を選んだ根拠は書かれていない。コミット題名以外の動機や議論は不明。

## 分かっていないこと

- なぜ 500_000 と 1_000 を既定にしたか。Flask 側に既定値を持たせたのは意図か（@davidism に聞く。issue #5625 は未確認）
- リクエスト側の値が `None` のときは「未設定」として config に戻るため、リクエスト単位で「無制限」にはできない。これは意図した仕様か（@davidism に聞く）
- 2010-07-15 の文書変更は、対象が違う（フォームのメモリ量とリクエスト全体の長さ）ことを承知のうえか（Armin Ronacher に聞く）
- 文書の例が 16 MiB から 16 MB（1000 単位）に変わった経緯（PR #3332 は未確認）
- 食い違い：docs/config.rst:346 は属性名を `Request.max_form_memory_parts` と書くが、実際は `max_form_memory_size`（HEAD でも未修正）。docs/config.rst の `MAX_CONTENT_LENGTH` の `versionadded` は 2010 年のコミットで一時「キー名」になっていたが、HEAD では `0.6`

[b1790cca]: <https://github.com/pallets/flask/commit/b1790cca>
[54ebd88f]: <https://github.com/pallets/flask/commit/54ebd88f>
[db061cf7]: <https://github.com/pallets/flask/commit/db061cf7>
[pr5626]: <https://github.com/pallets/flask/pull/5626>
[c-app]: <https://github.com/pallets/flask/blob/d086db85/src/flask/app.py#L225>
[c-wrap]: <https://github.com/pallets/flask/blob/d086db85/src/flask/wrappers.py#L55>
