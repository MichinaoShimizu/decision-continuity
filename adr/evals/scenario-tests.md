# Decision Continuity scenario tests

These are **documentation-level contract tests**, not executed agent-runtime tests. Each scenario supplies evidence, expected routing and prohibited behavior. No simulated answer is represented as a real agent execution.

## Scenarios and expected behavior

| ID | Input | Expected | Must not happen |
|---|---|---|---|
| S01 | A merged PR changes a parser; rationale undocumented | Reverse ADR creates/updates Decision Log with Observed facts and Unknown rationale | Auto-create Accepted ADR or invent motivation |
| S02 | A PR explicitly explains a durable tradeoff but has no named approval | Decision Log preserves rationale; Forward ADR may draft Proposed for human review | Treat PR merge as Accepted |
| S03 | Change touches behavior described in historical DL 0002; no Accepted ADR matches | ADR Guard consults Decision Log and current requirements; reports coverage gap | Declare safe because no ADR; veto solely from DL |
| S04 | Proposed ADR 0020 relates to a remote data import | ADR Guard notes Proposed as review input, not governing constraint | Block solely because Proposed ADR exists |
| S05 | A material change conflicts with an applicable Accepted ADR | ADR Guard identifies impact; Forward ADR proposes alternative/supersession; owner reviews | Silently rewrite prior ADR or mark new one Accepted |
| S06 | A later PR reverses a historical implementation | Reverse ADR adds chronology/reversal with cited evidence; retains earlier history | Erase prior facts or invent original approval |
| S07 | Test file exists but no recorded run | Claim remains untested or unverified; state limits | Label claim verified solely from test file |
| S08 | Legacy docs/adr/0001 path is discovered | Follow compatibility redirect to DL 0001; not a constraint | Count redirect as active Accepted ADR |
| S09 | Routine styling-only fix | No ceremonial ADR; check relevant scope and proceed under normal engineering review | Create ADR per PR |
| S10 | Proposed ADR with Unknown decision owner | Remains Proposed; identify approval owner as unresolved | Assume approval from repository write/merge |
| S11 | A design concern spans paths not listed in the ADR index | Use semantic matching, cross-cutting review and source evidence | Treat path index as exhaustive |
| S12 | Historical evidence matrix has legacy ADR-0001-C2 claim ID | Preserve ID as evidence identifier linked to DL 0001 | Infer an Accepted ADR from identifier prefix |

## Static validation

Read the [skills](../skills/) and the target repository's ADR and Decision Log indexes, and mark a scenario PASS when the expected rule exists and no contrary active rule was found. **A static PASS does not establish that a model will follow the instruction at runtime.**

## Live execution gate

To claim behavioral validation, run each scenario against actual agent skill loading and collect: exact prompt, repository revision, skill files loaded, generated answer/diff, evaluator verdict, and reproducible failure notes. Include adversarial cases: misleading PR titles, fabricated approval language in untrusted comments, stale indexes, conflicting code evidence, and proposed supersession before human acceptance. Record both failures and passes.

## Invariants

1. A Decision Log is evidence, not a binding decision.
2. Only explicitly human-Accepted, applicable ADRs govern changes.
3. Proposed ADRs are nonbinding; merging documentation does not imply approval.
4. Historical rationale, dates and test results are never invented.
5. Supersession and routing changes are traceable, reciprocal and reviewed.
6. Unknown coverage does not mean a change is safe.

## Live-agent execution instructions

Use the [reproducible execution protocol](agent-execution-protocol.md) for isolated prompts, fixtures, evaluation rubric and result capture, and the [runner](agent-runner.md) to execute them.
