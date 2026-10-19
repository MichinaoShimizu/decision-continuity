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

    def test_months_prs_and_places(self):
        self.assertEqual(self.run_script().returncode, 0)
        jan, feb = self.page("2025-01.md"), self.page("2025-02.md")
        self.assertIn("マージされた変更 1 件", jan)
        self.assertIn("- 2025-01-10 Initial import（[", jan)
        # JST で月をまたぐ。squash の (#2) は PR の番号になり、件名から外れる
        self.assertIn("- 2025-02-01 Extend session（[#2](https://github.com/o/r/pull/2)、src/auth/）", feb)
        # マージコミットは、本文の 1 行目をタイトルに、両方の置き場所を数える
        self.assertIn("- 2025-02-04 Raise payment retries（[#3](https://github.com/o/r/pull/3)、docs/ ほか 1）", feb)
        # 人の名前は書き出さない
        for name in ("main-user", "alice", "merger"):
            self.assertNotIn(name, feb)
        self.assertNotIn("Raise retries（", feb)
        index = self.page("README.md")
        # 索引が年表を兼ねる。主な変更をまだ書いていない月は「まだ」
        self.assertIn("## 2025\n\n（まだ書いていない）\n\n| 月 | 件数 | 主な変更 |", index)
        self.assertIn("| [2025-02](2025-02.md) | 2 | まだ |", index)
        self.assertFalse((self.repo / "docs/change-history/timeline.md").exists())
        self.assertLess(index.index("2025-02"), index.index("2025-01"))

    def test_summary_survives_rebuilds_and_check(self):
        self.run_script()
        path = self.repo / "docs/change-history/2025-02.md"
        path.write_text(path.read_text(encoding="utf-8").replace("（まだ書いていない）", "- 決済の再試行を増やした（#3）"), encoding="utf-8")
        self.assertEqual(self.run_script("--check").returncode, 1)  # 索引の「まだ」が古い
        self.assertEqual(self.run_script().returncode, 0)
        self.assertIn("- 決済の再試行を増やした（#3）", self.page("2025-02.md"))
        self.assertIn("| [2025-02](2025-02.md) | 2 | 決済の再試行を増やした（#3） |", self.page("README.md"))
        self.assertEqual(self.run_script("--check").returncode, 0)
        self.commit("src/auth/session.py", "TTL = 48", "Longer session (#4)", "2025-02-10T00:00:00Z")
        self.assertEqual(self.run_script("--check").returncode, 1)

    def test_timeline_collects_first_points_and_keeps_year_summaries(self):
        self.run_script()
        timeline = self.page("README.md")
        self.assertLess(timeline.index("## 2025"), timeline.index("| [2025-02](2025-02.md) | 2 | まだ |"))
        self.assertLess(timeline.index("| [2025-02](2025-02.md)"), timeline.index("| [2025-01](2025-01.md) | 1 | まだ |"))
        path = self.repo / "docs/change-history/2025-02.md"
        path.write_text(path.read_text(encoding="utf-8").replace("（まだ書いていない）", "- 決済の再試行を a|b に（#3）\n- 小さなこと"), encoding="utf-8")
        self.run_script()
        self.assertIn("| [2025-02](2025-02.md) | 2 | 決済の再試行を a\\|b に（#3） |", self.page("README.md"))
        path = self.repo / "docs/change-history/README.md"
        path.write_text(path.read_text(encoding="utf-8").replace("（まだ書いていない）", "- 決済の再試行を見直した（2025-02）"), encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 0)
        self.assertIn("## 2025\n\n- 決済の再試行を見直した（2025-02）\n\n| 月 |", self.page("README.md"))
        self.assertEqual(self.run_script("--check").returncode, 0)

    def test_summaries_by_category(self):
        # 主な変更と年の要点は分類ごとの見出しで書く。作り直しても残り、表には最初の行が入る
        self.run_script()
        folder = self.repo / "docs/change-history"
        month = "### reliability\n\n- 決済の再試行を 5 回に（#3）\n\n### security\n\n- セッションを延ばした（#2）\n- もう 1 つ（#2）"
        path = folder / "2025-02.md"
        path.write_text(path.read_text(encoding="utf-8").replace("（まだ書いていない）", month), encoding="utf-8")
        self.run_script()
        year = "### reliability\n\n- 決済の再試行を見直した（2025-02）"
        path = folder / "README.md"
        path.write_text(path.read_text(encoding="utf-8").replace("（まだ書いていない）", year), encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 0)
        self.assertIn(f"## 主な変更\n\n{month}\n\n## 一覧", self.page("2025-02.md"))
        readme = self.page("README.md")
        self.assertIn(f"## 2025\n\n{year}\n\n| 月 |", readme)
        self.assertIn("| [2025-02](2025-02.md) | 2 | 決済の再試行を 5 回に（#3） |", readme)
        self.assertEqual(self.run_script("--check").returncode, 0)

    def test_old_timeline_moves_into_readme(self):
        self.run_script()
        folder = self.repo / "docs/change-history"
        (folder / "README.md").write_text("# 変更の履歴\n\n| 月 | 件数 | 主な変更を書いたか |\n", encoding="utf-8")
        (folder / "timeline.md").write_text("# 年表\n\n## 2025\n\n- 前に書いた要点（2025-02）\n\n| 月 | 件数 | 主な変更 |\n", encoding="utf-8")
        self.assertEqual(self.run_script("--check").returncode, 1)
        self.assertEqual(self.run_script().returncode, 0)
        self.assertIn("## 2025\n\n- 前に書いた要点（2025-02）\n\n| 月 |", self.page("README.md"))
        self.assertFalse((folder / "timeline.md").exists())
        self.assertEqual(self.run_script("--check").returncode, 0)

    def test_branch_syncs_are_marked(self):
        self.git("switch", "-q", "-c", "stable")
        self.commit("src/auth/session.py", "TTL = 36", "Fix on stable", "2025-03-01T00:00:00Z")
        self.git("switch", "-q", "main")
        self.git("merge", "-q", "--no-ff", "stable", "-m", "Merge branch 'stable'",
                 env={"GIT_AUTHOR_DATE": "2025-03-02T00:00:00Z", "GIT_COMMITTER_DATE": "2025-03-02T00:00:00Z"})
        self.run_script()
        self.assertIn("- 2025-03-02 （ブランチの取り込み）Merge branch 'stable'（[", self.page("2025-03.md"))

    def test_releases_are_marked(self):
        for i, subject in enumerate(["Release v0.8.0 (#90)", "Bump version to 1.2.0", "chore(release): 1.3.0", "v1.4.0",
                                     "Release automation for the docs site (#91)", "Bump requests from 2.31 to 2.32"]):
            self.commit("CHANGELOG.md", str(i), subject, f"2025-04-0{i + 1}T00:00:00Z")
        self.run_script()
        april = self.page("2025-04.md")
        for line in ["- 2025-04-01 （リリース）Release v0.8.0（[#90]", "- 2025-04-02 （リリース）Bump version to 1.2.0（",
                     "- 2025-04-03 （リリース）chore(release): 1.3.0（", "- 2025-04-04 （リリース）v1.4.0（",
                     "- 2025-04-05 Release automation for the docs site（[#91]", "- 2025-04-06 Bump requests from 2.31 to 2.32（"]:
            self.assertIn(line, april)

    def merge(self, branch, message, date):
        self.git("merge", "-q", "--no-ff", branch, "-m", message, env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})

    def test_development_and_production_branches(self):
        # 機能の修正は develop へ、リリースは develop から main へ、緊急の修正は main へ直接
        self.git("switch", "-q", "-c", "develop")
        self.git("switch", "-q", "-c", "feature-x")
        self.commit("src/search/index.py", "LIMIT = 50", "Raise search limit", "2025-05-01T00:00:00Z")
        self.git("switch", "-q", "develop")
        self.merge("feature-x", "Merge pull request #10 from o/feature-x\n\nRaise search limit", "2025-05-02T00:00:00Z")
        self.git("switch", "-q", "main")
        self.merge("develop", "Merge pull request #11 from o/develop\n\nRelease 2025-05", "2025-05-03T00:00:00Z")
        self.commit("src/auth/session.py", "TTL = 12", "Shorten session (#12)", "2025-05-04T00:00:00Z")
        self.git("switch", "-q", "develop")
        self.merge("main", "Merge branch 'main' into develop", "2025-05-05T00:00:00Z")
        self.git("switch", "-q", "main")
        # develop が origin にしかなくても読む
        self.git("update-ref", "refs/remotes/origin/develop", "develop")
        self.git("branch", "-q", "-D", "develop", "feature-x")
        # 手元の main が古くても、origin/main を読む
        self.git("update-ref", "refs/remotes/origin/main", "main")
        self.git("update-ref", "refs/heads/main", "main~1")
        self.git("switch", "-q", "--detach", "origin/main")
        self.assertEqual(self.run_script().returncode, 0)
        may = self.page("2025-05.md")
        for line in ["- 2025-05-02 Raise search limit（[#10](https://github.com/o/r/pull/10)、src/search/、develop へ）",
                     "- 2025-05-03 （develop から取り込み）Release 2025-05（[#11](https://github.com/o/r/pull/11)、",
                     "- 2025-05-04 Shorten session（[#12](https://github.com/o/r/pull/12)、src/auth/、main へ）",
                     "- 2025-05-05 （main から取り込み）Merge branch 'main' into develop（["]:
            self.assertIn(line, may)
        # どちらにも入ったコミットは 1 件
        self.assertEqual(self.page("2025-02.md").count("Extend session"), 1)
        self.assertIn("Extend session（[#2](https://github.com/o/r/pull/2)、src/auth/、main・develop へ）", self.page("2025-02.md"))
        self.assertIn("読んだブランチ：main（origin/main）、develop（origin/develop）。", self.page("README.md"))
        # 1 つに絞れば、ブランチは書かない
        self.assertEqual(self.run_script("--branch", "main").returncode, 0)
        self.assertNotIn("Raise search limit（", self.page("2025-05.md"))
        self.assertNotIn(" へ）", self.page("2025-05.md"))
        self.assertEqual(self.run_script("--branch", "nope").returncode, 2)

    def test_since_and_depth(self):
        self.run_script("--since", "2025-02", "--depth", "1")
        self.assertFalse((self.repo / "docs/change-history/2025-01.md").exists())
        self.assertIn("pull/2)、src/）", self.page("2025-02.md"))
        self.assertEqual(self.run_script("--since", "2025-2").returncode, 2)


if __name__ == "__main__":
    unittest.main()
