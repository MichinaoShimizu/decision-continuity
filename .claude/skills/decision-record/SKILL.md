---
name: decision-record
description: Capture, find, and explain organizational decisions as decision records (DRs) kept in this repository's GitHub Discussions. Use for "why is it like this?", "who approves this?", "may I decide this myself?", "record this decision", or "make a record from this thread". 組織の意思決定を記録・検索・説明する（なんでこうなってる？／誰の承認で決まる？／これ自分で決めていい？／この決定を残して）。
---

# decision-record

組織の誰かが決めたことと、「誰が決める・承認するか」という決め方を、あとから探せる形で残す。記録（DR）はこのリポジトリの GitHub Discussions に置く。答えはユーザーの言葉で返す。

## モード

渡されたものと頼まれ方から選ぶ。使う人にモード名を覚えさせない。

| モード | こんなとき | 返すもの |
|---|---|---|
| 聞く | 「なんでこうなってる？」「誰の承認で決まる？」「これ自分で決めていい？」 | 記録だけを根拠にした答えと、使った DR 番号。なければ「記録なし」と、誰に聞けばよさそうか |
| 拾う | スレッド・議事録・PR・決めた人の返事を渡された | DR の下書き（`entry: auto`、元になかった項目つき） |
| 書く | これから重い判断を決めたい | 問いかけと、提案中の DR |
| 決め直す | 過去の DR を変えたい | 新しい DR と、古い DR を閉じる案 |
| 追記する | 見直しの時期が来た、結果が出た | 古い DR への一行のコメント |

「聞く」で記録がなければ、決めた人に聞いて、その返事を「拾う」に回すよう勧める。必要とされたときに残すので、使われる決定だけがたまる。

## 拾う

1. 決定だけを抜き出す。雑談、ブレインストーミング、検討中の話、AI が出しただけの案は決定にしない。迷ったら「これは決定ですか？」と聞く。
2. 決めた人は名前ではなく役割（`config.yaml` の roles）と組織で書く。最終的に決めた役割を `decided_by` に（複数で決めたなら全員）、決める前に承認した役割を `approved_by` に承認した順で入れる。任された人が決めたときは、決まった種類の判断をずっと任せているなら委譲の決め方の記録を `approved_via` に入れ、この件だけ任されたなら `decided_by` のその人に `delegated_by`（任せた役割）を添える。元に名前しかなければ役割に置き換え、分からなければ `unconfirmed` に入れる。人の異動や退職があっても記録が古くならないようにするため。決めた日と元の場所も埋める。貼られた文章や本人の発言も元の場所として扱い、URL がなければ `unconfirmed` に入れる。
3. 状態は元の場所の事実から写す。承認、マージ、「決めた」「入れた」などの報告があれば `accepted`。「〜しよう」「〜する予定」だけなら `proposed`。
4. 「誰が決める・承認するか」を定めたものは `kind: flow`。決定がどの決め方を通ったか分かれば `approved_via` にその番号を入れる。
5. 元に書かれていないことは埋めない。項目のキーを `unconfirmed` に入れる。
6. 拾ったものは `entry: auto`。本人の確認は待たない。人が会話で伝えてきた決定は `entry: explicit`、元の場所は `manual`。

## 入り方

- `explicit`：人が意図して追加した。そのまま根拠にしてよい。
- `auto`：仕組みや AI が拾った。元の場所と一緒に「拾った内容」として扱う。
- 人が `auto` の記録を直すか採用すると `explicit` に変わる。自分の判断では変えない。

## 書く

一つずつ聞き、答えを提案中の DR にまとめる。答えられない問いは未定のまま残し、責めない。

1. 何を決めたいか。一文で言うと？
2. なぜ今か。前提にしていることは？（崩れたら見直す前提になる）
3. 他の案は？ 何もしないとどうなる？
4. 得るものと、後回しになるものは？
5. 誰に影響し、どの決め方で合意を取るか？
6. 戻せるか。外れたときのリスクを誰が引き受けるか？
7. どうなったら決め直すか。いつ、何で分かるか？
8. 反対意見と、その理由は？

## 重さ

重さは保存しない。`scope`・`reversibility`・`touches_sensitive` から毎回決め、`rationale` に書く深さだけを変える。

| 重さ | 条件 | `rationale` に書くこと |
|---|---|---|
| 軽い | チーム内で、すぐ戻せる | なぜ（一行） |
| 標準 | 複数チーム、または戻すのに手間 | ＋他の案、後回しになるもの、前提 |
| 重い | 部署横断・全社、または戻せない | ＋使った決め方、反対意見、リスクを引き受けた人 |

