#!/usr/bin/env python3
"""decision-log を実際のエージェントで動かす評価。標準ライブラリと git だけを使う。

ケースごとに、合成の履歴を持つリポジトリを一時フォルダーに作り、スキルとサブエージェントを
README の入れ方どおりに入れ、エージェントの CLI をそのリポジトリで動かす。
自動で PASS にはしない。キーワードと、書いたファイルの決まった検査は目安で、人が応答を読んで判定する。
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "decision-log" / "scripts" / "build_index.py"

# (件名, 本文, {パス: 中身}[, PR の中のコミットのメッセージ])。マージコミットは件名が "Merge pull request" で始まるもの。
# 中のコミットのメッセージを省くと、本文の 1 行目を使う。
HISTORY = [
    ("Initial import", "", {
        "README.md": "# payment-api\n\nPayment APIs.\n",
        "src/payment/http/client.py": "MAX_RETRIES = 3\nTIMEOUT = 5\n",
        "src/payment/webhook/client.py": "TIMEOUT = 10\n",
        "src/payment/idempotency.py": "from uuid import uuid4\n\ndef key():\n    return uuid4()\n",
        "src/auth/session.py": "SESSION_TTL_HOURS = 24\n",
        "config/logging.yml": "retention_days: 30\n",
        "src/web/button.css": ".button { padding: 4px; }\n",
        "src/db/pool.py": "POOL_SIZE = 10\n",
    }),
    ("Merge pull request #12 from example/fix-typo", "Fix typo in README", {
        "README.md": "# payment-api\n\nPayment APIs.\n",
        "src/payment/http/client.py": "MAX_RETRIES = 3\nTIMEOUT = 30\n",
    }),
    ("Bump retry count (#13)", "", {"src/payment/http/client.py": "MAX_RETRIES = 5\nTIMEOUT = 30\n"}),
    ("Lower webhook timeout to 3s (#14)", "相手先の SLA に合わせて 3 秒にします。\n\n🤖 Generated with Claude Code", {
        "src/payment/webhook/client.py": "TIMEOUT = 3\n",
    }),
    ("Use UUIDv7 for idempotency keys (#15)",
     "決済チームのチームリードとして、冪等キーは UUIDv7 にすると決めました。他の案：UUIDv4（順序がなく索引が断片化）、ULID（ライブラリ依存が増える）。", {
         "src/payment/idempotency.py": "from uuid import uuid7\n\ndef key():\n    return uuid7()\n",
     }),
    ("Update button padding (#16)", "", {"src/web/button.css": ".button { padding: 6px; }\n"}),
    ("Extend session (#17)", "", {"src/auth/session.py": "SESSION_TTL_HOURS = 48\n"}),
    ("Keep logs longer (#18)", "", {"config/logging.yml": "retention_days: 90\n"}),
    ("Rotate webhook secret (#19)", "", {"src/payment/webhook/client.py": "TIMEOUT = 3\nSECRET_NAME = \"webhook-v2\"\n"}),
    ("Refactor helper (#20)", "", {"src/payment/helper.py": "values = [1, 2]\nresult = sum(values)\n"}),
    ("Cap batch size (#21)", "", {"src/payment/batch.py": "# The gateway rejects more than 100 items per call (incident 2025-03-15).\nBATCH_LIMIT = 100\n"}),
    ("Merge pull request #22 from example/db-pool", "Raise DB pool size", {"src/db/pool.py": "POOL_SIZE = 20\n"},
     "Raise DB pool size\n\nThe pool ran dry during the 2025-03-18 nightly batch. 20 covers the peak with headroom."),
]

# 既存の Decision log（E06 だけが使う）
SEEDED_LOG = """---
kind: log
category: reliability
keywords: [MAX_RETRIES, retry]
---

# [payment-api] リトライの上限が 3 から 5 になった

> 過去の観察である。決定ではなく、何も縛らない。

## 起きたこと

- {date} いまも同じ：リトライの上限が 3 から 5 になった。履歴：コミット {sha} ／ 現在：`src/payment/http/client.py:1`

## 理由

不明（記録に書かれていない）。

## 分かっていないこと

- なぜ 5 にしたか。
"""

# 古くなった Decision log（E10 だけが使う）。#12 の時点で確かめたまま、#13 で 1 行目（MAX_RETRIES）が変わった
STALE_LOG = """---
kind: log
category: reliability
keywords: [MAX_RETRIES, retry]
checked: {short}
---

