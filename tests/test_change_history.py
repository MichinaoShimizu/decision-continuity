"""change-history の build_history.py を、合成のリポジトリで回す。"""
import datetime
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import zoneinfo

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
        # clone したときに git が覚える origin のデフォルトブランチ（ここでは手元の main を指す）
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/heads/main")
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

    def run_script(self, *args, env=None):
        # 既定では本物の gh に問い合わせないよう --no-github を付ける。偽の gh を置いたときだけ外す
        extra = () if env else ("--no-github",)
        return subprocess.run([sys.executable, str(SCRIPT), "docs/change-history", *args, *extra], cwd=self.repo,
                              capture_output=True, text=True, check=False, env=env)

    def fake_gh(self, script):
        """PATH の先頭に偽の gh を置いた環境を返す。"""
        bin_dir = self.repo / ".bin"
        bin_dir.mkdir(exist_ok=True)
        gh = bin_dir / "gh"
        gh.write_text("#!/bin/sh\n" + script + "\n", encoding="utf-8")
        gh.chmod(0o755)
        return dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}")

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
        # 概要と PR だけ書けば、日付・Author・PR のリンクはスクリプトが入れる
        self.run_script()
        self.fill("2025-02", "| 日付 | 概要 | PR | Author |\n|---|---|---|---|\n|  | 決済の再試行を増やした | #3 |  |")
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
            "# 2025-02", "", "## 主な変更", "",
            "| 日付 | 概要 | PR | Author |", "|---|---|---|---|",
            "| 2025-02-04 | 決済の再試行を増やした | [#3](https://github.com/o/r/pull/3) | @alice |"]) + "\n")
        # 要約は作り直しても残る
        self.assertIn("| [2025-02](2025-02.md) | 2 | 決済の再試行とセッションを見直した |", self.page("README.md"))
        self.assertEqual(self.run_script("--check").returncode, 0)
        # 間違えた日付は直す。Author は GitHub から取れたときだけ直し、取れなければ書いてあるものを残す
        # （gh が使えるかどうかで --check の結果が変わらないように）。いくつかの PR をまとめた行の日付は最初の PR の日
        path = self.repo / "docs/change-history/2025-02.md"
        path.write_text(path.read_text(encoding="utf-8").replace("| 2025-02-04 | 決済の再試行を増やした | [#3](https://github.com/o/r/pull/3) | @alice |",
                                                                 "| 2025-02-09 | 決済とセッション | #2、#3 | @bob |"), encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 0)
        self.assertIn("| 2025-02-01 | 決済とセッション | [#2](https://github.com/o/r/pull/2)、[#3](https://github.com/o/r/pull/3) | @bob |",
                      self.page("2025-02.md"))
        path.write_text(path.read_text(encoding="utf-8").replace(" @bob |", "  |"), encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 0)
        self.assertIn("| [#2](https://github.com/o/r/pull/2)、[#3](https://github.com/o/r/pull/3) | —、@alice |", self.page("2025-02.md"))
        # PR のないコミットは、ハッシュかそのリンクで書ける。リンク先の URL の中は数えない
        sha = self.git("log", "-1", "--format=%H", "--grep", "Initial import").strip()
        self.fill("2025-01", f"| | 始めた | [{sha[:7]}](https://github.com/o/r/commit/{sha}) | |")
        self.assertEqual(self.run_script().returncode, 1)  # 2025-01 の要約がまだ
        self.assertIn(f"| 2025-01-10 | 始めた | [{sha[:7]}](https://github.com/o/r/commit/{sha}) | — |", self.page("2025-01.md"))
        self.commit("src/auth/session.py", "TTL = 48", "Longer session (#4)", "2025-02-10T00:00:00Z")
        self.assertEqual(self.run_script("--check").returncode, 1)

    def test_decision_logs_that_cite_a_pr_are_linked_after_it(self):
        # PR を挙げた Decision log へのリンクを、PR の後ろに番号の順に添える。書き手が書かなくても、作り直すたびに入れ直す
        self.write("docs/decision-logs/0007-retry.md", "# 再試行\n\n- 2025-02-04 上限を 5 に（[PR #3][pr3]）\n\n"
                                                      "[pr3]: https://github.com/o/r/pull/3")
        self.write("docs/decision-logs/0002-retry-again.md", "# 再試行の続き\n\n- [リンクだけ](https://github.com/o/r/pull/3)")
        # 索引、ほかのリポジトリの PR、#3 の文だけのものは当たらない
        self.write("docs/decision-logs/README.md", "- [PR #3](https://github.com/o/r/pull/3)")
        self.write("docs/decision-logs/0003-other.md", "# ほか\n\n- https://github.com/x/y/pull/3 と #3")
        self.run_script()
        self.fill("2025-02", "|  | 決済の再試行を増やした | #3 |  |\n|  | セッションを延ばした | #2 |  |")
        self.run_script()
        rows = self.page("2025-02.md")
        self.assertIn("| [#3](https://github.com/o/r/pull/3)、[DL-2](../decision-logs/0002-retry-again.md)、"
                      "[DL-7](../decision-logs/0007-retry.md) | @alice |", rows)
        self.assertIn("| [#2](https://github.com/o/r/pull/2) | — |", rows)
        # リンクは PR の列の参照に数えない。作り直しても変わらず、Decision log が消えればリンクも消える
        path = self.repo / "docs/change-history/README.md"
        path.write_text(path.read_text(encoding="utf-8").replace("| 2 | まだ |", "| 2 | 再試行を増やした |"), encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 0)
        self.assertEqual(self.page("2025-02.md"), rows)
        self.assertEqual(self.run_script("--check").returncode, 0)
        (self.repo / "docs/decision-logs/0002-retry-again.md").unlink()
        self.assertEqual(self.run_script("--check").returncode, 1)
        self.run_script()
        self.assertIn("| [#3](https://github.com/o/r/pull/3)、[DL-7](../decision-logs/0007-retry.md) |", self.page("2025-02.md"))
        # 置き場所は --decision-logs で変えられる
        shutil.move(self.repo / "docs/decision-logs", self.repo / "decisions")
        self.run_script("--decision-logs", "decisions")
        self.assertIn("、[DL-7](../../decisions/0007-retry.md) |", self.page("2025-02.md"))
        # --repo のとき（中央にまとめる）は、言われなければリンクしない
        self.write("docs/decision-logs/0007-retry.md", "- [PR #3][pr3]")
        self.run_script("--repo", ".")
        self.assertIn("| [#3](https://github.com/o/r/pull/3) | @alice |", self.page("2025-02.md"))

    def test_pr_column_variants_are_read(self):
        # 全角の ＃、PR の URL、数字だけの列、PR から入ったコミットのハッシュも、日付・リンク・Author を埋める
        self.run_script()
        squash = self.git("log", "-1", "--format=%h", "--grep", "Extend session").strip()
        self.fill("2025-02", "\n".join([
            "|  | 全角 | ＃３ |  |",
            "|  | URL | https://github.com/o/r/pull/3 |  |",
            "|  | 数字だけ | 2、3 |  |",
            f"|  | PR のコミットのハッシュ | {squash} |  |",
            "|  | 概要の数字は PR にしない | #3 ほか 2 件 |  |"]))
        result = self.run_script()
        self.assertNotIn("参照", result.stdout)
        feb = self.page("2025-02.md")
        for summary in ("全角", "URL", "概要の数字は PR にしない"):
            self.assertIn(f"| 2025-02-04 | {summary} | [#3](https://github.com/o/r/pull/3) | @alice |", feb)
        self.assertIn("| 2025-02-01 | 数字だけ | [#2](https://github.com/o/r/pull/2)、[#3](https://github.com/o/r/pull/3) | —、@alice |", feb)
        self.assertIn("| 2025-02-01 | PR のコミットのハッシュ | [#2](https://github.com/o/r/pull/2) | — |", feb)

    def test_github_gives_pr_authors(self):
        # gh があれば、言われなくても PR の作成者を GitHub から取り、.git の中に覚えておく。PR のないコミットはメールから取る
        env = self.fake_gh('echo "$@" >> gh-args.txt; printf "2\\tbob\\t\\tExtend\\n3\\tcarol\\t\\tRetries\\n"')
        self.assertEqual(self.run_script(env=env).returncode, 0)
        self.assertIn("api repos/o/r/pulls?state=closed&sort=updated&direction=desc&per_page=100&page=1 --jq",
                      (self.repo / "gh-args.txt").read_text())
        self.assertTrue((self.repo / ".git/decision-continuity-prs.json").exists())
        # --list（書き手が月ごとに呼ぶ）は問い合わせず、覚えておいた分を使う
        (self.repo / "gh-args.txt").unlink()
        result = self.run_script("--list", "2025-02", env=env)
        self.assertIn("Extend session（[#2](https://github.com/o/r/pull/2)、src/auth/、@bob）", result.stdout)
        self.assertIn("Raise payment retries（[#3](https://github.com/o/r/pull/3)、docs/ ほか 1、@carol）", result.stdout)
        self.assertRegex(result.stdout, r"  - Raise retries（\[[0-9a-f]{7}\]\([^)]*\)、@alice）")
        self.assertFalse((self.repo / "gh-args.txt").exists())
        # 表の Author にも入る
        self.fill("2025-02", "| | セッションを延ばした | #2 | |")
        self.run_script(env=env)
        self.assertIn("| 2025-02-01 | セッションを延ばした | [#2](https://github.com/o/r/pull/2) | @bob |", self.page("2025-02.md"))
        # gh が失敗しても、覚えておいた分を使う
        failing = self.fake_gh("echo 'HTTP 401' >&2; exit 1")
        self.assertIn("src/auth/、@bob）", self.run_script("--list", "2025-02", "--github", env=failing).stdout)
        result = self.run_script(env=failing)
        self.assertIn("gh api が失敗したので、PR の作成者は覚えておいた分とメールから取る（HTTP 401。止めるなら --no-github）", result.stderr)
        # --no-github なら問い合わせず、覚えておいた分も使わない
        self.assertIn("src/auth/、—）", self.run_script("--list", "2025-02", "--no-github", env=env).stdout)
        # gh がなければ黙って取らない。--github と言われたときだけ理由を出す
        only_git = self.repo / ".only-git"
        only_git.mkdir()
        (only_git / "git").symlink_to(shutil.which("git"))
        self.assertEqual(self.run_script(env=dict(os.environ, PATH=str(only_git))).stderr, "")
        result = self.run_script("--github", env=dict(os.environ, PATH=str(only_git)))
        self.assertIn("--github：gh がないので、PR の作成者は取らない", result.stderr)

    def test_github_pages_only_until_known_and_keeps_partial_results(self):
        # 100 件ちょうどなら次のページを取る。2 ページ目で失敗しても、1 ページ目の分は使う
        page1 = 'i=1; while [ $i -le 100 ]; do printf "%s\\tuser%s\\t\\tT\\n" $i $i; i=$((i+1)); done'
        env = self.fake_gh('echo "$@" >> gh-args.txt; case "$2" in *page=1) ' + page1 + ';; *) echo "HTTP 403" >&2; exit 1;; esac')
        result = self.run_script(env=env)
        self.assertIn("gh api が失敗したので、以降の PR の作成者は覚えておいた分とメールから取る（HTTP 403", result.stderr)
        self.assertIn("src/auth/、@user2）", self.run_script("--list", "2025-02", env=env).stdout)
        # 2 回目は、1 ページ目が全部覚えている PR なので、そこで止める
        (self.repo / "gh-args.txt").unlink()
        self.assertEqual(self.run_script(env=env).stderr, "")
        self.assertEqual(len((self.repo / "gh-args.txt").read_text().splitlines()), 1)

    def test_github_links_commits_without_numbers_to_their_pr(self):
        # Rebase and merge などで件名に番号がないコミットも、PR を入れたコミット（merge_commit_sha）から PR に結びつける
        self.commit("src/search.py", "x", "Add search", "2025-02-20T00:00:00Z")
        sha = self.git("rev-parse", "HEAD").strip()
        env = self.fake_gh(f'printf "9\\tdave\\t{sha}\\tAdd full-text search\\n"')
        self.run_script(env=env)
        self.assertIn("- 2025-02-20 Add full-text search（[#9](https://github.com/o/r/pull/9)、src/、@dave）",
                      self.run_script("--list", "2025-02", env=env).stdout)

    def test_until_limits_the_months(self):
        self.commit("src/late.py", "x", "Later (#7)", "2025-04-02T00:00:00Z")
        self.run_script("--since", "2025-02", "--until", "2025-02")
        folder = self.repo / "docs/change-history"
        self.assertEqual(sorted(p.name for p in folder.glob("*.md")), ["2025-02.md", "README.md"])
        self.assertNotIn("2025-04", self.page("README.md"))
        self.assertNotIn("2025-01", self.page("README.md"))
        self.assertEqual(self.run_script("--until", "2025-4").returncode, 2)

    def test_check_does_not_depend_on_gh(self):
        # gh で作った表は、gh のない環境（CI など）の --check でも最新のまま
        env = self.fake_gh('printf "2\\tbob\\t\\tExtend\\n"')
        self.run_script(env=env)
        self.fill("2025-02", "| | セッションを延ばした | #2 | |")
        self.run_script(env=env)
        self.fill("2025-01", "- 目立った変更なし（リリースのみ）")
        path = self.repo / "docs/change-history/README.md"
        path.write_text(path.read_text(encoding="utf-8").replace("| 2 | まだ |", "| 2 | セッションを延ばした |"), encoding="utf-8")
        self.assertEqual(self.run_script(env=env).returncode, 0)
        self.assertIn("| @bob |", self.page("2025-02.md"))
        self.assertEqual(self.run_script("--check").returncode, 0)

    def test_since_keeps_earlier_months_in_the_readme(self):
        self.run_script()
        path = self.repo / "docs/change-history/README.md"
        path.write_text(path.read_text(encoding="utf-8").replace("| [2025-01](2025-01.md) | 1 | まだ |", "| [2025-01](2025-01.md) | 1 | 始めた |"), encoding="utf-8")
        self.fill("2025-01", "| | 始めた | " + self.git("log", "-1", "--format=%h", "--grep", "Initial").strip() + " | |")
        self.run_script("--since", "2025-02")
        self.assertIn("| [2025-01](2025-01.md) | 1 | 始めた |", self.page("README.md"))
        # --list は --since に関わらず、その月を出す
        self.assertIn("Initial import", self.listing("2025-01", "--since", "2025-02"))

    def test_date_is_when_it_reached_the_branch(self):
        # rebase や cherry-pick で入ったコミットは、書いた日ではなく入った日の月に出る
        self.write("src/late.py", "x")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "Late (#9)", env={"GIT_AUTHOR_DATE": "2025-02-20T00:00:00Z", "GIT_COMMITTER_DATE": "2025-03-05T00:00:00Z"})
        self.assertIn("- 2025-03-05 Late（[#9]", self.listing("2025-03"))

    def test_unresolved_old_lines_are_reported_as_rows(self):
        self.run_script()
        self.fill("2025-02", "- 旧（#99）")
        result = self.run_script()
        self.assertIn("|  | 旧 | [#99](https://github.com/o/r/pull/99) | — |", self.page("2025-02.md"))
        self.assertIn("PR の列の参照が、この月の変更にない", result.stdout)
        self.assertNotIn("下に行がない", result.stdout)

    def test_rows_are_filled_even_when_they_break_the_rules(self):
        # 別の月の PR を書いても、リンク・日付・Author は入れ、崩れとして知らせる
        self.run_script()
        self.fill("2025-01", "| | セッションを延ばした | #2 | |")
        result = self.run_script()
        self.assertIn("| 2025-02-01 | セッションを延ばした | [#2](https://github.com/o/r/pull/2) | — |", self.page("2025-01.md"))
        self.assertIn("PR の列の参照が、この月の変更にない", result.stdout)

    def test_duplicate_and_unknown_references_are_kept(self):
        # 同じ PR を 2 度書いても、後ろの読めない参照を落とさない。どこにもないハッシュは書かれたまま
        self.run_script()
        self.fill("2025-02", "| | 重なり | #2、#2、#99 | |\n| | ハッシュ | deadbeef1 | |")
        self.run_script()
        feb = self.page("2025-02.md")
        self.assertIn("| 2025-02-01 | 重なり | [#2](https://github.com/o/r/pull/2)、[#99](https://github.com/o/r/pull/99) | — |", feb)
        self.assertIn("|  | ハッシュ | [deadbeef1](https://github.com/o/r/commit/deadbeef1) | — |", feb)

    def test_rebuilding_twice_changes_nothing(self):
        # 決まりから外れた行（別の月の PR、決まりにない見出し、前の形、読めない参照）が混じっても、2 回目は何も変えない
        self.run_script()
        sha = self.git("log", "-1", "--format=%H", "--grep", "Initial").strip()
        self.fill("2025-02", "\n".join(["### security", "| | 別の月のコミット | " + sha[:9] + " | |", "### バグ対応",
                                         "- 前の形（#3）", "- 読めない（#99）", "| | まとめ | [#2](x)、#3 | @someone |"]))
        self.run_script()
        first = {p.name: p.read_text(encoding="utf-8") for p in (self.repo / "docs/change-history").glob("*.md")}
        self.run_script()
        second = {p.name: p.read_text(encoding="utf-8") for p in (self.repo / "docs/change-history").glob("*.md")}
        self.assertEqual(first, second)
        self.assertIn(f"| 2025-01-10 | 別の月のコミット | [{sha[:7]}](https://github.com/o/r/commit/{sha}) | — |", second["2025-02.md"])
        self.assertNotIn("が古い", self.run_script("--check").stdout)

    def test_rows_are_sorted_by_date_and_any_quiet_month_is_allowed(self):
        self.run_script()
        self.fill("2025-02", "| | 後 | #3 | |\n| | 読めない | #99 | |\n| | 先 | #2 | |")
        self.fill("2025-01", "- 目立った変更なし（依存の更新のみ）")
        self.run_script()
        feb = self.page("2025-02.md")
        self.assertLess(feb.index("| 先 |"), feb.index("| 後 |"))
        self.assertLess(feb.index("| 後 |"), feb.index("| 読めない |"))
        self.assertIn("| [2025-01](2025-01.md) | 1 | 目立った変更なし（依存の更新のみ） |", self.page("README.md"))

    def test_too_many_references_in_a_row_are_reported(self):
        self.run_script()
        self.fill("2025-02", "| | 翻訳 | #2、#3、#91、#92、#93、#94 | |")
        self.assertIn("PR は 1 行に 5 件まで", self.run_script().stdout)

    def test_unwritten_months_are_listed(self):
        # 書き手が書けなかった月に気づけるよう、まだの月を出す
        self.assertIn("主な変更をまだ書いていない月（2）：2025-01、2025-02", self.run_script().stdout)
        self.fill("2025-01", "- 目立った変更なし（リリースのみ）")
        self.assertIn("主な変更をまだ書いていない月（1）：2025-02", self.run_script().stdout)

    def test_empty_repository(self):
        with tempfile.TemporaryDirectory() as empty:
            subprocess.run(["git", "init", "-q", empty], check=True)
            result = subprocess.run([sys.executable, str(SCRIPT), "docs/change-history", "--no-github"], cwd=empty,
                                    capture_output=True, text=True)
            self.assertEqual((result.returncode, result.stdout.strip()), (0, "コミットがまだないので、書くものはない"))

    def test_mailmap_maps_work_emails_to_accounts(self):
        # noreply でないメールも、.mailmap で noreply に対応させればアカウント名になる
        self.write(".mailmap", "<9+main-user@users.noreply.github.com> <m@example.com>")
        self.assertIn("Extend session（[#2](https://github.com/o/r/pull/2)、src/auth/、@main-user）", self.listing("2025-02"))

    def test_old_list_lines_become_rows(self):
        # 前の形（分類の見出しと説明、「- 概要（#3）」、「## 一覧」）は、作り直すと日付の順の 1 つの表になり、見出しと一覧は消える
        self.run_script()
        path = self.repo / "docs/change-history/2025-02.md"
        path.write_text("# 2025-02\n\nマージされた変更 2 件。\n\n## 主な変更\n\n### 運用改善\n\n- 決済の再試行を a|b に（[#3](x)）\n"
                        "\n### 機能改善\n\n使う人に見える機能の追加と変更\n\n- セッションを延ばした（#2）\n\n## 一覧\n\n- 2025-02-01 Extend session\n", encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 1)  # 要約がまだ
        feb = self.page("2025-02.md")
        self.assertNotIn("一覧", feb)
        self.assertNotIn("マージされた変更", feb)
        self.assertEqual(feb, "\n".join([
            "# 2025-02", "", "## 主な変更", "", "| 日付 | 概要 | PR | Author |", "|---|---|---|---|",
            "| 2025-02-01 | セッションを延ばした | [#2](https://github.com/o/r/pull/2) | — |",
            "| 2025-02-04 | 決済の再試行を a\\|b に | [#3](https://github.com/o/r/pull/3) | @alice |"]) + "\n")
        self.assertIn("| [2025-02](2025-02.md) | 2 | まだ |", self.page("README.md"))

    def test_year_summaries_are_plain_lines(self):
        # 年表の要点は分類に分けず、「- 」の行を並べる。前の形の分類の見出しと説明は、作り直すと外れる
        self.run_script()
        path = self.repo / "docs/change-history/README.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("（まだ書いていない）", "- セッションを延ばした（2025-02）\n- 決済の再試行を直した（2025-02）"), encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 0)
        self.assertIn("## 2025\n\n- セッションを延ばした（2025-02）\n- 決済の再試行を直した（2025-02）\n\n| 月 |", self.page("README.md"))
        self.assertEqual(self.run_script("--check").returncode, 0)
        path.write_text(text.replace("（まだ書いていない）", "不具合の修正と、その再発を防ぐ変更\n\n- 決済の再試行を直した（2025-02）"
                                     "\n\n### reliability\n\n- セッションを延ばした（2025-02）"), encoding="utf-8")
        self.assertEqual(self.run_script("--check").returncode, 1)
        self.assertEqual(self.run_script().returncode, 0)
        self.assertIn("## 2025\n\n- 決済の再試行を直した（2025-02）\n- セッションを延ばした（2025-02）\n\n| 月 |", self.page("README.md"))

    def test_broken_summaries_are_reported(self):
        self.run_script()
        folder = self.repo / "docs/change-history"
        self.fill("2025-02", "\n".join([
            "認証を変えた", "| | x | #2 | |", "| | 5 月に延ばした | #2 | |",
            "| | ない PR | #99 | |", "| | PR がない | なし | |", "| | 列が 3 つ | #2 |", "* 記号が違う"]))
        path = folder / "README.md"
        path.write_text(path.read_text(encoding="utf-8").replace("（まだ書いていない）", "- 期間がない\n- 3 月に始めた（2025-03）"), encoding="utf-8")
        result = self.run_script("--check")
        self.assertEqual(result.returncode, 1)
        for want in ["2025-02.md の「## 主な変更」1 行目：表の行だけを書く",
                     "2025-02.md の「## 主な変更」2 行目：表の行だけを書く",
                     "行目：日付は YYYY-MM-DD、月は YYYY-MM で書く",
                     "行目：PR の列の参照が、この月の変更にない",
                     "行目：PR の列に PR かコミット",
                     "行目：表の行は | 日付 | 概要 | PR | Author | の 4 列で書く",
                     "README.md の「## 2025」1 行目：行の末尾に（YYYY-MM）か（YYYY-MM〜YYYY-MM）がない",
                     "README.md の「## 2025」2 行目：日付は YYYY-MM-DD"]:
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
        self.assertIn("- 2025-03-02 （ブランチの取り込み）Merge branch 'stable'（[", self.listing("2025-03"))

    def test_releases_are_marked(self):
        for i, subject in enumerate(["Release v0.8.0 (#90)", "Bump version to 1.2.0", "chore(release): 1.3.0", "v1.4.0",
                                     "Release automation for the docs site (#91)", "Bump requests from 2.31 to 2.32"]):
            self.commit("CHANGELOG.md", str(i), subject, f"2025-04-0{i + 1}T00:00:00Z")
        self.run_script()
        april = self.listing("2025-04")
        for line in ["- 2025-04-01 （リリース）Release v0.8.0（[#90]", "- 2025-04-02 （リリース）Bump version to 1.2.0（",
                     "- 2025-04-03 （リリース）chore(release): 1.3.0（", "- 2025-04-04 （リリース）v1.4.0（",
                     "- 2025-04-05 Release automation for the docs site（[#91]", "- 2025-04-06 （依存の更新）Bump requests from 2.31 to 2.32（"]:
            self.assertIn(line, april)

    def test_dependency_updates_are_marked_and_quiet_months_are_written(self):
        subjects = ["Bump requests from 2.31 to 2.32", "build(deps): bump the pip group with 3 updates",
                    "chore(deps): update dependency ruff to v0.5", "Update dependency eslint to v9",
                    "[pre-commit.ci] pre-commit autoupdate", "Release v0.9.0"]
        for i, subject in enumerate(subjects):
            self.commit("requirements.txt", str(i), subject, f"2025-05-0{i + 1}T00:00:00Z")
        self.commit("requirements.txt", "x", "Bump requests from 2.32 to 2.33", "2025-06-01T00:00:00Z")
        self.run_script()
        may = self.listing("2025-05")
        for subject in subjects[:-1]:
            self.assertIn(f"（依存の更新）{subject}（", may)
        # 依存の更新とリリースだけの月は、書き手を呼ばずにスクリプトが書く
        self.assertIn("- 目立った変更なし（依存の更新・リリースのみ）", self.page("2025-05.md"))
        self.assertIn("- 目立った変更なし（依存の更新のみ）", self.page("2025-06.md"))
        self.assertIn("| [2025-06](2025-06.md) | 1 | 目立った変更なし（依存の更新のみ） |", self.page("README.md"))
        self.assertIn("主な変更をまだ書いていない月（2）：2025-01、2025-02", self.run_script().stdout)
        # 書いたものは上書きしない
        self.fill_over("2025-06", "- 目立った変更なし（依存の更新のみ）", "| | requests を上げた | " +
                       self.git("log", "-1", "--format=%h").strip() + " | |")
        self.run_script()
        self.assertIn("requests を上げた", self.page("2025-06.md"))
        # 終わっていない月は、あとから変更が増えるので書かない
        now = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Tokyo"))
        self.commit("requirements.txt", "y", "Bump requests from 2.33 to 2.34", now.astimezone(datetime.timezone.utc).isoformat())
        self.run_script()
        self.assertIn("（まだ書いていない）", self.page(f"{now:%Y-%m}.md"))

    def fill_over(self, month, old, new):
        path = self.repo / "docs/change-history" / f"{month}.md"
        path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")

    def test_quiet_months_and_years_stay_in_the_timeline(self):
        self.commit("src/a.py", "1", "Pick it up again (#7)", "2027-03-01T00:00:00Z")
        self.assertEqual(self.run_script().returncode, 0)
        index = self.page("README.md")
        # 変更のなかった月も 0 件の行で載せ（月のファイルは作らない）、年ごと変更のない年は要点を「変更なし」にする
        # 続いた月は 1 行にまとめ、年はまたがない
        self.assertIn("| [2027-03](2027-03.md) | 1 | まだ |\n| 2027-01〜2027-02 | 0 | 変更なし |\n", index)
        self.assertIn("## 2026\n\n変更なし\n\n| 月 | 件数 | 主な変更 |\n|---|---|---|\n| 2026-01〜2026-12 | 0 | 変更なし |\n", index)
        self.assertIn("| 2025-03〜2025-12 | 0 | 変更なし |\n| [2025-02](2025-02.md) | 2 | まだ |\n| [2025-01](2025-01.md) | 1 | まだ |", index)
        self.assertNotIn("| 2027-04", index)
        self.commit("src/a.py", "2", "One more (#13)", "2026-06-01T00:00:00Z")
        self.run_script()
        self.assertIn("| 2026-07〜2026-12 | 0 | 変更なし |\n| [2026-06](2026-06.md) | 1 | まだ |\n| 2026-01〜2026-05 | 0 | 変更なし |",
                      self.page("README.md"))
        self.assertIn("## 2026\n\n（まだ書いていない）", self.page("README.md"))
        self.assertTrue((self.repo / "docs/change-history/2025-02.md").exists())
        self.assertFalse((self.repo / "docs/change-history/2025-03.md").exists())
        self.assertEqual(self.run_script("--check").returncode, 0)

    def test_counts_include_changes_merged_on_other_branches(self):
        # 保守ブランチでマージした PR と直接のコミットは、取り込んだ月の件数に入る。PR の中のコミットは数えない
        self.git("switch", "-q", "-c", "1.x")
        self.git("switch", "-q", "-c", "fix")
        self.commit("src/a.py", "1", "Fix a", "2025-03-01T00:00:00Z")
        self.commit("src/a.py", "2", "Fix a again", "2025-03-01T00:00:00Z")
        self.git("switch", "-q", "1.x")
        self.merge("fix", "Merge pull request #8 from alice/fix\n\nFix a", "2025-03-02T00:00:00Z")
        self.commit("src/b.py", "1", "Fix b (#9)", "2025-03-03T00:00:00Z")
        self.commit("CHANGES.md", "1", "Release 1.0.1", "2025-03-04T00:00:00Z")
        self.merge("main", "Merge branch 'main' into 1.x", "2025-03-04T00:00:00Z")  # 本流を戻したマージは数えない
        self.git("switch", "-q", "main")
        self.merge("1.x", "Merge branch '1.x'", "2025-03-05T00:00:00Z")
        # 中で別の PR をマージした PR は、その PR も数える
        self.git("switch", "-q", "-c", "big")
        self.git("switch", "-q", "-c", "part")
        self.commit("src/c.py", "1", "Part (#10)", "2025-03-06T00:00:00Z")
        self.git("switch", "-q", "big")
        self.merge("part", "Merge pull request #11 from o/part\n\nPart", "2025-03-07T00:00:00Z")
        self.commit("src/c.py", "2", "Finish", "2025-03-07T00:00:00Z")
        self.git("switch", "-q", "main")
        self.merge("big", "Merge pull request #12 from o/big\n\nBig", "2025-03-08T00:00:00Z")
        self.run_script()
        self.assertIn("| [2025-03](2025-03.md) | 5 | まだ |", self.page("README.md"))
        self.assertIn("2025-03：5 件。", self.listing("2025-03"))
        self.assertIn("| [2025-02](2025-02.md) | 2 | まだ |", self.page("README.md"))

    def test_single_commit_prs_are_not_listed_twice(self):
        self.git("switch", "-q", "-c", "one")
        self.commit("src/a.py", "1", "Add a", "2025-03-01T00:00:00Z")
        self.git("switch", "-q", "main")
        self.merge("one", "Merge pull request #5 from o/one\n\nAdd a", "2025-03-02T00:00:00Z")
        march = self.listing("2025-03")
        self.assertIn("- 2025-03-02 Add a（[#5]", march)
        self.assertNotIn("  - Add a（", march)
        # 中のコミットが別のタイトルなら出す
        self.assertIn("  - Raise retries（", self.listing("2025-02"))

    def merge(self, branch, message, date):
        self.git("merge", "-q", "--no-ff", branch, "-m", message, env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})

    def test_fork_merges_give_authors_without_github(self):
        # フォークからのマージは、件名のフォークの持ち主が PR の作成者。noreply でないメールでも Author が出る
        self.git("config", "user.name", "Bob")
        self.git("config", "user.email", "bob@example.com")
        self.git("switch", "-q", "-c", "fix")
        self.commit("src/cache.py", "TTL = 1", "Fix cache", "2025-06-01T00:00:00Z")
        self.git("switch", "-q", "main")
        self.merge("fix", "Merge pull request #20 from bob-gh/fix\n\nFix cache", "2025-06-02T00:00:00Z")
        # 同じメールの、PR を通さない変更にも使う
        self.commit("src/cache.py", "TTL = 2", "Tune cache", "2025-06-03T00:00:00Z")
        # メンテナーが同じリポジトリのブランチでも使うメールは、フォークのマージに出ても使わない
        self.git("config", "user.email", "lead@example.com")
        for n, (owner, day) in enumerate([("carol-gh", "05"), ("o", "07")]):
            self.git("switch", "-q", "-c", f"b{n}")
            self.commit("src/db.py", str(n), f"Change db {n}", f"2025-06-{day}T00:00:00Z")
            self.git("switch", "-q", "main")
            self.merge(f"b{n}", f"Merge pull request #{21 + n} from {owner}/b{n}\n\nChange db {n}", f"2025-06-{day}T01:00:00Z")
        self.commit("src/db.py", "x", "Tidy db", "2025-06-08T00:00:00Z")
        self.assertEqual(self.run_script().returncode, 0)
        june = self.listing("2025-06")
        for line in ["Fix cache（[#20](https://github.com/o/r/pull/20)、src/、@bob-gh）", "Tune cache（[",
                     "Change db 0（[#21](https://github.com/o/r/pull/21)、src/、@carol-gh）",
                     "Change db 1（[#22](https://github.com/o/r/pull/22)、src/、—）"]:
            self.assertIn(line, june)
        self.assertRegex(june, r"Tune cache（\[[0-9a-f]{7}\][^\n]*、@bob-gh）")
        self.assertRegex(june, r"Tidy db（\[[0-9a-f]{7}\][^\n]*、—）")
        # 前に — と書いた行は、取れるようになった名前に替わる。取れない側は、書いてある名前を残す
        self.fill("2025-06", "| | キャッシュを直した | #20 | — |\n| | DB を変えた | #22 | @lead |")
        self.run_script()
        page = self.page("2025-06.md")
        self.assertIn("| キャッシュを直した | [#20](https://github.com/o/r/pull/20) | @bob-gh |", page)
        self.assertIn("| DB を変えた | [#22](https://github.com/o/r/pull/22) | @lead |", page)

    def test_default_branch_only_unless_branches_are_named(self):
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
        self.git("update-ref", "refs/remotes/origin/develop", "develop")
        self.git("branch", "-q", "-D", "develop", "feature-x")
        # 手元の main が古くても、origin のデフォルトブランチ（origin/HEAD の先の origin/main）を読む。develop は推測で足さない
        self.git("update-ref", "refs/remotes/origin/main", "main")
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
        self.git("update-ref", "refs/heads/main", "main~1")
        self.git("switch", "-q", "--detach", "origin/main")
        self.assertEqual(self.run_script().returncode, 0)
        may = self.listing("2025-05")
        self.assertIn("読んだブランチ：main（origin/main）", may)
        self.assertNotIn("develop（", may)
        # develop を読まなければ、main に入ったマージの下に、develop で入った PR が見える
        self.assertIn("- 2025-05-03 Release 2025-05（[#11](https://github.com/o/r/pull/11)、src/search/、@alice）\n"
                      "  - Raise search limit（[#10](https://github.com/o/r/pull/10)、@alice）", may)
        self.assertIn("- 2025-05-04 Shorten session（[#12](https://github.com/o/r/pull/12)、src/auth/、@alice）", may)
        self.assertNotIn("Merge branch 'main' into develop", may)
        # 表は、マージの中の PR を指してよい。日付は main に入った日
        self.fill("2025-05", "| | 検索の上限を上げた | #10 | |")
        self.run_script()
        self.assertIn("| 2025-05-03 | 検索の上限を上げた | [#10](https://github.com/o/r/pull/10) | @alice |", self.page("2025-05.md"))
        # 言われたブランチは全部読む。どれにも入ったコミットは 1 件、読んだブランチどうしのマージには印を付ける
        both = ("--branch", "origin/main", "--branch", "origin/develop")
        may = self.listing("2025-05", *both)
        for line in ["- 2025-05-02 Raise search limit（[#10](https://github.com/o/r/pull/10)、src/search/、@alice、origin/develop へ）",
                     "- 2025-05-03 （origin/develop から取り込み）Release 2025-05（[#11](https://github.com/o/r/pull/11)、",
                     "- 2025-05-05 （origin/main から取り込み）Merge branch 'main' into develop（["]:
            self.assertIn(line, may)
        feb = self.listing("2025-02", *both)
        self.assertEqual(feb.count("Extend session"), 1)
        self.assertIn("、origin/main・origin/develop へ）", feb)
        self.assertEqual(self.run_script("--branch", "nope").returncode, 2)

    def test_unknown_default_branch_is_not_guessed(self):
        # origin/HEAD がなければ、main や HEAD を推測せず、--branch を求めて止まる
        self.git("symbolic-ref", "--delete", "refs/remotes/origin/HEAD")
        result = self.run_script()
        self.assertEqual(result.returncode, 2)
        self.assertIn("デフォルトブランチが分からない", result.stderr)
        self.assertFalse((self.repo / "docs/change-history").exists())
        self.assertEqual(self.run_script("--branch", "main").returncode, 0)
        # gh があれば、GitHub のデフォルトブランチを聞いて origin/ のそれを読む
        self.git("update-ref", "refs/remotes/origin/trunk", "main")
        env = self.fake_gh('case "$*" in *default_branch*) echo trunk;; *) exit 1;; esac')
        result = self.run_script("--list", "2025-02", env=env)
        self.assertIn("読んだブランチ：trunk（origin/trunk）", result.stdout)

    def test_since_and_depth(self):
        self.run_script("--since", "2025-02", "--depth", "1")
        self.assertFalse((self.repo / "docs/change-history/2025-01.md").exists())
        self.assertIn("pull/2)、src/、—）", self.listing("2025-02", "--since", "2025-02", "--depth", "1"))
        self.assertEqual(self.run_script("--since", "2025-2").returncode, 2)


