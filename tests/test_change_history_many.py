"""change-history の build_many.py（複数のリポジトリを中央にまとめる）と、build_history.py の --repo・--show を、合成のリポジトリと
偽の gh（tests/fake_gh.py）で回す。GitHub の URL は、git の insteadOf で手元の合成のリポジトリに向ける。"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "change-history" / "scripts"
FAKE_GH = pathlib.Path(__file__).resolve().parent / "fake_gh.py"


class BuildManyTests(unittest.TestCase):

    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.work.name)
        self.central = self.base / "central"
        self.central.mkdir()
        (self.base / "bin").mkdir()
        (self.base / "bin/gh").write_text(f"#!/bin/sh\nexec {sys.executable} {FAKE_GH} \"$@\"\n", encoding="utf-8")
        (self.base / "bin/gh").chmod(0o755)
        (self.base / "gitconfig").write_text(f'[url "file://{self.base}/"]\n\tinsteadOf = https://github.com/\n', encoding="utf-8")
        self.gh = {"repos": {}}
        self.env = dict(os.environ, PATH=f"{self.base / 'bin'}{os.pathsep}{os.environ['PATH']}", FAKE_GH=str(self.base / "gh.json"),
                        GIT_CONFIG_GLOBAL=str(self.base / "gitconfig"))
        # o/app は 2024-11 から 2025-02 まで、o/lib は 2025-01 だけ
        self.make("o/app", [("Start app", "2024-11-10", None), ("Add login (#2)", "2025-02-03", 2)])
        self.make("o/lib", [("Start lib", "2025-01-05", None)])
        self.write_list("o/app\nhttps://github.com/o/lib --branch main  # 説明\n")

    def tearDown(self):
        self.work.cleanup()

    def git(self, repo, *args, date=None):
        env = dict(os.environ, GIT_AUTHOR_DATE=f"{date}T00:00:00Z", GIT_COMMITTER_DATE=f"{date}T00:00:00Z") if date else None
        return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True, env=env).stdout

    def make(self, name, commits):
        repo = self.base / f"{name}.git"  # GitHub の URL（…/o/app.git）が向く先
        repo.mkdir(parents=True)
        self.git(repo, "init", "-q", "-b", "main")
        self.git(repo, "config", "user.name", "Real Name")
        self.git(repo, "config", "user.email", "real@example.com")
        self.gh["repos"][name] = {"default": "main", "pulls": [], "commits": {}}
        for i, (subject, date, pr) in enumerate(commits):
            self.commit(name, f"{subject}-{i}", subject, date, pr)

    def commit(self, name, text, subject, date, pr=None):
        repo = self.base / f"{name}.git"  # GitHub の URL（…/o/app.git）が向く先
        (repo / "f.txt").write_text(text + "\n", encoding="utf-8")
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-q", "-m", subject, date=date)
        sha = self.git(repo, "rev-parse", "HEAD").strip()
        fixture = self.gh["repos"][name]
        if pr:
            fixture["pulls"].append({"number": pr, "login": "alice", "merged_at": f"{date}T00:00:00Z", "sha": sha,
                                     "title": subject.rsplit(" (#", 1)[0]})
        else:
            fixture["commits"][sha] = ["bob", "", ""]

    def write_list(self, text):
        (self.central / "repos.txt").write_text(text, encoding="utf-8")

    def call(self, *args):
        (self.base / "gh.json").write_text(json.dumps(self.gh), encoding="utf-8")
        return subprocess.run(args, cwd=self.central, capture_output=True, text=True, env=self.env)

    def many(self, *args):
        return self.call(sys.executable, str(SCRIPTS / "build_many.py"), "repos.txt", "docs/change-history", *args)

    def page(self, name):
        return (self.central / "docs/change-history" / name).read_text(encoding="utf-8")

    def test_builds_each_repository_and_an_overview(self):
        result = self.many()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # クローンは中央の .cache の下（git に入れない）。各リポジトリの年表は owner/repo の下に、今の形で
        self.assertTrue((self.central / ".cache/change-history/o/app/HEAD").exists())
        self.assertEqual((self.central / ".cache/change-history/.gitignore").read_text(encoding="utf-8"), "*\n")
        self.assertIn("| [2025-02](2025-02.md) | 1 | まだ |", self.page("o/app/README.md"))
        # 書き手に渡すもの
        self.assertIn("== o/app（置き場所 docs/change-history/o/app、--repo .cache/change-history/o/app --github-repo o/app）", result.stdout)
        self.assertIn("--github-repo o/lib --branch main）", result.stdout)
        overview = self.page("README.md")
        self.assertTrue(overview.startswith("# 変更の履歴\n\n## 2025\n\n### [o/app](o/app/README.md)\n\n（まだ書いていない）\n\n"
                                             "### [o/lib](o/lib/README.md)\n\n（まだ書いていない）\n\n| 月 | o/app | o/lib |"))
        self.assertIn("| 2025-02 | [1](o/app/2025-02.md) | 0 |", overview)
        self.assertIn("| 2024-11 | [1](o/app/2024-11.md) |\n", overview)
        self.assertEqual(self.many("--check").returncode, 0)

    def test_year_points_are_copied_and_quiet_months_collapse(self):
        self.make("o/old", [("Begin", "2023-01-01", None), ("End", "2023-06-01", None)])
        self.write_list("o/app\no/old\n")
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
        self.commit("o/lib", "x", "Fix lib (#3)", "2025-03-01", 3)
        self.assertEqual(self.many("--check").returncode, 0)  # 取らないので、いまのクローンのまま
        self.many()
        self.assertIn("| 2025-03 | 0 | [1](o/lib/2025-03.md) |", self.page("README.md"))

    def test_bad_lists_are_refused(self):
        for text, error in [("../x\n", "GitHub の owner/repo か、その URL"), ("https://gitlab.example.com/t/api.git\n", "GitHub の"),
                            ("o/a\no/A\n", "2 度ある"), ("o/a --since 2024-01\n", "書けるのは --branch・--depth だけ"),
                            ("o/a --branch\n", "値がない"), ("# 空\n", "リポジトリがない")]:
            with self.subTest(text=text):
                self.write_list(text)
                result = self.many()
                self.assertEqual(result.returncode, 1)
                self.assertIn(error, result.stderr)

    def test_writer_commands_read_another_repository(self):
        self.many()
        history = [sys.executable, str(SCRIPTS / "build_history.py"), "docs/change-history/o/app",
                   "--repo", ".cache/change-history/o/app", "--github-repo", "o/app"]
        listing = self.call(*history, "--list", "2025-02")
        self.assertIn("- 2025-02-03 Add login（[#2](https://github.com/o/app/pull/2)、（ルート）、@alice）", listing.stdout)
        self.assertIn("- 2024-11-10 Start app（[", self.call(*history, "--list", "2024-11").stdout)
        sha = self.git(self.base / "o/app.git", "rev-parse", "--short", "HEAD").strip()
        shown = self.call(*history, "--show", sha)
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertTrue(shown.stdout.startswith(f"{sha} 2025-02-03 Add login (#2)"))
        self.assertIn("f.txt", shown.stdout)
        # 人の名前とメールは出さない
        self.assertNotIn("Real Name", shown.stdout)
        self.assertNotIn("real@example.com", shown.stdout)
        missing = self.call(*history[:3], "--repo", "nowhere", "--list", "2025-02")
        self.assertEqual(missing.returncode, 2)
        self.assertIn("git のリポジトリではない", missing.stderr)


if __name__ == "__main__":
    unittest.main()
