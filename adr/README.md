# ADR キット

コードのリポジトリで、変更のたびに組織の決定と照らし、過去の変更の理由を起こすための仕組み。2 つのスキルと、`CLAUDE.md` に足す指示、スキルの評価からなる。

記録はコードのリポジトリには置かない。すべてこのリポジトリの `records/` に Markdown で置き、`decision-record` と同じ書式・同じ状態で扱う。技術の決定（いわゆる ADR）は、`repos`・`paths`・`keywords` を持った DR にすぎない。

## 考え方

**起きたこと**と、**意図して決めたこと**を分けて残す。

| | Decision log | 決定（DR） |
|---|---|---|
| フォルダー | `records/decision-logs/` | `records/decisions/`、`records/decision-flows/` |
| 何を残すか | 過去に何が変わったか、なぜか（分かる範囲で）、何が分からないか | これからどうするか、なぜか、誰が決めたか |
| 縛るか | 縛らない。判断の材料 | 有効なものだけが、以後の変更を縛る |

- 状態は 3 つだけ：提案中（`proposed`）、有効（`accepted` か「決まった」の追記）、終了（「終了」の追記がある）。
- マージされた PR は「変わった」ことの証拠で、「方針として決めた」ことの証拠ではない。
- 分からない理由は Unknown のまま残す。後から理由を作らない。
- 索引のファイルは持たない。各 DR の `repos`・`paths`・`keywords` が索引の 1 行の代わりで、`records.py index` がそれを並べる。

詳しい流れと図は [guide.md](guide.md)。

## 構成

| 場所 | 中身 |
|---|---|
| `skills/adr-guard/` | 変更が有効な決定とぶつからないかを確かめる |
| `skills/reverse-adr/` | PR・issue・コード・テストから、過去の変更を Decision log に起こす。`SKILL.md` 1 枚で、どのリポジトリでも動く |
| `skills/decision-continuity-contract.md` | スキルが共通で守るルール |
| `templates/agent-instructions.md` | `CLAUDE.md` に足す指示 |
| `evals/` | スキルを試す 16 のケース、固定データ、実行の手順、実行スクリプト |

新しい決定を書くこと、決め直すことは `decision-record`（`.claude/skills/decision-record/`）の「書く」「決め直す」が受け持つ。記録を読み書きするのは同じフォルダーの `records.py`。

## 入れ方

対象のリポジトリで:

1. `adr/skills/` の中身と、このリポジトリの `.claude/skills/decision-record/` を、`.claude/skills/` に写す（Kiro なら `.kiro/skills/` にも）。`decision-record/STORE` に記録のリポジトリ（`owner/decision-records`）が書いてある。
2. `templates/agent-instructions.md` の内容を `CLAUDE.md`（Kiro なら steering）に足し、`<repo-name>` をそのリポジトリの名前にする。
3. 記録のリポジトリを `git clone` できるようにしておく（非公開なら git の認証を通す）。`records.py` は読むたびにキャッシュへ最新を取ってくる。読めないと adr-guard は「読めなかった」と報告する。
4. 記録を書く（reverse-adr の `write` など）なら、記録のリポジトリを手元にクローンし、`--store <パス>` か環境変数 `DR_STORE` でそのパスを渡す。

reverse-adr だけを使うなら、`adr/skills/reverse-adr/SKILL.md` を対象のリポジトリの `.claude/skills/reverse-adr/SKILL.md` に写すだけでよい。`records.py` がなければ、既存の Decision log を `docs/decision-logs/` から読み、`write` でもそこに書く（形は組織の記録と同じなので、あとで移せる）。

## 使い方

- 「この変更、決定とぶつからない？」→ adr-guard
- 「この方針を変えたいので DR にして」→ decision-record（書く）
- 「認証まわりがなぜこうなったか、履歴から起こして」→ reverse-adr（audit / write）
- 「この Decision log の形を、これからのルールにしたい」→ decision-record（Decision log から決定にする）

## 評価

[evals/scenario-tests.md](evals/scenario-tests.md) の 16 のケースで、スキルが決まりどおりに動くかを確かめる。記録は固定データ（`evals/fixtures/`）から読むので、GitHub には触れない。実際のエージェントで回すときは [evals/agent-runner.md](evals/agent-runner.md)。実行スクリプトのテストは、`adr/evals/` を変えた PR で GitHub Actions が回す。