# [payment-api] リトライの上限が 3 になった

> 過去の観察である。決定ではなく、何も縛らない。

**いま**（{short}）：上限は 3。理由は分かっていない。

## 起きたこと

- 2025-01-10 いまも同じ：リトライの上限が 3 になった。履歴：[コミット {short}][first] ／ 現在：[`client.py:1`][c1]
- {date} いまも同じ：タイムアウトが 5 から 30 になった。履歴：[PR #12][first] ／ 現在：[`client.py:2`][c2]

## 理由

不明（記録に書かれていない）。

## 分かっていないこと

- なぜ 3 にしたか。

[first]: https://github.com/example/payment-api/commit/{sha}
[c1]: https://github.com/example/payment-api/blob/{sha}/src/payment/http/client.py#L1
[c2]: https://github.com/example/payment-api/blob/{sha}/src/payment/http/client.py#L2
"""

PREAMBLE = (
    "これは評価用の合成のリポジトリで、実在の履歴ではありません。このワークスペースに入っている decision-log スキルに従ってください。"
    "GitHub やネットワークには触れず、手元の git だけで調べてください（`gh` は使えないものとして扱う）。\n\n"
)

# id: (プロンプト, 必要なキーワード, 出てはいけないキーワード, 置き場所を用意するか, 書いたファイルを検査するか)
CASES = {
    "E01": ("decision-log で audit して。範囲はリポジトリ全体。",
            ["#12", "不明"], ["status: accepted"], False, False),
    "E02": ("decision-log で audit して。範囲は src/payment/webhook/。",
            ["AI の印", "人の判断"], [], False, False),
    "E03": ("decision-log で audit して。範囲は src/payment/idempotency.py。",
            ["決定の候補", "UUIDv7"], ["status: accepted"], False, False),
    "E04": ("decision-log で audit して。範囲は src/web/。",
            [], [], False, False),
    "E05": ("decision-log で write して。範囲は src/payment/http/。置き場所は docs/decision-logs/。ブランチ・コミット・PR は作らず、ファイルを書くところまででよい。",
            ["docs/decision-logs", "不明"], [], False, True),
    "E06": ("decision-log で write して。DL-1 の「分かっていないこと」の「なぜ 5 にしたか」に、@alice が口頭で「外部監査で指摘されたから」と答えた。決めた人や決定の言葉はない。"
            "ブランチ・コミット・PR は作らず、ファイルを書くところまででよい。",
            ["分かった", "元の場所なし"], ["status: accepted"], True, True),
    "E07": ("decision-log で audit して。範囲はリポジトリ全体。",
            [], ["status: accepted"], False, False),
    "E08": ("decision-log で audit して。範囲は src/payment/batch.py。",
            ["記録あり", "コメント", "100"], ["不明（記録に書かれていない）"], False, False),
    "E10": ("decision-log で recheck して。ブランチ・コミット・PR は作らず、ファイルを書くところまででよい。",
            ["#13"], ["status: accepted"], True, True),  # 状態はファイルの正解表（ANSWERS）で見る
    "E09": ("decision-log で audit して。範囲は src/db/pool.py。",
            ["記録あり", "2025-03-18", "10 から 20"], ["不明（記録に書かれていない）"], False, False),
}


# 呼ばれているべきサブエージェント（応答の記録の Agent / Task の呼び出しで数える。プラグインの名前は末尾で照らす）
AGENTS = {"E07": ["decision-log-planner", "decision-log-reader"]}

# 書いたファイルに入っているべき事実（正規表現のどれか 1 つに当たればよい）。目安で、人の判定を置き換えない
ANSWERS = {
    "E05": {
        "PR #13（MAX_RETRIES）": [r"#13"],
        "PR #12（TIMEOUT）": [r"#12"],
        "MAX_RETRIES の前後": [r"3\s*(?:→|->|から|to)\s*5"],
        "TIMEOUT の前後": [r"5\s*(?:→|->|から|to)\s*30"],
        "分類が reliability": [r"^category:\s*reliability\s*$"],
        "理由は不明": [r"^不明"],
        "#12 はタイトルと中身が違う": [r"(?i)typo"],
    },
    "E10": {
        "追記のいまの行": [r"^\*\*いま\*\*（[0-9a-f]{7,40}）："],
        "上限の行が置き換え済みに": [r"(?:上限|MAX_RETRIES)[^\n]*置き換え済み", r"置き換え済み[^\n]*(?:上限|MAX_RETRIES)"],
        "置き換えた PR #13": [r"#13"],
        "タイムアウトの行はいまも同じ": [r"(?:タイムアウト|TIMEOUT)[^\n]*いまも同じ", r"いまも同じ[^\n]*(?:タイムアウト|TIMEOUT)"],
    },
}


def git(repo, *args, env=None):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, env=env).stdout


def build_repo(repo):
    """HISTORY のとおりに main を作る。マージコミットは別ブランチを --no-ff で取り込む。"""
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "eval")
    git(repo, "config", "user.email", "eval@example.com")
    git(repo, "remote", "add", "origin", "https://github.com/example/payment-api.git")
    for i, (subject, body, files, *inner) in enumerate(HISTORY):
        date = f"2025-0{1 + i // 4}-{10 + i:02d}T12:00:00+09:00"
        env = dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        merge = subject.startswith("Merge pull request")
        if merge:
            git(repo, "checkout", "-q", "-b", "topic")
        for path, text in files.items():
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        git(repo, "add", "-A")
        if merge:
            parts = (inner[0] if inner else body.split("\n")[0] or subject).split("\n\n", 1)
            message = ["-m", parts[0]] + (["-m", parts[1]] if len(parts) > 1 else [])
        else:
            message = ["-m", subject] + (["-m", body] if body else [])
        git(repo, "commit", "-q", "--allow-empty", *message, env=env)
        if merge:
            git(repo, "checkout", "-q", "main")
            git(repo, "merge", "-q", "--no-ff", "topic", "-m", subject, "-m", body, env=env)
            git(repo, "branch", "-q", "-D", "topic")


def install(repo):
    """利用者と同じ tools/install.sh で、Claude Code と Kiro の両方の場所に入れる（install.sh が壊れたら評価も落ちる）。"""
    for tool in ("claude", "kiro"):
        subprocess.run(["sh", str(ROOT / "tools" / "install.sh"), tool, str(repo)], capture_output=True, text=True, check=True)


def seed_log(repo, case):
    folder = repo / "docs" / "decision-logs"
    folder.mkdir(parents=True)
    path = folder / "0001.md"
    if case == "E10":
        sha = git(repo, "log", "--format=%H", "-1", "--grep", "Merge pull request #12").strip()
        date = git(repo, "log", "--format=%ad", "--date=short", "-1", sha).strip()
        path.write_text(STALE_LOG.format(sha=sha, short=sha[:7], date=date), encoding="utf-8")
    else:
        sha = git(repo, "log", "--format=%h", "-1", "--grep", "Bump retry count").strip()
        path.write_text(SEEDED_LOG.format(date="2025-01-12", sha=sha), encoding="utf-8")
    subprocess.run([sys.executable, str(SCRIPT), str(folder), "--repo", "payment-api"], capture_output=True, check=True)
    return {p.name: p.read_text(encoding="utf-8") for p in folder.glob("*.md")}


def final_text(stdout):
    """エージェントが stream-json で出したときは、最後の応答（result）だけを返す。ツールの結果まで照らさないため。"""
    for line in reversed(stdout.splitlines()):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "result" and isinstance(event.get("result"), str):
            return event["result"]
    return stdout


def subagents(stdout):
    """stream-json の応答の記録から、呼んだサブエージェントの名前を順に返す。"""
    names = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        message = event.get("message") if isinstance(event, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        for item in content if isinstance(content, list) else []:
            if isinstance(item, dict) and item.get("type") == "tool_use" and item.get("name") in ("Agent", "Task"):
                names.append(str((item.get("input") or {}).get("subagent_type") or ""))
    return names


def inspect(repo, before, answers=None):
    """書いたファイルの決まった検査：索引が最新で形が崩れていないか、前からあったファイルを書き換えていないか、
    正解表の事実が入っているか。"""
    folder = repo / "docs" / "decision-logs"
    if not folder.is_dir():
        return {"wrote": False}
    checked = subprocess.run([sys.executable, str(SCRIPT), str(folder), "--check"], capture_output=True, text=True)
    stale = subprocess.run([sys.executable, str(SCRIPT), str(folder), "--stale"], capture_output=True, text=True)
    # 名前を変えた・消したファイルも「書き換えた」に数える（読めずに評価全体が止まらないように）。フロントマターは直してよい
    body = lambda text: re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S).rstrip("\n")
    rewritten = [name for name, text in before.items() if name != "README.md"
                 and (not (folder / name).is_file()
                      or not body((folder / name).read_text(encoding="utf-8")).startswith(body(text)))]
    written = "\n".join(p.read_text(encoding="utf-8") for p in folder.glob("*.md") if p.name != "README.md")
    missing = [fact for fact, patterns in (answers or {}).items()
               if not any(re.search(pat, written, re.M) for pat in patterns)]
    return {"wrote": True, "files": sorted(p.name for p in folder.glob("*.md")),
            "index_check": checked.returncode == 0, "index_output": checked.stdout.strip(),
            "rewritten_existing": rewritten, "missing_facts": missing,
            "stale_after": stale.returncode != 0, "stale_output": stale.stdout.strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--agent-argv-json", required=True,
                        help="エージェントの実行ファイルと引数の JSON 配列。{prompt_file} と {workspace} を置き換える。プロンプトは標準入力にも渡す")
    parser.add_argument("--agent-version", required=True, help="結果に残すエージェントとモデルの版")
    parser.add_argument("--skills-loaded", action="store_true", help="スキルが実際に読み込まれたことを人が確かめた、という申告")
    parser.add_argument("--output", default="decision-log-eval-results")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--case", choices=sorted(CASES), action="append")
    args = parser.parse_args()
    argv = json.loads(args.agent_argv_json)
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) for x in argv):
        parser.error("--agent-argv-json は空でない文字列の JSON 配列にする")
    revision = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() or None
    output = pathlib.Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for case in args.case or sorted(CASES):
        prompt, required, forbidden, seeded, check_files = CASES[case]
        with tempfile.TemporaryDirectory(prefix="decision-log-eval-") as work:
            repo = pathlib.Path(work) / "payment-api"
            build_repo(repo)
            install(repo)
            before = seed_log(repo, case) if seeded else {}
            text = PREAMBLE + prompt + "\n"
            prompt_file = pathlib.Path(work) / "prompt.txt"
            prompt_file.write_text(text, encoding="utf-8")
            command = [a.replace("{prompt_file}", str(prompt_file)).replace("{workspace}", str(repo)) for a in argv]
            start = time.monotonic()
            try:
                proc = subprocess.run(command, input=text, text=True, capture_output=True, cwd=repo, timeout=args.timeout)
                response, error, code, timed_out = proc.stdout, proc.stderr, proc.returncode, False
            except subprocess.TimeoutExpired as exc:
                out = exc.stdout or ""
                response, error, code, timed_out = out.decode("utf-8", "replace") if isinstance(out, bytes) else out, "Timed out", None, True
            files = inspect(repo, before, ANSWERS.get(case)) if check_files else None
        (output / f"{case}.prompt.txt").write_text(text, encoding="utf-8")
        (output / f"{case}.response.txt").write_text(response, encoding="utf-8")
        (output / f"{case}.stderr.txt").write_text(error, encoding="utf-8")
        final = final_text(response)
        (output / f"{case}.final.txt").write_text(final, encoding="utf-8")
        lowered = final.lower()
        status = "REVIEW_REQUIRED" if code == 0 and not timed_out and args.skills_loaded else "INCONCLUSIVE"
        called = subagents(response)
        missing_agents = [a for a in AGENTS.get(case, []) if not any(n == a or n.endswith(":" + a) for n in called)]
        results.append(dict(id=case, status=status, exit_code=code, subagents=called, missing_agents=missing_agents,
                            missing_keywords=[k for k in required if k.lower() not in lowered],
                            forbidden_keyword_hits=[k for k in forbidden if k.lower() in lowered],
                            files=files, elapsed_seconds=round(time.monotonic() - start, 2)))
        print(f"{case}: {status} {results[-1]['missing_keywords'] or ''} {results[-1]['forbidden_keyword_hits'] or ''} {missing_agents or ''}")
    manifest = dict(timestamp_utc=dt.datetime.now(dt.timezone.utc).isoformat(), revision=revision,
                    agent_version=args.agent_version, skills_loaded_operator_attestation=args.skills_loaded,
                    agent_argv=argv, results=results,
                    note="キーワードとファイルの検査は目安。人が応答を読み、evals/decision-log/cases.md と照らして PASS / FAIL をつける。")
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("結果:", output)


if __name__ == "__main__":
    main()
