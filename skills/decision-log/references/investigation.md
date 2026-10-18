# 手順 0〜3：範囲を決め、候補を読み、確かめ、振り分ける（decision-log）

## サブエージェントに任せる

調べ役 `decision-log-planner` と読み手 `decision-log-reader` が入っていれば（`.claude/agents/`、`.kiro/agents/` に `.md` か `.json`、Claude Code のプラグインなら `decision-continuity:` を前に付けた名前）、名前で指定して任せる。手順は各サブエージェントの定義にあり、読むコマンドはその許可で確認なしに通る。

1. 自分で読むのは、既存の Decision log の `category` と `keywords` の行だけ（エージェントの読む・探す道具で `^(category|keywords):` を探す）。全文は候補と重なったものだけ読む。
2. planner に範囲・`depth`・時間帯・`keywords` を渡す。例：「decision-log-planner サブエージェントで、範囲 src/payment/、depth 20、keywords は MAX_RETRIES|webhook で洗って」。浅いクローンと返ってきたら `git fetch --unshallow` をしてから呼び直す。できなければ見えた範囲を報告に書く。
3. 返ってきた「分担」の分類ごとに reader を 1 つずつ、**1 回の応答でまとめて**呼ぶ（1 つずつ順に呼ばない）。件数が少なくても自分で読まない。Kiro は 1 回に 4 つまでなので、多ければ小さい分類をまとめる。例：「decision-log-reader サブエージェントで、reliability の PR #101、#117 を基準のコミット abc1234 で読んで」。結果は呼び出しの戻りで受け取り、`sleep` で待たない。
4. 戻りの重なりを除き、自分で Decision log にまとめる。planner の「広さ」「`depth` の外」「落としたもの」「注意」は報告に使う。

## 入っていないとき

名前で呼んで失敗したときも同じ（Kiro は知らない名前を既定に切り替えない）。自分か既定のサブエージェントで、同じことをする。コマンドの形は [commands.md](commands.md)。

1. **範囲**：リポジトリ名（`git remote get-url origin` の末尾）、基準のコミット（`git rev-parse HEAD`）。
2. **一覧**：`TZ=Asia/Tokyo git log --first-parent --date=short-local --format='@@ %h %ad %s' --name-only [-- <scope>]` を 1 回。マージコミットの件名はブランチ名なので、`git log --first-parent --merges --format='@@ %h %b' [-- <scope>]` の本文 1 行目をタイトルにする。`(#123)` や `Merge pull request #123` で PR に結びつける。マージされた変更の総数を数える。
3. **候補**：タイトルと変更ファイルで分類に当てはめ（[categories.md](categories.md)）、さらに差分を次の 3 つで別々に洗って合わせる。タイトルと中身が違う変更（「fix typo」でタイムアウトを変えた）を拾うため。lockfile とスナップショットは外す（`':(exclude)*lock*' ':(exclude)*.snap'`）。
   1. 言葉：`git log --first-parent -i -G '<言葉>' --format='%h' -- <scope か .>`。言葉は、既定：`timeout|retr(y|ies)|limit|max_|ttl|expire|auth|permission|role|token|secret|encrypt|signature|hmac|verify|email|phone|schema|migrat|deprecat|feature_?flag|instance_type|sampling|sample_rate` に `keywords` を足したもの。
   2. 定数・設定の値の変更：`^[A-Z][A-Z0-9_]{2,} *[:=]` を `-i` を付けずに `-G` で（1 とつなぐと `-i` が効いてしまう）。
   3. 設定ファイルの変更：`git log --first-parent --format='%h' -- '*.yml' '*.yaml' '*.toml' '*.ini' '*.properties' '*.env'`。

   言葉がほぼ全件に当たるなら（文書中心のリポジトリ）、言葉では並べない。依存の更新・見た目・ふつうのバグ修正は、2 に当たらなかったものだけ落とす。大事なもの、2 に当たったのにタイトルからは分からないもの、`Revert`、あいまいなものの順に並べ、上から `depth` 件を読む。残りは分類ごとの数と番号を報告に書く。
4. **読む**：PR ごとに `gh pr view <番号> --json number,title,body,author,createdAt,mergedAt,mergedBy,url,reviews,comments,files` と、行のコメント `gh api repos/<owner>/<repo>/pulls/<番号>/comments`。PR の中のコミットのメッセージ（`git log --format='%h %s%n%b' <c>^1..<c>`）、参照された issue（1 段だけ）も読む。差分は `git show --stat <c>` から当たるファイルだけ `git show <c> -- <パス>`。GitLab は `glab mr view`。どちらもなければ git だけで進め、「レビューは見ていない」と書く。`gh` で読めないリンク（Slack、Notion など）は開かず「元の場所」に「未読」と挙げ、作成者への問いを足す。

日付は JST の YYYY-MM-DD。API の時刻は UTC なので 9 時間足す。

## 2. 主張ごとに確かめる

主張ごとに **履歴**（日付のある PR・issue・差分・レビュー・コミット）と **現在**（基準のコミットのコード・設定・ドキュメント）を別々に持つ。履歴のない主張は書かない。テストの成否は調べない。状態は [writing.md](writing.md#書き方) の 3 つ。証拠どうしが食い違えば（履歴とコード、本文と差分）、**報告の先頭**に出し、どちらが正しいかは決めない。

一つの流れの変更は 1 つの Decision log にまとめ、別の判断は分ける。理由が分からない大事な変更も Decision log にし、理由は「不明」のまま問いを残す。

## 3. 振り分ける

| 見つけたもの | 行き先 |
|---|---|
| 変更は分かるが、決定の言葉も決めた人もない | 新しい Decision log |
| 既存の Decision log と同じ流れの後の変更 | その Decision log への追記 |
| 決定の言葉と決めた人が PR やレビューにある | 報告の「決定の候補」と、Decision log の出典 |
| 大事な変更なのに理由が不明 | 「分かっていないこと」に、知っていそうな人への問い |

決定の候補では、決めた人を記録にある役割で書き、なければ「未確認」。承認が見えなければ「承認は見えない」と書くが、候補からは外さない。Decision log を決定に書き換えない。
