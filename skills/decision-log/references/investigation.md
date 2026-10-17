# 手順 0〜3：範囲を決め、候補を読み、確かめ、振り分ける（decision-log）

## 0. 範囲と既存の記録

1. リポジトリ名（`git remote get-url origin` の末尾）、基準のコミット（`git rev-parse HEAD`）、範囲を決める。
2. 既存の決定と Decision log の、探し方の行だけを読む（`grep -H -E '^(category|repos|paths|keywords):' <置き場所>/*.md`）。全文は、手順 1 で候補と重なったものだけ読む。索引の `README.md` は参考にとどめる。
3. 履歴の一覧を手元で 1 回で取る。`TZ=Asia/Tokyo git log --first-parent --date=short-local --format='@@ %h %ad %s' --name-only [-- <scope のパス>]`。日付はすべて JST（日本時間）の YYYY-MM-DD で書く。PR の `mergedAt` などは UTC なので、9 時間足して JST の日付にする（例：`gh pr view 101 --json mergedAt --jq '.mergedAt | fromdate + 32400 | strftime("%Y-%m-%d")'`）。メッセージの `(#123)` や `Merge pull request #123` で PR の番号に結びつける。マージコミットの件名はブランチ名なので（`Merge pull request #12 from x/fix-typo`）、`git log --first-parent --merges --format='@@ %h %b' [-- <scope のパス>]` も取り、本文の 1 行目を PR のタイトルとして読む。浅いクローンなら先に `git fetch --unshallow`。できなければ、見えた範囲を報告に書く。
4. マージされた変更を全部数え、総数とどこまで見たかを記録する。

## 1. 候補を見つける

タイトルと変更ファイルだけでは、名前と中身が違う変更（「fix typo」でタイムアウトを変えたもの）や、`settings.py`・`constants.ts` の中の値の変更を見落とす。次の 2 つを合わせて候補にする。

1. **一覧から**：タイトルと変更ファイルで、各変更を「分類」に当てはめる。手がかりはファイルの場所である（例：`migrations/` → `data`、`auth` → `security`、`openapi` → `compatibility`、`timeout`・`retry` → `reliability`、デプロイ・`monitoring`・`alerts` → `release`、`.github/workflows` のテストや lint・`.eslintrc` → `engineering`、`terraform` のインスタンスの種類・サンプリング → `cost`）。
2. **差分から**：全件の差分を手元の git で 1 回洗う。`git log --first-parent -i -G '<言葉>' --format='%h' -- <scope のパス（なければ .）> ':(exclude)*lock*' ':(exclude)*.snap'`。lockfile とスナップショットは、依存の更新が当たり続けるので外す。`<言葉>` は次をつないだ正規表現にする。
   - 既定：`timeout|retr(y|ies)|limit|max_|ttl|expire|auth|permission|role|token|secret|encrypt|signature|hmac|verify|email|phone|schema|migrat|deprecat|feature_?flag|instance_type|sampling|sample_rate`
   - 定数・設定の値の変更：`^[A-Z][A-Z0-9_]{2,} *[:=]`
   - 手順 0 で読んだ既存の記録の `keywords`

依存の更新、見た目の変更、ふつうのバグ修正は落とす。ただし、落とすのは 2 に当たらなかったものだけにする。タイトルだけで落とさない。

候補を、大事なもの、2 に当たったのにタイトルからは分からないもの、戻されたもの（`Revert`）、あいまいなもの、議論があったものの順に並べ、上から `depth` 件だけ本文とレビューをまとめて取る。`depth` の外に残った候補は、分類ごとの数と番号を報告に書く。

- GitHub：`for n in 101 117; do gh pr view $n --json number,title,body,author,createdAt,mergedAt,mergedBy,url,reviews,comments,files; done`。多いときは `gh api graphql` で 1 回に 20〜50 件。`gh` がなければ MCP ツールか REST API。
- GitLab：`glab mr view <番号>` を同じようにループする。
- どちらも使えない：git の一覧と `git show` だけで進める。履歴の証拠はコミットメッセージだけになり、レビューは見ていないと書く。
- issue とリリースは、候補の本文から参照されているものだけを開く。

差分は先に `git show --stat <コミット>` を見て、当たるファイルだけ `git show <コミット> -- <パス>` で読む。lockfile、生成物、スナップショットは読まない。

一つの流れの変更は 1 つの Decision log にまとめ、別の判断は分ける。PR ごとに作らない。理由が分からない大事な変更も Decision log にし、理由は「不明」のまま問いを残す。推測は「推測：」と明記して書く。

## サブエージェントに分ける

読む候補が 5 件を超えたとき（SKILL.md の「手順」）、分類ごとに 1 つ、同時に呼ぶ。

- `.kiro/agents/decision-log-reader.json` か `.kiro/agents/decision-log-reader.md`（Kiro）か `.claude/agents/decision-log-reader.md`（Claude Code）があるときだけ、名前で指定して呼ぶ。例：「decision-log-reader サブエージェントで、reliability の PR #101、#117 を基準のコミット abc1234 で読んで」。
- ないとき、または名前で呼んで失敗したとき（Kiro は登録のない名前を既定に切り替えない）は、既定のサブエージェントにリポジトリ・基準のコミット・分類・PR の番号を渡し、「起きたこと」「理由」「関わった人」の行、決定の言葉、問い、keywords の候補を返させる。ファイルは書かせない。
- 返ってきたものの重なりを除き、自分で Decision log にまとめる。

## 2. 主張ごとに確かめる

主張ごとに 2 つの証拠を別々に持つ。**履歴**（日付のある PR、issue、差分、レビュー、コミット）と、**現在**（基準のコミットのコード、設定、ドキュメント）である。履歴のない主張は書かない。テストの成否は調べない。

| 状態 | 条件 |
|---|---|
| いまも同じ | 履歴の変更が、基準のコミットにもそのまま残っている |
| 置き換え済み | 後の変更で置き換わった |
| 競合 | 証拠どうし、または有効な決定と矛盾する |
| 履歴のみ | 履歴はあるが、基準のコミットで該当するコードが見つからない |

**有効な決定といまのコードが矛盾していたら、「競合」にして報告の先頭に出す。**どちらが正しいかは決めない。

## 3. 振り分ける

| 見つけたもの | 行き先 |
|---|---|
| 変更は分かるが、決定の言葉も決めた人もない | 新しい Decision log |
| 既存の Decision log と同じ流れの、後の変更（戻した、広げた） | その Decision log への追記 |
| 決定の言葉と決めた人が PR やレビューにある | 報告の「決定の候補」と、Decision log の出典 |
| 大事な変更なのに理由が不明 | 「分かっていないこと」に、知っていそうな人への問いを書く |
| 有効な決定と競合する | 報告の先頭。決定には追記しない |

決定の候補では、決めた人を記録に書かれた役割で書き、なければ「未確認」とする。承認が見えなければ「承認は見えない」と書くが、候補からは外さない。Decision log を決定に書き換えない。
