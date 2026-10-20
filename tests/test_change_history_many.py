"""change-history の build_many.py（複数のリポジトリを中央にまとめる）と、build_history.py の --repo・--show を、合成のリポジトリで回す。"""
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "change-history" / "scripts"


class BuildManyTests(unittest.TestCase):

    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.work.name)
        self.central = self.base / "central"
        self.central.mkdir()
        # o/app は 2024-11 から 2025-02 まで、o/lib は 2025-01 だけ
        self.make("o/app", [("Start app", "2024-11-10"), ("Add login (#2)", "2025-02-03")])
        self.make("o/lib", [("Start lib", "2025-01-05")])
        self.write_list(f"file://{self.base}/o/app\nfile://{self.base}/o/lib --branch main  # 説明\n")

    def tearDown(self):
        self.work.cleanup()

    def git(self, repo, *args, date=None):
        env = dict(os.environ, GIT_AUTHOR_DATE=f"{date}T00:00:00Z", GIT_COMMITTER_DATE=f"{date}T00:00:00Z") if date else None
        return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True, env=env).stdout

    def make(self, name, commits):
        repo = self.base / name
        repo.mkdir(parents=True)
        self.git(repo, "init", "-q", "-b", "main")
        self.git(repo, "config", "user.name", "Real Name")
        self.git(repo, "config", "user.email", "real@example.com")
        for i, (subject, date) in enumerate(commits):
            self.commit(repo, f"{subject}-{i}", subject, date)

    def commit(self, repo, text, subject, date):
        (repo / "f.txt").write_text(text + "\n", encoding="utf-8")
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-q", "-m", subject, date=date)

    def write_list(self, text):
        (self.central / "repos.txt").write_text(text, encoding="utf-8")

    def many(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / "build_many.py"), "repos.txt", "docs/change-history", "--no-github", *args],
                              cwd=self.central, capture_output=True, text=True)

    def page(self, name):
        return (self.central / "docs/change-history" / name).read_text(encoding="utf-8")

    def test_builds_each_repository_and_an_overview(self):
        result = self.many()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # クローンは中央の .cache の下（git に入れない）。各リポジトリの年表は owner/repo の下に、今の形で
        self.assertTrue((self.central / ".cache/change-history/o/app/HEAD").exists())
        self.assertEqual((self.central / ".cache/change-history/.gitignore").read_text(encoding="utf-8"), "*\n")
        self.assertIn("| [2025-02](2025-02.md) | 1 | まだ |", self.page("o/app/README.md"))
        self.assertIn("| 2024-12 | 0 | 変更なし |", self.page("o/app/README.md"))
        # 書き手に渡す置き場所と --repo・--branch を出す
        self.assertIn("== o/lib（置き場所 docs/change-history/o/lib、--repo .cache/change-history/o/lib --branch main）", result.stdout)
        overview = self.page("README.md")
        # 年ごとに、リポジトリごとの要点と、月 × リポジトリの件数。まだなかった月は空、最後の変更より後は 0
        self.assertEqual(overview, "\n".join([
            "# 変更の履歴", "",
            "## 2025", "",
            "### [o/app](o/app/README.md)", "", "（まだ書いていない）", "",
            "### [o/lib](o/lib/README.md)", "", "（まだ書いていない）", "",
            "| 月 | o/app | o/lib |", "|---|---|---|",
            "| 2025-02 | [1](o/app/2025-02.md) | 0 |",
            "| 2025-01 | 0 | [1](o/lib/2025-01.md) |", "",
            "## 2024", "",
            "### [o/app](o/app/README.md)", "", "（まだ書いていない）", "",
            "| 月 | o/app |", "|---|---|",
            "| 2024-12 | 0 |",
            "| 2024-11 | [1](o/app/2024-11.md) |"]) + "\n")
        self.assertEqual(self.many("--check").returncode, 0)

    def test_year_points_are_copied_and_quiet_months_collapse(self):
        self.make("o/old", [("Begin", "2023-01-01"), ("End", "2023-06-01")])
        self.write_list(f"file://{self.base}/o/app\nfile://{self.base}/o/old\n")
        self.many()
        path = self.central / "docs/change-history/o/old/README.md"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "## 2023\n\n（まだ書いていない）", "## 2023\n\n- 始めて、終えた（2023-01〜2023-06）"), encoding="utf-8")
        self.many()
        overview = self.page("README.md")
        # 年の要点はそのまま写す。変更のなかった年は「変更なし」
        self.assertIn("### [o/old](o/old/README.md)\n\n- 始めて、終えた（2023-01〜2023-06）", overview)
        self.assertIn("## 2024\n\n### [o/app](o/app/README.md)\n\n（まだ書いていない）\n\n### [o/old](o/old/README.md)\n\n変更なし", overview)
        # どこにも変更のない月が続けば 1 行。マスが変われば分ける
        self.assertIn("| 2023-07〜2023-12 | 0 |", overview)
        self.assertIn("| 2024-11 | [1](o/app/2024-11.md) | 0 |\n| 2024-01〜2024-10 |  | 0 |\n", overview)

    def test_fetches_new_changes_and_check_does_not(self):
        self.many()
        self.commit(self.base / "o/lib", "x", "Fix lib (#3)", "2025-03-01")
        self.assertEqual(self.many("--check").returncode, 0)  # 取らないので、いまのクローンのまま
        self.many()
        self.assertIn("| 2025-03 | 0 | [1](o/lib/2025-03.md) |", self.page("README.md"))

    def test_bad_lists_are_refused(self):
        for text, error in [("../x\n", "owner/repo か clone できる URL"), ("o/a\no/A\n", "2 度ある"),
                            ("o/a --since 2024-01\n", "書けるのは --branch・--depth だけ"), ("o/a --branch\n", "値がない"),
                            ("# 空\n", "リポジトリがない")]:
            with self.subTest(text=text):
                self.write_list(text)
                result = self.many()
                self.assertEqual(result.returncode, 1)
                self.assertIn(error, result.stderr)

    def test_writer_commands_read_another_repository(self):
        self.many()
        history = [sys.executable, str(SCRIPTS / "build_history.py"), "docs/change-history/o/app",
                   "--repo", ".cache/change-history/o/app", "--no-github"]
        listing = subprocess.run([*history, "--list", "2025-02"], cwd=self.central, capture_output=True, text=True)
        self.assertIn("- 2025-02-03 Add login（#2、（ルート）、—）", listing.stdout)
        sha = self.git(self.base / "o/app", "rev-parse", "--short", "HEAD").strip()
        shown = subprocess.run([*history, "--show", sha], cwd=self.central, capture_output=True, text=True)
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertTrue(shown.stdout.startswith(f"{sha} 2025-02-03 Add login (#2)"))
        self.assertIn("f.txt", shown.stdout)
        # 人の名前とメールは出さない
        self.assertNotIn("Real Name", shown.stdout)
        self.assertNotIn("real@example.com", shown.stdout)
        missing = subprocess.run([*history[:3], "--repo", "nowhere", "--list", "2025-02"], cwd=self.central, capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)
        self.assertIn("git のリポジトリではない", missing.stderr)


if __name__ == "__main__":
    unittest.main()
