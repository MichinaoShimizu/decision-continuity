"""change-history の build_history.py を、合成のリポジトリで回す。"""
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "change-history" / "scripts" / "build_history.py"


class BuildHistoryTests(unittest.TestCase):

    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.work.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "main-user")
        self.git("config", "user.email", "m@example.com")
        self.git("remote", "add", "origin", "git@github.com:o/r.git")
        # 2025-01-31 23:30 UTC は JST で 2025-02-01
        self.commit("README.md", "a", "Initial import", "2025-01-10T00:00:00Z")
        self.commit("src/auth/session.py", "TTL = 24", "Extend session (#2)", "2025-01-31T23:30:00Z")
        self.git("switch", "-q", "-c", "feature")
        self.git("config", "user.name", "alice")
        self.commit("src/payment/client.py", "MAX = 5", "Raise retries", "2025-02-03T00:00:00Z")
        self.write("docs/retry.md", "5")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "Document retries", env={"GIT_AUTHOR_DATE": "2025-02-03T00:00:00Z", "GIT_COMMITTER_DATE": "2025-02-03T00:00:00Z"})
        self.git("switch", "-q", "main")
        self.git("config", "user.name", "merger")
        self.git("merge", "-q", "--no-ff", "feature", "-m", "Merge pull request #3 from o/feature\n\nRaise payment retries",
                 env={"GIT_AUTHOR_DATE": "2025-02-04T00:00:00Z", "GIT_COMMITTER_DATE": "2025-02-04T00:00:00Z"})

    def tearDown(self):
        self.work.cleanup()

    def git(self, *args, env=None):
        return subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True, check=True,
                              env=dict(os.environ, **(env or {}))).stdout

    def write(self, path, text):
        (self.repo / path).parent.mkdir(parents=True, exist_ok=True)
        (self.repo / path).write_text(text + "\n", encoding="utf-8")

    def commit(self, path, text, message, date):
        self.write(path, text)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message, env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})

    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "docs/change-history", *args], cwd=self.repo,
                              capture_output=True, text=True, check=False)

    def page(self, name):
        return (self.repo / "docs/change-history" / name).read_text(encoding="utf-8")

    def test_months_prs_authors_and_places(self):
        self.assertEqual(self.run_script().returncode, 0)
        jan, feb = self.page("2025-01.md"), self.page("2025-02.md")
        self.assertIn("マージされた変更 1 件", jan)
        self.assertIn("- 01-10 Initial import（[", jan)
        # JST で月をまたぐ。squash の (#2) は PR の番号になり、件名から外れる
        self.assertIn("- 02-01 Extend session（[#2](https://github.com/o/r/pull/2) main-user、src/auth/）", feb)
        # マージコミットは、本文の 1 行目をタイトルに、取り込んだ側の author を作成者に、両方の置き場所を数える
        self.assertIn("- 02-04 Raise payment retries（[#3](https://github.com/o/r/pull/3) alice、docs/ ほか 1）", feb)
        self.assertNotIn("Raise retries（", feb)
        index = self.page("README.md")
        self.assertIn("| [2025-02](2025-02.md) | 2 | まだ |", index)
        self.assertLess(index.index("2025-02"), index.index("2025-01"))

    def test_summary_survives_rebuilds_and_check(self):
        self.run_script()
        path = self.repo / "docs/change-history/2025-02.md"
        path.write_text(path.read_text(encoding="utf-8").replace("（まだ書いていない）", "- 決済の再試行を増やした（#3）"), encoding="utf-8")
        self.assertEqual(self.run_script("--check").returncode, 1)  # 索引の「まだ」が古い
        self.assertEqual(self.run_script().returncode, 0)
        self.assertIn("- 決済の再試行を増やした（#3）", self.page("2025-02.md"))
        self.assertIn("| [2025-02](2025-02.md) | 2 | あり |", self.page("README.md"))
        self.assertEqual(self.run_script("--check").returncode, 0)
        self.commit("src/auth/session.py", "TTL = 48", "Longer session (#4)", "2025-02-10T00:00:00Z")
        self.assertEqual(self.run_script("--check").returncode, 1)

    def test_since_and_depth(self):
        self.run_script("--since", "2025-02", "--depth", "1")
        self.assertFalse((self.repo / "docs/change-history/2025-01.md").exists())
        self.assertIn("main-user、src/）", self.page("2025-02.md"))
        self.assertEqual(self.run_script("--since", "2025-2").returncode, 2)


if __name__ == "__main__":
    unittest.main()
