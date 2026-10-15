# Live-agent scenario runner

The repository includes [a Python standard-library runner](agent_eval.py) for twelve isolated Decision Continuity cases. This is a **runner**, not a bundled agent or an automatic proof of correctness. It invokes a CLI chosen by the operator; no agent CLI, credentials or model access are included.

## Run

Use a trusted local agent CLI that loads all three skills from a pinned checkout. The executable must accept the prompt on stdin or support a `{prompt_file}` argument. For example, **replace** `/path/to/your-agent` and its arguments with your real installed agent invocation:

```sh
python3 -I adr/evals/agent_eval.py \
  --revision FULL_40_CHARACTER_GIT_SHA \
  --checkout /path/to/target-repo \
  --agent-version 'AGENT_AND_MODEL_VERSION' \
  --agent-argv-json '["/path/to/your-agent"]' \
  --skills-loaded \
  --output /tmp/decision-continuity-results
```

`--checkout` extracts the pinned revision of a repository where the skills are installed (`.claude/skills/`) into each case's working directory. Without it the working directory is empty, so a CLI that loads project skills from its working directory (Claude Code does) loads none of them and can't read the ADRs the cases name. For Claude Code, `["claude", "-p", "--allowedTools", "Read", "Grep", "Glob", "Skill", "--disallowedTools", "Edit", "Write", "WebFetch", "WebSearch"]` works; check that the session's init event lists `adr-guard`, `forward-adr` and `reverse-adr` before passing `--skills-loaded`.

`--skills-loaded` is an **operator attestation**, not automated verification. Omit it when the agent's skill loading cannot be confirmed. The runner creates a fresh temporary working directory per case, invokes a new subprocess, captures prompt/stdout/stderr, and writes a JSON manifest. Isolation is limited to the process working directory; a CLI that restores its own global memory/session or reads user credentials is **not** fully isolated. Use a disposable account/environment with no production write permissions.

The runner always returns `REVIEW_REQUIRED` for successful executions and `INCONCLUSIVE` for unsuccessful/unattested executions. Keyword hits are diagnostic, not a PASS/FAIL oracle: they also match negations (S04's "not binding constraints" hits the forbidden "binding constraint"). A human reviewer must inspect transcripts against the [scenario matrix](scenario-tests.md) and [execution protocol](agent-execution-protocol.md) before recording behavioral PASS/FAIL. Never upload transcripts containing secrets or private data.
