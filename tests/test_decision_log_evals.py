"""evals/decision-log/run.py を偽のエージェントで動かすテスト。実際のモデルは呼ばない。"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = ROOT / "evals" / "decision-log" / "run.py"
sys.path.insert(0, str(RUNNER.parent))
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

    def test_keywords_are_matched_against_the_final_answer_only(self):
        # ツールの結果に出てくる言葉（ここでは「AI の印」）は、照合に数えない
        lines = [{"type": "user", "message": {"content": [{"type": "tool_result", "content": "AI の印 人の判断"}]}},
                 {"type": "result", "result": "理由は不明。"}]
        agent = [sys.executable, "-c", "import json; " + "; ".join(f"print(json.dumps({l!r}))" for l in lines)]
        result, _ = self.run_case(agent, "E02", "--skills-loaded")
        self.assertEqual(result["missing_keywords"], ["AI の印", "人の判断"])

    def test_subagents_are_counted_from_tool_calls(self):
        call = lambda name: {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Agent", "input": {"subagent_type": name}}]}}
        lines = [call("decision-continuity:decision-log-planner"), call("decision-log-reader"), {"type": "result", "result": "終わり"}]
        agent = [sys.executable, "-c", "import json; " + "; ".join(f"print(json.dumps({l!r}))" for l in lines)]
        result, _ = self.run_case(agent, "E07", "--skills-loaded")
        self.assertEqual(result["missing_agents"], [])
        result, _ = self.run_case([sys.executable, "-c", "print('自分で読んだ')"], "E07", "--skills-loaded")
        self.assertEqual(result["missing_agents"], ["decision-log-planner", "decision-log-reader"])

    def test_renamed_seed_file_counts_as_rewritten_instead_of_crashing(self):
        rename = [sys.executable, "-c", "import pathlib; p = pathlib.Path('docs/decision-logs'); (p / '0001.md').rename(p / '0001-retry.md')"]
        result, _ = self.run_case(rename, "E06", "--skills-loaded")
        self.assertEqual(result["files"]["rewritten_existing"], ["0001.md"])

    def test_recheck_case_counts_a_good_addendum(self):
        add = [sys.executable, "-c", "import pathlib, subprocess, sys; p = pathlib.Path('docs/decision-logs/0001.md'); "
               "head = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip(); "
               "import re; t = re.sub(r'checked: \\w+', 'checked: ' + head, p.read_text()); "
               "p.write_text(t + f'\\n---\\n\\n## 追記 2026-01-01（x）\\n\\n**いま**（{head}）：上限は 5。\\n\\n"
               "- 上限の行は置き換え済みになった：PR #13 で 3 から 5 になった（1 日後）\\n- タイムアウトの行はいまも同じ\\n'); "
               "subprocess.run([sys.executable, '.claude/skills/decision-log/scripts/build_index.py', 'docs/decision-logs'])"]
        result, _ = self.run_case(add, "E10", "--skills-loaded")
        files = result["files"]
        self.assertEqual((files["missing_facts"], files["rewritten_existing"], files["stale_after"], files["index_check"]),
                         ([], [], False, True), files)
        result, _ = self.run_case([sys.executable, "-c", "print('見た')"], "E10", "--skills-loaded")
        self.assertTrue(result["files"]["stale_after"])

    def test_answer_key_reports_missing_facts(self):
        write = [sys.executable, "-c", "import pathlib, subprocess, sys; d = pathlib.Path('docs/decision-logs'); d.mkdir(parents=True); "
                 "(d / '0001.md').write_text('---\\nkind: log\\ncategory: reliability\\n---\\n\\n# [payment-api] x\\n\\n## 起きたこと\\n\\n"
                 "- 2025-01-11 いまも同じ：MAX_RETRIES が 3 から 5 になった。履歴：PR #13 ／ 現在：client.py:1\\n\\n## 理由\\n\\n不明（記録に書かれていない）。\\n'); "
                 "subprocess.run([sys.executable, '.claude/skills/decision-log/scripts/build_index.py', str(d)])"]
        result, _ = self.run_case(write, "E05", "--skills-loaded")
        self.assertTrue(result["files"]["index_check"], result["files"]["index_output"])
        self.assertEqual(result["files"]["missing_facts"], ["PR #12（TIMEOUT）", "TIMEOUT の前後", "#12 はタイトルと中身が違う"])

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
    """decision-log-planner に書いた候補の洗い出しを、合成の履歴で実際に回す。"""

    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.work.name) / "payment-api"
        run.build_repo(self.repo)
        doc = (ROOT / "agents/claude/decision-log-planner.md").read_text(encoding="utf-8")
        self.words = re.search(r"既定：`([^`]+)`", doc).group(1)
        self.constant = re.search(r"定数・設定の値の変更：`([^`]+)`", doc).group(1)
        config_line = next(l for l in doc.splitlines() if "設定ファイルの変更" in l)
        self.config_globs = re.findall(r"'(\*\.[a-z]+)'", config_line)

    def tearDown(self):
        self.work.cleanup()

    def subjects(self, *args):
        return run.git(self.repo, "log", "--first-parent", "--format=%s", *args).splitlines()

    def scan(self):
        """planner の手順 3：3 つを別々に回して合わせる。"""
        exclude = ["--", ".", ":(exclude)*lock*", ":(exclude)*.snap"]
        return (set(self.subjects("-i", "-G", self.words, *exclude))
                | set(self.subjects("-G", self.constant, *exclude))
                | set(self.subjects("--", *self.config_globs, ":(exclude)*lock*")))

    def test_diff_scan_catches_misleading_titles_and_skips_cosmetic_changes(self):
        hits = self.scan()
        for subject in ("Merge pull request #12 from example/fix-typo", "Bump retry count (#13)",
                        "Lower webhook timeout to 3s (#14)", "Extend session (#17)", "Keep logs longer (#18)",
                        "Rotate webhook secret (#19)", "Merge pull request #22 from example/db-pool"):
            self.assertIn(subject, hits)
        for subject in ("Update button padding (#16)", "Refactor helper (#20)"):
            self.assertNotIn(subject, hits)

    def test_case_insensitive_flag_does_not_leak_into_the_constant_pattern(self):
        # 1 本につないで -i を付けると、ふつうの代入（result = ...）まで当たる。手順書が分けている理由
        joined = self.subjects("-i", "-G", f"{self.words}|{self.constant}", "--", ".")
        self.assertIn("Refactor helper (#20)", joined)
        self.assertNotIn("Refactor helper (#20)", self.scan())

    def test_reason_of_pr_22_is_only_in_its_inner_commit(self):
        # E09：--first-parent の一覧には出ず、マージの親 1 からの範囲で読むと見える（reader の手順 2）
        merge = run.git(self.repo, "log", "--first-parent", "--merges", "--format=%h", "--grep", "#22").strip()
        self.assertNotIn("2025-03-18", run.git(self.repo, "log", "--first-parent", "--format=%B"))
        self.assertIn("ran dry during the 2025-03-18 nightly batch", run.git(self.repo, "log", "--format=%B", f"{merge}^1..{merge}"))

    def test_merge_commit_body_gives_the_pr_title(self):
        bodies = run.git(self.repo, "log", "--first-parent", "--merges", "--format=@@ %h %b")
        self.assertRegex(bodies, r"@@ [0-9a-f]+ Fix typo in README")


if __name__ == "__main__":
    unittest.main()
