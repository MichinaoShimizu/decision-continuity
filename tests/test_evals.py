"""evals/run.py を偽のエージェントで動かすテスト。実際のモデルは呼ばない。"""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

RUNNER = pathlib.Path(__file__).resolve().parents[1] / "evals" / "run.py"


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


if __name__ == "__main__":
    unittest.main()
