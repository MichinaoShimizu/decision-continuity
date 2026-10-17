"""evals/run.py を偽のエージェントで動かすテスト。実際のモデルは呼ばない。"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = ROOT / "evals" / "run.py"
sys.path.insert(0, str(ROOT / "evals"))
import run  # noqa: E402


class RunnerTests(unittest.TestCase):
    def run_case(self, agent, case, *extra):
        with tempfile.TemporaryDirectory() as out:
            done = subprocess.run([sys.executable, str(RUNNER), "--agent-version", "fake", "--agent-argv-json", json.dumps(agent),
                                   "--output", out, "--case", case, "--timeout", "30", *extra],
                                  capture_output=True, text=True, timeout=120)
            self.assertEqual(done.returncode, 0, done.stderr)
            manifest = json.loads((pathlib.Path(out) / "manifest.json").read_text(encoding="utf-8"))
            return manifest["results"][0], (pathlib.Path(out) / f"{case}.response.txt").read_text(encoding="utf-8")

    def test_workspace_has_history_and_installed_kit(self):
        agent = [sys.executable, "-c", "import subprocess, pathlib; "
                 "print(subprocess.run(['git', 'log', '--first-parent', '--merges', '--format=%b'], capture_output=True, text=True).stdout); "
                 "print(sorted(str(p) for p in pathlib.Path('.').glob('.*/*/decision-log*')))"]
        result, response = self.run_case(agent, "E01", "--skills-loaded")
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertIn("Fix typo in README", response)
        for path in (".claude/skills/decision-log", ".kiro/skills/decision-log",
                     ".claude/agents/decision-log-reader.md", ".kiro/agents/decision-log-reader.json"):
            self.assertIn(path, response)

    def test_without_attestation_is_inconclusive(self):
        result, _ = self.run_case([sys.executable, "-c", "print('x')"], "E04")
        self.assertEqual(result["status"], "INCONCLUSIVE")

    def test_failed_agent_is_inconclusive(self):
        result, _ = self.run_case([sys.executable, "-c", "import sys; sys.exit(3)"], "E04", "--skills-loaded")
        self.assertEqual((result["status"], result["exit_code"]), ("INCONCLUSIVE", 3))

    def test_file_checks_catch_a_rewritten_log(self):
        rewrite = [sys.executable, "-c", "import pathlib; p = pathlib.Path('docs/decision-logs/0001.md'); "
                   "p.write_text(p.read_text().replace('不明', '監査の指摘'))"]
        result, _ = self.run_case(rewrite, "E06", "--skills-loaded")
        self.assertEqual(result["files"]["rewritten_existing"], ["0001.md"])
        append = [sys.executable, "-c", "import pathlib; p = pathlib.Path('docs/decision-logs/0001.md'); "
                  "p.write_text(p.read_text() + '\\n---\\n\\n## 追記 2026-01-01（x）\\n\\n**分かった**（2026-01-01）：「なぜ 5 にしたか」\\n外部監査。@alice。元の場所なし\\n'); import subprocess, sys; subprocess.run([sys.executable, '.claude/skills/decision-log/scripts/build_index.py', 'docs/decision-logs'])"]
        result, _ = self.run_case(append, "E06", "--skills-loaded")
        self.assertEqual(result["files"]["rewritten_existing"], [])
        self.assertTrue(result["files"]["index_check"], result["files"]["index_output"])


class CandidateScanTests(unittest.TestCase):
    """references/investigation.md に書いた候補の洗い出しを、合成の履歴で実際に回す。"""

    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.work.name) / "payment-api"
        run.build_repo(self.repo)
        doc = (ROOT / "skills/decision-log/references/investigation.md").read_text(encoding="utf-8")
        self.words = re.search(r"既定：`([^`]+)`", doc).group(1)
        self.constant = re.search(r"定数・設定の値の変更：`([^`]+)`", doc).group(1)

    def tearDown(self):
        self.work.cleanup()

    def subjects(self, *args):
        return run.git(self.repo, "log", "--first-parent", "--format=%s", *args).splitlines()

    def test_diff_scan_catches_misleading_titles_and_skips_cosmetic_changes(self):
        hits = self.subjects("-i", "-G", f"{self.words}|{self.constant}", "--", ".", ":(exclude)*lock*", ":(exclude)*.snap")
        for subject in ("Merge pull request #12 from example/fix-typo", "Bump retry count (#13)",
                        "Lower webhook timeout to 3s (#14)", "Extend session (#17)"):
            self.assertIn(subject, hits)
        self.assertNotIn("Update button padding (#16)", hits)

    def test_merge_commit_body_gives_the_pr_title(self):
        bodies = run.git(self.repo, "log", "--first-parent", "--merges", "--format=@@ %h %b")
        self.assertRegex(bodies, r"@@ [0-9a-f]+ Fix typo in README")


if __name__ == "__main__":
    unittest.main()
