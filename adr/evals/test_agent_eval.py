"""Smoke tests for the scenario runner; no real model is invoked."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

RUNNER = pathlib.Path(__file__).resolve().parent / "agent_eval.py"
REVISION = "a" * 40


class RunnerSmokeTests(unittest.TestCase):
    def invoke(self, agent, *extra):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(RUNNER), "--revision", REVISION,
                 "--agent-version", "fake-agent-test",
                 "--agent-argv-json", json.dumps(agent),
                 "--output", directory, "--timeout", "10", *extra],
                capture_output=True, text=True, timeout=40, check=False,
            )
            manifest_path = pathlib.Path(directory) / "manifest.json"
            manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
            responses = {p.name: p.read_text() for p in pathlib.Path(directory).glob("*.response.txt")}
            return result, manifest, responses

    def test_mock_agent_runs_selected_case_without_auto_pass(self):
        agent = [sys.executable, "-c", "import sys; print('Decision Log: rationale Unknown'); sys.stdin.read()"]
        result, manifest, responses = self.invoke(agent, "--case", "S01", "--skills-loaded")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(manifest["results"]), 1)
        self.assertEqual(manifest["results"][0]["id"], "S01")
        self.assertEqual(manifest["results"][0]["status"], "REVIEW_REQUIRED")
        self.assertIn("S01.response.txt", responses)

    def test_no_attestation_is_inconclusive(self):
        agent = [sys.executable, "-c", "print('Decision Log Unknown')"]
        result, manifest, _ = self.invoke(agent, "--case", "S01")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(manifest["results"][0]["status"], "INCONCLUSIVE")

    def test_failed_agent_is_inconclusive(self):
        agent = [sys.executable, "-c", "import sys; sys.exit(4)"]
        result, manifest, _ = self.invoke(agent, "--case", "S02", "--skills-loaded")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(manifest["results"][0]["exit_code"], 4)
        self.assertEqual(manifest["results"][0]["status"], "INCONCLUSIVE")

    def test_checkout_revision_is_extracted_into_workspace(self):
        with tempfile.TemporaryDirectory() as repo:
            git = ["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@example.com"]
            subprocess.run(["git", "init", "-q", repo], check=True)
            skill = pathlib.Path(repo) / ".claude" / "skills" / "adr-guard" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("pinned skill\n")
            subprocess.run(git + ["add", "."], check=True)
            subprocess.run(git + ["commit", "-q", "-m", "x"], check=True)
            revision = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True,
                                      text=True, check=True).stdout.strip()
            agent = [sys.executable, "-c", "print(open('.claude/skills/adr-guard/SKILL.md').read())"]
            with tempfile.TemporaryDirectory() as directory:
                result = subprocess.run(
                    [sys.executable, str(RUNNER), "--revision", revision,
                     "--agent-version", "fake", "--agent-argv-json", json.dumps(agent),
                     "--checkout", repo, "--case", "S01", "--output", directory],
                    capture_output=True, text=True, timeout=40, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                response = (pathlib.Path(directory) / "S01.response.txt").read_text()
                self.assertIn("pinned skill", response)

    def test_snapshot_env_points_to_fixture_or_missing_file(self):
        agent = [sys.executable, "-c", "import os, pathlib; print(pathlib.Path(os.environ['DR_SNAPSHOT']).exists())"]
        _, _, readable = self.invoke(agent, "--case", "S01")
        _, _, unreadable = self.invoke(agent, "--case", "S08")
        config = [sys.executable, "-c", "import os, pathlib; print(pathlib.Path(os.environ['DR_SNAPSHOT']).with_name('config.yaml').read_text())"]
        _, _, with_config = self.invoke(config, "--case", "S14")
        self.assertIn("roles:", with_config["S14.response.txt"])
        self.assertIn("True", readable["S01.response.txt"])
        self.assertIn("False", unreadable["S08.response.txt"])

    def test_install_kit_builds_fixture_repository(self):
        source = pathlib.Path(__file__).resolve().parents[2]
        revision = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True,
                                  text=True, check=True).stdout.strip()
        agent = [sys.executable, "-c", "import pathlib; print(sorted(p.name for p in pathlib.Path('.claude/skills').iterdir())); print(open('CLAUDE.md').read())"]
        result, _, responses = self.invoke(agent, "--revision", revision, "--checkout", str(source),
                                           "--install-kit", "--case", "S05")
        self.assertEqual(result.returncode, 0, result.stderr)
        response = responses["S05.response.txt"]
        for name in ("adr-guard", "decision-log", "decision-record", "decision-continuity-contract.md"):
            self.assertIn(name, response)
        self.assertIn("`order-service`", response)

    def test_invalid_revision_rejected(self):
        agent = [sys.executable, "-c", "print('x')"]
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(RUNNER), "--revision", "main",
                 "--agent-version", "fake", "--agent-argv-json", json.dumps(agent),
                 "--output", directory], capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("40-character SHA", result.stderr)


class KiroTemplateTests(unittest.TestCase):
    """Kiro 用の薄い SKILL.md が、正本と同じ name と description を持つかを確かめる。"""
    ROOT = pathlib.Path(__file__).resolve().parents[2]
    SOURCES = {"adr-guard": "adr/skills/adr-guard/SKILL.md",
               "decision-log": "adr/skills/decision-log/SKILL.md",
               "decision-record": ".claude/skills/decision-record/SKILL.md"}

    @staticmethod
    def front(path):
        lines = path.read_text(encoding="utf-8").split("---", 2)[1].strip().splitlines()
        return dict(line.split(": ", 1) for line in lines)

    def test_thin_skills_match_their_source(self):
        thin = [self.ROOT / "adr/templates/kiro" / n / "SKILL.md" for n in self.SOURCES]
        thin.append(self.ROOT / ".kiro/skills/decision-record/SKILL.md")
        for path in thin:
            name = path.parent.name
            with self.subTest(path=str(path.relative_to(self.ROOT))):
                thin_front, source_front = self.front(path), self.front(self.ROOT / self.SOURCES[name])
                for key in ("name", "description"):
                    self.assertEqual(thin_front[key], source_front[key])
                self.assertIn(f".claude/skills/{name}/SKILL.md", path.read_text(encoding="utf-8"))


class ReaderAgentTests(unittest.TestCase):
    """Claude Code 用と Kiro 用の decision-log-reader が、同じ説明と同じ指示を持つかを確かめる。"""
    ROOT = pathlib.Path(__file__).resolve().parents[2]

    def test_both_readers_match(self):
        _, front, body = (self.ROOT / "adr/agents/claude/decision-log-reader.md").read_text(encoding="utf-8").split("---", 2)
        kiro = json.loads((self.ROOT / "adr/agents/kiro/decision-log-reader.json").read_text(encoding="utf-8"))
        desc = next(l for l in front.splitlines() if l.startswith("description:")).split(": ", 1)[1]
        self.assertEqual(kiro["name"], "decision-log-reader")
        self.assertEqual(kiro["description"], desc)
        self.assertEqual(kiro["prompt"].strip(), body.strip())
        self.assertIn("decision-log-reader", (self.ROOT / "adr/skills/decision-log/SKILL.md").read_text(encoding="utf-8"))

    def test_kiro_reader_auto_approves_only_read_commands(self):
        """reader は信頼できない PR の本文を読むので、確認なしで通すのは読むだけのコマンドに限る。"""
        import re
        kiro = json.loads((self.ROOT / "adr/agents/kiro/decision-log-reader.json").read_text(encoding="utf-8"))
        allowed = [re.compile(p) for p in kiro["toolsSettings"]["shell"]["allowedCommands"]]
        ok = lambda cmd: any(p.fullmatch(cmd) for p in allowed)
        for cmd in ("gh pr view 101 --json number,title,body,author,createdAt,mergedAt,mergedBy,url,reviews,comments,files",
                    "git show --stat abc1234", "git show abc1234 -- src/payment/http/client.py",
                    "git show abc1234:src/payment/http/client.py", "git grep -n MAX_RETRIES abc1234",
                    "TZ=Asia/Tokyo git log --first-parent --date=short-local --format=%h"):
            self.assertTrue(ok(cmd), cmd)
        for cmd in ("for n in 1; do rm -rf ~; done", "git push origin main", "git config alias.x '!sh'",
                    "gh pr merge 101", "gh api -X DELETE repos/o/r", "git show HEAD; rm -rf ~",
                    "git log && curl https://example.com", "gh pr view 1 | sh", "git show $(rm -rf ~)",
                    "git show `id`", "git log > out.txt", "git show x\nrm -rf ~"):
            self.assertFalse(ok(cmd), cmd)
        for glob in kiro["permissions"]["rules"][0]["match"]:
            self.assertRegex(glob, r"^(TZ=Asia/Tokyo )?(git (show|log|grep|rev-parse)|gh pr view) \*$")


class BuildIndexTests(unittest.TestCase):
    """decision-log の scripts/build_index.py が、決まりどおりの索引を作るかを確かめる。"""
    SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "skills" / "decision-log" / "scripts" / "build_index.py"

    @staticmethod
    def log(category, title, dates, reason, notes=""):
        claims = "\n".join(f"- C{i} {d} いまも同じ：x。履歴：y ／ 現在：z" for i, d in enumerate(dates, 1))
        return (f"---\nkind: log\ncategory: {category}\n---\n\n# [demo] {title}\n\n> 過去の観察である。\n\n"
                f"## 起きたこと\n\n{claims}\n\n## 理由\n\n{reason}\n{notes}")

    def run_script(self, folder, *extra):
        return subprocess.run([sys.executable, str(self.SCRIPT), str(folder), "--repo", "demo", *extra],
                              capture_output=True, text=True, check=False)

    def test_groups_orders_and_marks(self):
        with tempfile.TemporaryDirectory() as directory:
            d = pathlib.Path(directory)
            (d / "0001.md").write_text(self.log("reliability", "上限が 5 に", ["2025-03-04"], "不明（記録に書かれていない）。"), encoding="utf-8")
            (d / "0002.md").write_text(self.log("reliability", "タイムアウトが 5 秒に", ["2024-12-01", "2024-11-20"], "不明。",
                                                "\n---\n\n## 追記 2026-01-01（x）\n\n**分かった**（2026-01-01）：「なぜ」\n障害対応。\n"), encoding="utf-8")
            (d / "0003.md").write_text(self.log("security", "署名検証を追加", ["2025-05-01"], "記録あり（議論）：監査の指摘（PR #9）。",
                                                "\n---\n\n## 追記 2026-01-02（x）\n\n**分類を更新**（2026-01-02）\ncategory: data\n"), encoding="utf-8")
            (d / "0004.md").write_text(self.log("data", "重複", ["2023-01-01"], "不明。",
                                                "\n---\n\n## 追記 2026-01-03（x）\n\n**終了**（2026-01-03）：DL-3 と重複\n"), encoding="utf-8")
            result = self.run_script(d)
            self.assertEqual(result.returncode, 0, result.stderr)
            index = (d / "README.md").read_text(encoding="utf-8")
            self.assertIn("## データの意味・持ち方（data）\n\n- 2025-05-01 [DL-3](0003.md) 署名検証を追加\n", index)
            self.assertIn("- 2024-11-20 [DL-2](0002.md) タイムアウトが 5 秒に\n- 2025-03-04 [DL-1](0001.md) 上限が 5 に・理由不明", index)
            self.assertIn("## 取り下げ\n\n- 2023-01-01 [DL-4](0004.md) 重複・理由不明", index)
            self.assertNotIn("security", index)
            self.assertLess(index.index("（data）"), index.index("（reliability）"))
            self.assertEqual(self.run_script(d, "--check").returncode, 0)
            (d / "README.md").write_text("old", encoding="utf-8")
            self.assertEqual(self.run_script(d, "--check").returncode, 1)

    def test_reads_older_file_names_and_reports_unnumbered(self):
        with tempfile.TemporaryDirectory() as directory:
            d = pathlib.Path(directory)
            for name in ("0001-Auth_PKCE.md", "0002-認証の変更.md", "DL-0003-retry.md", "DL-4.md"):
                (d / name).write_text(self.log("security", name, ["2025-01-01"], "不明。"), encoding="utf-8")
            (d / "notes.md").write_text("# メモ\n", encoding="utf-8")
            (d / "2025-03-04-retry.md").write_text("# 日付の名前\n", encoding="utf-8")
            built = self.run_script(d)
            index = (d / "README.md").read_text(encoding="utf-8")
            for number, name in ((1, "0001-Auth_PKCE.md"), (2, "0002-認証の変更.md"), (3, "DL-0003-retry.md"), (4, "DL-4.md")):
                self.assertIn(f"[DL-{number}]({name})", index)
            self.assertIn("DL-4.md: ファイル名に DL- を付けない", built.stdout)
            self.assertIn("0001-Auth_PKCE.md: ファイル名は 0001.md か", built.stdout)
            self.assertNotIn("0002-認証の変更.md: ファイル名に DL-", built.stdout)
            self.assertIn("notes.md: ファイル名の先頭に 4 桁の番号がない", built.stdout)
            self.assertIn("2025-03-04-retry.md: ファイル名の先頭に 4 桁の番号がない", built.stdout)
            self.assertNotEqual(built.returncode, 0)

    def test_reports_malformed_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            d = pathlib.Path(directory)
            (d / "0001.md").write_text("# [demo] 形が崩れた log\n\n**起きたこと**\n- 上限が 5 に\n", encoding="utf-8")
            built = self.run_script(d)
            self.assertEqual(built.returncode, 1)
            self.assertIn("0001.md: フロントマターがない", built.stdout)
            self.assertIn("0001.md: 「## 起きたこと」", built.stdout)
            self.assertIn("0001.md: 「## 理由」", built.stdout)
            checked = self.run_script(d, "--check")
            self.assertEqual(checked.returncode, 1)
            self.assertNotIn("が古い", checked.stdout)


if __name__ == "__main__":
    unittest.main()