class WriterAgentTests(unittest.TestCase):
    """change-history-writer が、使うコマンドを Kiro で確認なしに通せるか。"""

    def test_kiro_writer_auto_approves_the_commands_it_needs(self):
        import json, re
        kiro = json.loads((ROOT / "agents/kiro/change-history-writer.json").read_text(encoding="utf-8"))
        allowed = [re.compile(p) for p in kiro["toolsSettings"]["shell"]["allowedCommands"]]
        for cmd in ("python3 .kiro/skills/change-history/scripts/build_history.py docs/change-history --list 2025-02",
                    "python3 .kiro/skills/change-history/scripts/build_history.py docs/change-history --list 2025-02 --branch main",
                    "python3 .kiro/skills/change-history/scripts/build_history.py docs/change-history --show abc1234",
                    "python3 .kiro/skills/change-history/scripts/build_history.py docs/change-history/o/r --list 2025-02"
                    " --repo .cache/change-history/o/r --branch main",
                    "git show --stat abc1234"):
            self.assertTrue(any(p.fullmatch(cmd) for p in allowed), cmd)
        for cmd in ("python3 .kiro/skills/change-history/scripts/build_history.py x; rm -rf ~", "python3 -c 'import os'", "git push"):
            self.assertFalse(any(p.fullmatch(cmd) for p in allowed), cmd)
        # 1 つのリポジトリの置き場所と、中央にまとめるときの <owner>/<repo> の下だけ
        self.assertEqual(kiro["toolsSettings"]["write"]["allowedPaths"], ["docs/change-history/*.md", "docs/change-history/*/*/*.md"])

    def test_writer_does_not_sort_into_categories(self):
        for path in ("agents/claude/change-history-writer.md", "skills/change-history/SKILL.md"):
            text = (ROOT / path).read_text(encoding="utf-8")
            for word in ("機能改善", "運用改善", "バグ対応", "### <分類>"):
                self.assertNotIn(word, text, path)

    def test_skill_calls_the_writer_by_name(self):
        self.assertIn("change-history-writer", (ROOT / "skills/change-history/SKILL.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
