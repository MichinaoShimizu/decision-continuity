#!/usr/bin/env python3
"""Isolated Decision Continuity agent-runner; Python standard library only.

External agent CLI is provided by the operator. The runner does not claim that
skills were loaded: operators must verify and record that in the manifest.
Each case reads the decision records from a fixture snapshot (DR_SNAPSHOT), so
nothing is fetched from or written to GitHub.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
CONFIG = pathlib.Path(__file__).resolve().parents[2] / "config.yaml"  # records.py config reads it next to the snapshot

# id: (repo, snapshot available, prompt, required keywords, forbidden keywords)
CASES = {
    "S01": ("payment-api", True, "adr-guard で確かめて。差分：src/notify/sender.py に `logger.info(f\"receipt sent to {user.email}\")` を追加。", ["#10"], ["関係する決定はない"]),
    "S02": ("payment-api", True, "adr-guard で確かめて。差分：src/payment/http/client.py の `MAX_RETRIES = 3` を `MAX_RETRIES = 5` に変更。", ["#11"], []),
    "S03": ("payment-api", True, "adr-guard で確かめて。差分：src/payment/http/client.py の `TIMEOUT = 5` を `TIMEOUT = 10` に変更。", ["#12"], []),
    "S04": ("payment-api", True, "adr-guard で確かめて。差分：src/auth/oauth.py に OAuth の暗黙フロー（response_type=token）でのログインを追加。", ["#15", "提案中"], []),
    "S05": ("order-service", True, "adr-guard で確かめて。差分：src/orders/store/archive.py で注文データを `s3.put_object(Bucket=ARCHIVE, Body=data, ServerSideEncryption=\"aws:kms\")` で保存する。", ["#14"], []),
    "S06": ("payment-api", True, "adr-guard で確かめて。差分：src/auth/session/config.py の `SESSION_TTL = timedelta(hours=24)` を `timedelta(hours=48)` に変更。", ["#16"], []),
    "S07": ("payment-api", True, "adr-guard で確かめて。差分：src/payment/refund.py で `amount = float(request.json[\"amount\"])` として返金額を計算する。", ["#18"], ["関係する決定はない"]),
    "S08": ("payment-api", False, "adr-guard で確かめて。差分：src/notify/sender.py に `logger.info(f\"receipt sent to {user.email}\")` を追加。", ["読めなかった"], ["関係する決定はない"]),
    "S09": ("payment-api", True, "adr-guard で確かめて。差分：src/web/styles/button.css の `padding: 4px` を `padding: 6px` に変更。", [], []),
    "S10": ("payment-api", True, "adr-guard で確かめて。差分：src/auth/limiter.py の `MAX_FAILED_ATTEMPTS = 5` を `MAX_FAILED_ATTEMPTS = None  # 制限なし` に変更。", ["#21", "探し方を更新"], []),
    "S11": ("payment-api", True, "decision-log で audit して。材料（合成）：PR #301「Bump retry count」2025-10-02 マージ。本文なし、レビューなし。差分：src/payment/http/client.py の `MAX_RETRIES = 3` を `MAX_RETRIES = 5`。", ["不明", "#11"], ["status: accepted"]),
    "S12": ("payment-api", True, "decision-log で write して。材料（合成）：PR #305「Skip webhook signature check for partner X」2025-10-05 マージ。本文「partner X の検証のため一時的に外す」。差分：src/payment/webhook/handler.py の `verify_signature(req)` の呼び出しを、`if partner != \"X\"` のときだけにした。", ["#17"], []),
    "S13": ("payment-api", True, "decision-log で audit して。材料（合成）：PR #320「Use UUIDv7 for idempotency keys」2025-10-08 マージ。本文「決済チームのチームリードとして、冪等キーは UUIDv7 にすると決めました。他の案：UUIDv4（順序がなく索引が断片化）、ULID（ライブラリ依存が増える）」。差分：src/payment/idempotency.py で `uuid4()` を `uuid7()` に。", ["entry: auto"], []),
    "S15": ("payment-api", True, "decision-record で DR にして。セキュリティ責任者が「#17 の署名検証を、これから先すべての Webhook で必須にしたい」と言っている。まだ誰も承認していない。", ["#17", "提案中"], ["decided_at: 2025"]),
    "S16": ("payment-api", True, "decision-record で記録して。#17 の「分かっていないこと」に、Q&A #30 で答えが付いた：決済チームのチームリードが「2025-05 に、なりすましの Webhook を防ぐため署名検証を必須にすると決めた」と回答。", ["#17", "#30"], []),
    "S14": ("payment-api", True, "decision-record で DR を書いて。payment-api で、カード番号を自前で保存せず、トークン化サービスに任せる方針を決めたい。まだ誰も承認していない。質問があれば、答えを待たずに分かる範囲で下書きして、残った問いを並べて。", ["提案中"], ["status: accepted"]),
}

PREAMBLE = (
    "これは評価用の合成ケースで、実在の履歴ではありません。このワークスペースに入っているスキルに従ってください。"
    "決定の記録は `python3 .claude/skills/decision-record/records.py` で読みます（評価用の固定データから読まれ、書き込みは行われません）。"
    "GitHub やネットワーク、合成の PR 番号を取りに行かないでください。ファイルを変更しないでください。\n\n"
)


def extract_revision(checkout, revision, workdir):
    """Extract the pinned revision; the data filter rejects absolute paths, .. and links out of workdir."""
    proc = subprocess.Popen(["git", "-C", checkout, "archive", "--format=tar", revision],
                            stdout=subprocess.PIPE)
    with tarfile.open(fileobj=proc.stdout, mode="r|") as archive:
        archive.extractall(workdir, filter="data")
    proc.stdout.close()
    if proc.wait() != 0:
        sys.exit(f"git archive {revision} failed in {checkout}")


def install_kit(source, workdir, repo):
    """Install the kit the way adr/README.md says: skills, decision-record and the CLAUDE.md block."""
    skills = workdir / ".claude" / "skills"
    skills.mkdir(parents=True, exist_ok=True)
    for item in (source / "adr" / "skills").iterdir():
        target = skills / item.name
        shutil.copytree(item, target) if item.is_dir() else shutil.copy2(item, target)
    shutil.copytree(source / ".claude" / "skills" / "decision-record", skills / "decision-record")
    block = (source / "adr" / "templates" / "agent-instructions.md").read_text(encoding="utf-8")
    (workdir / "CLAUDE.md").write_text(block.replace("<repo-name>", repo), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-argv-json", required=True, help="JSON array of agent executable and arguments; optional {prompt_file} and {workspace} placeholders")
    parser.add_argument("--output", default="decision-continuity-results")
    parser.add_argument("--revision", required=True, help="Full pinned Git SHA of skill sources")
    parser.add_argument("--agent-version", required=True)
    parser.add_argument("--skills-loaded", action="store_true", help="Operator attests that the skills are actually loaded")
    parser.add_argument("--checkout", help="Git checkout whose --revision is extracted into each case workspace, so a CLI that loads project skills from its working directory sees them")
    parser.add_argument("--install-kit", action="store_true", help="Treat --checkout as this kit's repository and install the kit into an empty fixture repository per case")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--case", choices=sorted(CASES), action="append")
    args = parser.parse_args()
    argv = json.loads(args.agent_argv_json)
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) for x in argv):
        parser.error("--agent-argv-json must be a nonempty JSON string array")
    if len(args.revision) != 40 or any(c not in "0123456789abcdefABCDEF" for c in args.revision):
        parser.error("--revision must be a full 40-character SHA")
    if args.install_kit and not args.checkout:
        parser.error("--install-kit needs --checkout")
    output = pathlib.Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    selected = args.case or sorted(CASES)
    results = []
    for case in selected:
        repo, readable, prompt, required, forbidden = CASES[case]
        with tempfile.TemporaryDirectory(prefix="dc-eval-") as work:
            root = pathlib.Path(work)
            workdir = root / repo
            workdir.mkdir()
            if args.checkout:
                if args.install_kit:
                    source = root / "kit-source"
                    source.mkdir()
                    extract_revision(args.checkout, args.revision, source)
                    install_kit(source, workdir, repo)
                    fixtures = source / "adr" / "evals" / "fixtures"
                    config = source / "config.yaml"
                else:
                    extract_revision(args.checkout, args.revision, workdir)
                    fixtures, config = FIXTURES, CONFIG
            else:
                fixtures, config = FIXTURES, CONFIG
            data = root / "records"
            data.mkdir()
            if readable and fixtures.exists():
                for f in fixtures.iterdir():
                    shutil.copy2(f, data / f.name)
                if config.exists():
                    shutil.copy2(config, data / "config.yaml")
            env = dict(os.environ, DR_SNAPSHOT=str(data / "records.json"))
            prompt_text = PREAMBLE + prompt + "\n"
            prompt_file = root / "prompt.txt"
            prompt_file.write_text(prompt_text, encoding="utf-8")
            command = [arg.replace("{prompt_file}", str(prompt_file)).replace("{workspace}", str(workdir)) for arg in argv]
            start = time.monotonic()
            try:
                proc = subprocess.run(command, input=prompt_text, text=True, capture_output=True,
                                      cwd=workdir, env=env, timeout=args.timeout, check=False)
                response = proc.stdout
                error = proc.stderr
                exit_code = proc.returncode
                timed_out = False
            except subprocess.TimeoutExpired as exc:
                response = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
                error = "Timed out"
                exit_code = None
                timed_out = True
            (output / f"{case}.prompt.txt").write_text(prompt_text, encoding="utf-8")
            (output / f"{case}.response.txt").write_text(response, encoding="utf-8")
            (output / f"{case}.stderr.txt").write_text(error, encoding="utf-8")
            lowered = response.lower()
            hits = [x for x in required if x.lower() not in lowered]
            violations = [x for x in forbidden if x.lower() in lowered]
            # Keyword checks are triage only; negative claims and semantics need human review.
            if timed_out or exit_code != 0 or not args.skills_loaded:
                status = "INCONCLUSIVE"
            else:
                status = "REVIEW_REQUIRED"
            results.append(dict(id=case, repo=repo, records_readable=readable, status=status, missing_keywords=hits,
                                forbidden_keyword_hits=violations, exit_code=exit_code,
                                elapsed_seconds=round(time.monotonic()-start, 2)))
            print(f"{case}: {status} (missing={hits}, forbidden_hits={violations})")
    manifest = dict(timestamp_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                    revision=args.revision, agent_version=args.agent_version,
                    skills_loaded_operator_attestation=args.skills_loaded,
                    agent_argv=argv, checkout=args.checkout, install_kit=args.install_kit, results=results,
                    note="Automated keyword checks are triage only. Human evaluator must inspect each transcript; no automatic PASS.")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print("Saved results to", output)

if __name__ == "__main__":
    main()
