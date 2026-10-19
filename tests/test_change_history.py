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
        self.git("config", "user.name", "Alice Example")
        self.git("config", "user.email", "123+alice@users.noreply.github.com")
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

    def listing(self, month, *args):
        result = self.run_script("--list", month, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def fill(self, month, text):
        path = self.repo / "docs/change-history" / f"{month}.md"
        path.write_text(path.read_text(encoding="utf-8").replace("（まだ書いていない）", text), encoding="utf-8")

    def page(self, name):
        return (self.repo / "docs/change-history" / name).read_text(encoding="utf-8")

    def test_months_prs_and_places(self):
        self.assertEqual(self.run_script().returncode, 0)
        # 月のファイルは見出しと主な変更だけ。全変更の一覧と件数の文は書かない
        self.assertEqual(self.page("2025-02.md"), "# 2025-02\n\n## 主な変更\n\n（まだ書いていない）\n")
        jan, feb = self.listing("2025-01"), self.listing("2025-02")
        self.assertIn("- 2025-01-10 Initial import（[", jan)
        # JST で月をまたぐ。squash の (#2) は PR の番号になり、件名から外れる。noreply でないメールの Author は —
        self.assertIn("- 2025-02-01 Extend session（[#2](https://github.com/o/r/pull/2)、src/auth/、—）", feb)
        # マージコミットは、本文の 1 行目をタイトルに、両方の置き場所を数え、Author は取り込んだ側のアカウント名
        self.assertIn("- 2025-02-04 Raise payment retries（[#3](https://github.com/o/r/pull/3)、docs/ ほか 1、@alice）", feb)
        self.assertIn("2025-02：2 件。読んだブランチ：main", feb)
        # 人の名前は書き出さない（マージした人も出ない）
        for name in ("main-user", "Alice Example", "merger"):
            self.assertNotIn(name, feb)
        # マージコミットの下に、PR の中のコミット（実際の改修）を字下げして並べる
        self.assertRegex(feb, r"、@alice）\n  - Raise retries（\[[0-9a-f]{7}\]\(https://github.com/o/r/commit/[0-9a-f]{40}\)、@alice）\n"
                              r"  - Document retries（\[[0-9a-f]{7}\]")
        index = self.page("README.md")
        # 索引が年表を兼ねる。h1 の直下に文を置かない。主な変更をまだ書いていない月は「まだ」
        self.assertTrue(index.startswith("# 変更の履歴\n\n## 2025\n\n（まだ書いていない）\n\n| 月 | 件数 | 主な変更 |"))
        self.assertIn("| [2025-02](2025-02.md) | 2 | まだ |", index)
        self.assertFalse((self.repo / "docs/change-history/timeline.md").exists())
        self.assertLess(index.index("2025-02"), index.index("2025-01"))
        self.assertEqual(self.run_script("--list", "2025-2").returncode, 2)

    def test_summary_table_is_filled_from_the_changes(self):
        # 概要と PR だけ書けば、日付・Author・PR のリンクと分類の説明はスクリプトが入れる
        self.run_script()
        self.fill("2025-02", "### reliability\n\n| 日付 | 概要 | PR | Author |\n|---|---|---|---|\n|  | 決済の再試行を増やした | #3 |  |")
        self.assertEqual(self.run_script("--check").returncode, 1)  # 表と索引が古い
        # 月の要約は年表の表に人か AI が書く。まだなければ崩れとして知らせる
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("README.md の 2025-02：主な変更の要約（表の「主な変更」の列）がない", result.stdout)
        self.assertIn("| [2025-02](2025-02.md) | 2 | まだ |", self.page("README.md"))
        path = self.repo / "docs/change-history/README.md"
        path.write_text(path.read_text(encoding="utf-8").replace("| 2 | まだ |", "| 2 | 決済の再試行とセッションを見直した |"), encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 0)
        self.assertEqual(self.page("2025-02.md"), "\n".join([
            "# 2025-02", "", "## 主な変更", "", "### reliability", "",
            "性能・信頼性：負荷や障害のときの振る舞い。タイムアウト、リトライ、上限、キャッシュ、縮退", "",
            "| 日付 | 概要 | PR | Author |", "|---|---|---|---|",
            "| 2025-02-04 | 決済の再試行を増やした | [#3](https://github.com/o/r/pull/3) | @alice |"]) + "\n")
        # 要約は作り直しても残る
        self.assertIn("| [2025-02](2025-02.md) | 2 | 決済の再試行とセッションを見直した |", self.page("README.md"))
        self.assertEqual(self.run_script("--check").returncode, 0)
        # 間違えた日付と Author は直す。いくつかの PR をまとめた行は、最初の日付と Author を重ねずに
        path = self.repo / "docs/change-history/2025-02.md"
        path.write_text(path.read_text(encoding="utf-8").replace("| 2025-02-04 | 決済の再試行を増やした | [#3](https://github.com/o/r/pull/3) | @alice |",
                                                                 "| 2025-02-09 | 決済とセッション | #2、#3 | @bob |"), encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 0)
        self.assertIn("| 2025-02-01 | 決済とセッション | [#2](https://github.com/o/r/pull/2)、[#3](https://github.com/o/r/pull/3) | —、@alice |",
                      self.page("2025-02.md"))
        # PR のないコミットは、ハッシュかそのリンクで書ける。リンク先の URL の中は数えない
        sha = self.git("log", "-1", "--format=%H", "--grep", "Initial import").strip()
        self.fill("2025-01", f"### other\n\n| | 始めた | [{sha[:7]}](https://github.com/o/r/commit/{sha}) | |")
        self.assertEqual(self.run_script().returncode, 1)  # 2025-01 の要約がまだ
        self.assertIn(f"| 2025-01-10 | 始めた | [{sha[:7]}](https://github.com/o/r/commit/{sha}) | — |", self.page("2025-01.md"))
        self.commit("src/auth/session.py", "TTL = 48", "Longer session (#4)", "2025-02-10T00:00:00Z")
        self.assertEqual(self.run_script("--check").returncode, 1)

    def test_mailmap_maps_work_emails_to_accounts(self):
        # noreply でないメールも、.mailmap で noreply に対応させればアカウント名になる
        self.write(".mailmap", "<9+main-user@users.noreply.github.com> <m@example.com>")
        self.assertIn("Extend session（[#2](https://github.com/o/r/pull/2)、src/auth/、@main-user）", self.listing("2025-02"))

    def test_old_list_lines_become_rows(self):
        # 前の形（「- 概要（#3）」と「## 一覧」）は、作り直すと表になり、一覧は消える
        self.run_script()
        path = self.repo / "docs/change-history/2025-02.md"
        path.write_text("# 2025-02\n\nマージされた変更 2 件。\n\n## 主な変更\n\n### reliability\n\n- 決済の再試行を a|b に（[#3](x)）\n"
                        "\n### security\n\n- セッションを延ばした（#2）\n\n## 一覧\n\n- 2025-02-01 Extend session\n", encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 1)  # 要約がまだ
        feb = self.page("2025-02.md")
        self.assertNotIn("一覧", feb)
        self.assertNotIn("マージされた変更", feb)
        self.assertIn("| 2025-02-04 | 決済の再試行を a\\|b に | [#3](https://github.com/o/r/pull/3) | @alice |", feb)
        self.assertIn("認証・権限・セキュリティ：認証方式", feb)
        self.assertIn("| [2025-02](2025-02.md) | 2 | まだ |", self.page("README.md"))

    def test_year_summaries_use_three_kinds(self):
        # 年表の要点は 機能改善・運用改善・バグ対応 で分け、見出しの直下に説明が入る。月の 11 種は使えない
        self.run_script()
        path = self.repo / "docs/change-history/README.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("（まだ書いていない）", "### バグ対応\n\n- 決済の再試行を直した（2025-02）\n\n### 機能改善\n\n- セッションを延ばした（2025-02）"), encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 0)
        self.assertIn("## 2025\n\n### バグ対応\n\n不具合の修正と、その再発を防ぐ変更\n\n- 決済の再試行を直した（2025-02）\n\n"
                      "### 機能改善\n\n使う人に見える機能の追加と変更\n\n- セッションを延ばした（2025-02）\n\n| 月 |", self.page("README.md"))
        self.assertEqual(self.run_script("--check").returncode, 0)
        path.write_text(text.replace("（まだ書いていない）", "### reliability\n\n- 決済の再試行を見直した（2025-02）"), encoding="utf-8")
        result = self.run_script("--check")
        self.assertIn("分類 reliability は 機能改善・運用改善・バグ対応 のどれでもない", result.stdout)

    def test_broken_summaries_are_reported(self):
        self.run_script()
        folder = self.repo / "docs/change-history"
        self.fill("2025-02", "\n".join([
            "認証を変えた", "### セキュリティ", "| | x | #2 | |", "### security", "| | 5 月に延ばした | #2 | |",
            "| | ない PR | #99 | |", "| | PR がない | なし | |", "| | 列が 3 つ | #2 |", "### security", "| | もう 1 つ | #2 | |",
            "### reliability", "* 記号が違う", "### release"]))
        path = folder / "README.md"
        path.write_text(path.read_text(encoding="utf-8").replace("（まだ書いていない）", "### 機能改善\n\n- 期間がない\n- 3 月に始めた（2025-03）"), encoding="utf-8")
        result = self.run_script("--check")
        self.assertEqual(result.returncode, 1)
        for want in ["2025-02.md の「## 主な変更」1 行目：### <分類> と表の行だけを書く",
                     "行目：分類 セキュリティ は architecture・",
                     "行目：日付は YYYY-MM-DD、月は YYYY-MM で書く",
                     "行目：PR の列の参照が、この月の変更にない",
                     "行目：PR の列に PR かコミット",
                     "行目：表の行は | 日付 | 概要 | PR | Author | の 4 列で書く",
                     "行目：分類 security が 2 度ある",
                     "行目：### <分類> と表の行だけを書く",
                     "行目：### release の下に行がない",
                     "README.md の「## 2025」5 行目：行の末尾に（YYYY-MM）か（YYYY-MM〜YYYY-MM）がない",
                     "README.md の「## 2025」6 行目：日付は YYYY-MM-DD"]:
            self.assertIn(want, result.stdout)
        # 作り直しても書き出しはするが、崩れが残れば終了コード 1
        self.assertEqual(self.run_script().returncode, 1)
        # まだ書いていない・目立った変更なしは通す
        path = folder / "2025-02.md"
        path.write_text("# 2025-02\n\n## 主な変更\n\n- 目立った変更なし（リリースのみ）\n", encoding="utf-8")
        path = folder / "README.md"
        path.write_text(path.read_text(encoding="utf-8").replace("- 期間がない\n- 3 月に始めた（2025-03）", "- 始めた（2025-01〜2025-02）"), encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 0)
        self.assertIn("| [2025-02](2025-02.md) | 2 | 目立った変更なし（リリースのみ） |", self.page("README.md"))
        self.assertEqual(self.run_script("--check").returncode, 0)

    def test_old_timeline_moves_into_readme(self):
        self.run_script()
        folder = self.repo / "docs/change-history"
        (folder / "README.md").write_text("# 変更の履歴\n\n| 月 | 件数 | 主な変更を書いたか |\n", encoding="utf-8")
        (folder / "timeline.md").write_text("# 年表\n\n## 2025\n\n- 前に書いた要点（2025-02）\n\n| 月 | 件数 | 主な変更 |\n", encoding="utf-8")
        self.assertEqual(self.run_script("--check").returncode, 1)
        # 以前の要点は分類の見出しがないので、移したうえで形の崩れとして知らせる
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("README.md の「## 2025」1 行目：行の前に ### <分類> がない", result.stdout)
        self.assertIn("## 2025\n\n- 前に書いた要点（2025-02）\n\n| 月 |", self.page("README.md"))
        self.assertFalse((folder / "timeline.md").exists())
        path = folder / "README.md"
        path.write_text(path.read_text(encoding="utf-8").replace("- 前に書いた要点", "### 運用改善\n\n- 前に書いた要点"), encoding="utf-8")
        self.assertEqual(self.run_script("--check").returncode, 1)  # 分類の説明がまだない
        self.assertEqual(self.run_script().returncode, 0)
        self.assertEqual(self.run_script("--check").returncode, 0)

    def test_branch_syncs_are_marked(self):
        self.git("switch", "-q", "-c", "stable")
        self.commit("src/auth/session.py", "TTL = 36", "Fix on stable", "2025-03-01T00:00:00Z")
        self.git("switch", "-q", "main")
        self.git("merge", "-q", "--no-ff", "stable", "-m", "Merge branch 'stable'",
                 env={"GIT_AUTHOR_DATE": "2025-03-02T00:00:00Z", "GIT_COMMITTER_DATE": "2025-03-02T00:00:00Z"})
        self.run_script()
        self.assertIn("- 2025-03-02 （ブランチの取り込み）Merge branch 'stable'（[", self.listing("2025-03"))

    def test_releases_are_marked(self):
        for i, subject in enumerate(["Release v0.8.0 (#90)", "Bump version to 1.2.0", "chore(release): 1.3.0", "v1.4.0",
                                     "Release automation for the docs site (#91)", "Bump requests from 2.31 to 2.32"]):
            self.commit("CHANGELOG.md", str(i), subject, f"2025-04-0{i + 1}T00:00:00Z")
        self.run_script()
        april = self.listing("2025-04")
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
        may = self.listing("2025-05")
        for line in ["- 2025-05-02 Raise search limit（[#10](https://github.com/o/r/pull/10)、src/search/、@alice、develop へ）",
                     "- 2025-05-03 （develop から取り込み）Release 2025-05（[#11](https://github.com/o/r/pull/11)、",
                     "- 2025-05-04 Shorten session（[#12](https://github.com/o/r/pull/12)、src/auth/、@alice、main へ）",
                     "- 2025-05-05 （main から取り込み）Merge branch 'main' into develop（["]:
            self.assertIn(line, may)
        # どちらにも入ったコミットは 1 件
        feb = self.listing("2025-02")
        self.assertEqual(feb.count("Extend session"), 1)
        self.assertIn("Extend session（[#2](https://github.com/o/r/pull/2)、src/auth/、—、main・develop へ）", feb)
        self.assertIn("読んだブランチ：main（origin/main）、develop（origin/develop）", feb)
        # 1 つに絞れば、ブランチは書かない
        # 読んだブランチどうしのマージの下には、中身を並べない（元のブランチの行に出ている）
        self.assertRegex(self.listing("2025-05"), r"Release 2025-05（[^\n]*main へ）\n- 2025-05-04 ")
        # develop を読まなければ、main に入ったマージの下に、develop で入った PR が見える
        may = self.listing("2025-05", "--branch", "main")
        self.assertIn("- 2025-05-03 Release 2025-05（[#11](https://github.com/o/r/pull/11)、src/search/、@alice）\n"
                      "  - Raise search limit（[#10](https://github.com/o/r/pull/10)、@alice）", may)
        self.assertNotIn(" へ）", may)
        # 表は、マージの中の PR を指してよい。日付は main に入った日
        self.assertEqual(self.run_script("--branch", "main").returncode, 0)
        self.fill("2025-05", "### product\n\n| | 検索の上限を上げた | #10 | |")
        self.run_script("--branch", "main")
        self.assertIn("| 2025-05-03 | 検索の上限を上げた | [#10](https://github.com/o/r/pull/10) | @alice |", self.page("2025-05.md"))
        self.assertEqual(self.run_script("--branch", "nope").returncode, 2)

    def test_since_and_depth(self):
        self.run_script("--since", "2025-02", "--depth", "1")
        self.assertFalse((self.repo / "docs/change-history/2025-01.md").exists())
        self.assertIn("pull/2)、src/、—）", self.listing("2025-02", "--since", "2025-02", "--depth", "1"))
        self.assertEqual(self.run_script("--since", "2025-2").returncode, 2)


if __name__ == "__main__":
    unittest.main()
