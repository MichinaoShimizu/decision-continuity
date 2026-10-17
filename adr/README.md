# ADR キット

コードのリポジトリで、変更のたびに組織の決定と照らし、過去の変更の理由を起こすための仕組み。2 つのスキルと、`CLAUDE.md` に足す指示、スキルの評価からなる。

記録はコードのリポジトリには置かない。すべてこのリポジトリの `records/` に Markdown で置き、`decision-record` と同じ書式・同じ状態で扱う。技術の決定（いわゆる ADR）は、`repos`・`paths`・`keywords` を持った DR にすぎない。

## 考え方

**起きたこと**（Decision log。`records/decision-logs/`）と、**意図して決めたこと**（DR。`records/decisions/`、`records/decision-flows/`）を分けて残す。Decision log は縛らず、有効な DR だけが以後の変更を縛る。記録の種類、状態、探し方、流れと図は [guide.md](guide.md)。

## 構成

| 場所 | 中身 |
|---|---|
| `skills/adr-guard/` | 変更が有効な決定とぶつからないかを確かめる |
| `skills/decision-log/` | PR・issue・コードから、過去の変更を Decision log に起こす。このフォルダーだけで、どのリポジトリでも動く。手順と書き方の詳細は `references/`、索引を作るスクリプトは `scripts/` |
| `skills/decision-continuity-contract.md` | スキルが共通で守るルール |
| [`templates/agent-instructions.md`](templates/agent-instructions.md) | `CLAUDE.md`（Kiro なら steering）に足す指示 |
| `agents/` | decision-log が候補を並行に読ませるサブエージェント `decision-log-reader`（[Claude Code 用](agents/claude/decision-log-reader.md)と Kiro 用の [JSON](agents/kiro/decision-log-reader.json) と [Markdown](agents/kiro/decision-log-reader.md)。Kiro は CLI が JSON、IDE が Markdown を読むので両方を置く） |
| `templates/kiro/` | Kiro 用の薄い `SKILL.md`。中身は `.claude/skills/` の正本を読むように言うだけ |
| `evals/` | スキルを試す 21 のケース、固定データ、実行の手順、実行スクリプト |

新しい決定を書くこと、決め直すことは `decision-record`（`.claude/skills/decision-record/`）の「書く」「決め直す」が受け持つ。記録を読み書きするのは同じフォルダーの `records.py`。

## 入れ方

対象のリポジトリで:

1. `adr/skills/` の中身と、このリポジトリの `.claude/skills/decision-record/` を、`.claude/skills/` に写す。ここが正本で、`records.py` もここに置く。Kiro も使うなら、`templates/kiro/` の中身を `.kiro/skills/` に写す。サブエージェント `decision-log-reader` も、`agents/claude/` を `.claude/agents/` に、Kiro なら `agents/kiro/` の 2 つ（`.json` と `.md`）を両方 `.kiro/agents/` に写す（候補が多いとき、decision-log が並行に読ませる）。`decision-record/STORE` に記録のリポジトリ（`owner/decision-continuity`）が書いてある。
2. `templates/agent-instructions.md` の内容を `CLAUDE.md`（Kiro なら steering）に足し、`<repo-name>` をそのリポジトリの名前にする。
3. 記録のリポジトリを `git clone` できるようにしておく（非公開なら git の認証を通す）。`records.py` は読むたびにキャッシュへ最新を取ってくる。読めないと adr-guard は「読めなかった」と報告する。
4. 記録を書く（decision-log の `write` など）なら、記録のリポジトリを手元にクローンし、`--store <パス>` か環境変数 `DR_STORE` でそのパスを渡す。

decision-log は以前 `reverse-adr` という名前だった。入れてあるなら、フォルダーを `decision-log` に置き換える。

decision-log だけを使うなら、`adr/skills/decision-log/` をフォルダーごと（`SKILL.md`・`references/`・`scripts/`）対象のリポジトリに写すだけでよい。写す先は Claude Code なら `.claude/skills/decision-log/`、Kiro なら `.kiro/skills/decision-log/`（両方使うなら両方）。候補が多いリポジトリなら、`agents/` のサブエージェントも写すと速い。`records.py` がなければ、既存の Decision log を `docs/decision-logs/` から読み、`write` でもそこに書く（形は組織の記録と同じなので、あとで移せる）。

## 使い方

- 「この変更、決定とぶつからない？」→ adr-guard
- 「この方針を変えたいので DR にして」→ decision-record（書く）
- 「認証まわりがなぜこうなったか、履歴から起こして」→ decision-log（audit / write）
- 「この Decision log の形を、これからのルールにしたい」→ decision-record（Decision log から決定にする）

## 評価

[evals/scenario-tests.md](evals/scenario-tests.md) の 21 のケースで、スキルが決まりどおりに動くかを確かめる。記録は固定データ（`evals/fixtures/`）から読むので、GitHub には触れない。実際のエージェントで回すときは [evals/agent-runner.md](evals/agent-runner.md)。実行スクリプトのテストは、`adr/evals/` を変えた PR で GitHub Actions が回す。
