# reverse-adr — 細かい監査の成果物

リポジトリ全体の監査や、主張ごとの証拠の一覧を頼まれたときだけ読む。ふつうの範囲を絞った起こし直しでは要らない。

## 置き場所

コードのリポジトリにはファイルを置かない。

| 成果物 | 置き場所 |
|---|---|
| 主張ごとの証拠（evidence matrix） | 各 Decision log の記録データの `claims` |
| 時系列と候補の一覧（ledger） | 報告に書く。残したいと頼まれたら、Decision logs に `[<リポジトリ名>] 監査 YYYY-MM-DD` として投稿する（`kind: audit`） |
| 広さと深さ、確かめた手順、残った穴 | 同上 |

## 主張の書き方

```yaml
claims:
  - id: C1                       # Decision log の中で一意。投稿後は番号を振り直さない
    statement: "<確かめられる主張を一つ>"
    status: historical-only      # verified | historical-only | untested | superseded | conflict | unknown
    historical: ["<PR やレビューのパーマリンク>"]
    current: ["<パス:行 @コミット>"]
    tests: []                    # [{test: "<パス::名前>", run: "<実行のリンクかコマンドと結果>", revision: "<コミット>"}]
    notes: "いまの振る舞いは見ていない"
```

主張を訂正するときは本文を書き換えず、コメントで「C1 の状態を conflict に：理由、証拠」と足す。リンクは開いて確かめたものだけを書く。秘密情報や個人情報を写さない。
