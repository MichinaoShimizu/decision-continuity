# ADR キット

コードのリポジトリで、設計の意思決定を残し、変更のたびに確かめるための仕組み。3 つのスキルと、索引のひな形、スキルの評価からなる。

このリポジトリの `decision-record`（組織の意思決定を Discussions に残す）とは別のもの。こちらは**コードのリポジトリの中に**、そのリポジトリの設計判断を残す。

## 考え方

**起きたこと**と、**意図して決めたこと**を分けて残す。

| | Decision Log | ADR |
|---|---|---|
| 何を残すか | 過去に何が変わったか、なぜか（分かる範囲で）、何が分からないか | これからどうするか、なぜか、誰が決めるか |
| 縛るか | 縛らない。判断の材料 | 人が Accepted にした ADR だけが、以後の変更を縛る |

- マージされた PR は「変わった」ことの証拠で、「方針として承認された」ことの証拠ではない。
- 分からない理由は Unknown のまま残す。後から理由を作らない。
- 新しい ADR は Proposed で書き、人が承認して Accepted にする。

詳しい流れと図は [guide.md](guide.md)。

## 構成

| 場所 | 中身 |
|---|---|
| `skills/reverse-adr/` | PR・issue・コード・テストから、過去の決定を Decision Log に起こす |
| `skills/adr-guard/` | 変更が既存の ADR とぶつからないかを確かめる |
| `skills/forward-adr/` | 新しい決定や、決定の変更を Proposed の ADR として書く |
| `skills/decision-continuity-contract.md` | 3 つのスキルが共通で守るルール |
| `templates/` | ADR の索引、Decision Log の索引、`CLAUDE.md` に足す指示 |
| `evals/` | スキルを試す 12 のシナリオ、実行の手順、実行スクリプト |

ADR と Decision Log の書式は、それぞれ forward-adr と reverse-adr の中にある（写しを別に持たない）。

## 入れ方

対象のリポジトリで:

1. `skills/` の中身を `.claude/skills/` に写す（Kiro なら `.kiro/skills/` にも）。`decision-continuity-contract.md` はスキルのフォルダーと同じ階層に置く。
2. `templates/adr-index.md` を `docs/adr/README.md` に、`templates/decision-log-index.md` を `docs/decision-log/README.md` に写す。
3. `templates/agent-instructions.md` の内容を `CLAUDE.md`（Kiro なら steering）に足す。
4. 過去の決定を起こしたいときは「reverse-adr で audit して」と頼む。書き出すときは write。

置き場所を変えるときは、`CLAUDE.md` に書いたパスも合わせる。スキルは対象のリポジトリの決まりを優先する。

## 使い方

- 「この変更、ADR とぶつからない？」→ adr-guard（check）
- 「この方針を変えたいので ADR にして」→ forward-adr（draft）
- 「認証まわりがなぜこうなったか、履歴から起こして」→ reverse-adr（audit / write）

## 評価

[evals/scenario-tests.md](evals/scenario-tests.md) の 12 のシナリオで、スキルが決まりどおりに動くかを確かめる。実際のエージェントで回すときは [evals/agent-runner.md](evals/agent-runner.md)。実行スクリプトのテストは、`adr/evals/` を変えた PR で GitHub Actions が回す。