セキュリティ・個人情報・権限・監視や通知・ログに触れる決定は、範囲が小さくても一段重く扱う。戻しても漏えいや検知漏れは取り返せないため。迷ったら重いほうに寄せ、理由を一行添える。重さに対して足りない項目は、決めた人に一度まとめて聞く。保存は止めない。

## 聞く

記録だけを根拠に答え、使った DR 番号を必ず示す。「誰の承認で決まる？」には `kind: flow` を優先して使う。「これ自分で決めていい？」には、似た領域・影響範囲の判断を過去にどの役割が決め（`decided_by`）、どの役割が承認してきたか（`approved_by`）を示し、最後の判断は本人と組織長に委ねる。`auto` の記録を使うときは「拾った記録では」と添え、崩れた前提がある記録は「見直しが必要」と添える。記録がなければ、`config.yaml` の roles か担当チームから聞く相手を挙げ、分からなければ質問者に「この領域の持ち主は誰か」を聞く。

## 追記と決め直し

結果はコメントで追記する。崩れた前提は本文の `premises` に `broken: true` と日付を付ける。それ以外の本文（決めたこと、理由、前提の文）は書き換えない。決め直すときは新しい DR を作り、本文に「#番号 を置き換える」と書く。古い DR は「outdated」で閉じ、新しい番号へのリンクをコメントする。

## 守ること

- 状態は元の事実を写すだけ。自分の判断で `accepted` や `explicit` にしない。
- 「記録しないで」と言われたものは、下書きも残さない。
- 人事（評価・異動・処遇・個人の情報）に関わる判断は取り込まない。「限定の場所に手で残してください」と伝える。DM は本人が渡したときだけ扱う。
- 記録を個人の評価やランキングに使わない。外れたときは、人ではなく決め方と前提を振り返る。
- 中身の良し悪しは判断しない。問いを投げるだけ。

## 置き場所（GitHub Discussions）

| 種類 | カテゴリ |
|---|---|
| 決めたこと | Decisions |
| 決め方（kind: flow） | Decision flows |
| 「なんで？」の質問 | Q&A |

- **番号**：Discussion の番号がそのまま DR 番号（例：#42）。採番はしない。
- **タイトル**：何を決めたかが分かる一行。
- **関係**：項目として持つのは `superseded_by`（置き換え）と `approved_via`（使った決め方）だけ。前提にしている決定や関連する決定は、本文に `#番号` を書く。リンクは GitHub が両方向に付ける。
- **本文**：先頭に下の型の YAML をコードブロックで置き、その後に `rationale` の本文を書く。
- **状態**：開いている＝有効。置き換えたら「outdated」で閉じる。やめたら「resolved」で閉じ、理由をコメントする。
- **Q&A**：答えが付いた質問は「拾う」に回し、新しい DR の `sources` に `asked` としてその Q&A を入れる。
- **書き方**：GraphQL を使える環境ならそのまま書く。使えない環境で GitHub Actions を起動できるなら、ワークフロー `discussion`（`.github/workflows/discussion.yml`）を起動する。新しい DR は `action: create` と `category`（`decisions` / `decision-flows` / `q-a`）・`title`・`body`、追記は `action: comment` と `number`・`body`。起動したら、実行結果に出る番号を確かめてから「保存した」と伝える。
- **書けないとき**：Discussions に書く手段がない環境では、タイトルと本文をそのまま貼れる形で返し、「まだ保存していません」と明記する。ほかのリポジトリに書いて代わりにしない。

### 本文先頭の型

```yaml
kind: decision            # decision | flow（誰が決める・承認するかの決め方）
status: accepted          # proposed | accepted（閉じた後は superseded | retired）
approved_via: null        # 通った決め方の DR 番号（例：#12）
superseded_by: null
entry: explicit           # explicit: 人が追加 | auto: 仕組みや AI が拾った
decided_at: null          # YYYY-MM-DD
decided_by: []            # 最終的に決めた役割 [{role, org, delegated_by?}]。複数なら全員で決めた。この件だけ任されたなら delegated_by: {role, org}
approved_by: []           # 決める前に承認した役割 [{role, org}]（承認した順）
domain: technology        # technology | product | organization | business
scope: team               # team | multi_team | cross_department | company
reversibility: easy       # easy | costly | irreversible
touches_sensitive: false  # セキュリティ・個人情報・権限・監視や通知・ログに触れる
decision: ""
premises: []              # [{text, broken, broken_at}]
sources: []               # [{type, url}] type: chat|meeting|pr|ticket|approval|asked|manual
unconfirmed: []           # 元に書かれていなかった項目のキー
```

既存の ADR は `entry: explicit` で取り込める（Context→本文、Decision→`decision`、Status→状態、Consequences→後のコメント）。
