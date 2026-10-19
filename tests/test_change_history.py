"""change-history の build_history.py を、合成のリポジトリで回す。"""
import os
import pathlib
import shutil
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
        # 概要と PR だけ書けば、日付・Author・PR のリンクと分類の説明はスクリプトが入れる
        self.run_script()
        self.fill("2025-02", "### 運用改善\n\n| 日付 | 概要 | PR | Author |\n|---|---|---|---|\n|  | 決済の再試行を増やした | #3 |  |")
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
            "# 2025-02", "", "## 主な変更", "", "### 運用改善", "",
            "開発・リリース・運用の進め方の改善（CI、デプロイ、監視、手順、文書など）", "",
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
        self.fill("2025-01", f"### 運用改善\n\n| | 始めた | [{sha[:7]}](https://github.com/o/r/commit/{sha}) | |")
        self.assertEqual(self.run_script().returncode, 1)  # 2025-01 の要約がまだ
        self.assertIn(f"| 2025-01-10 | 始めた | [{sha[:7]}](https://github.com/o/r/commit/{sha}) | — |", self.page("2025-01.md"))
        self.commit("src/auth/session.py", "TTL = 48", "Longer session (#4)", "2025-02-10T00:00:00Z")
        self.assertEqual(self.run_script("--check").returncode, 1)

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
        self.fill("2025-02", "### 機能改善\n\n| | セッションを延ばした | #2 | |")
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
        self.fill("2025-02", "### 機能改善\n\n| | セッションを延ばした | #2 | |")
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
        self.fill("2025-01", "### 機能改善\n\n| | 始めた | " + self.git("log", "-1", "--format=%h", "--grep", "Initial").strip() + " | |")
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
        self.fill("2025-02", "### バグ対応\n\n- 旧（#99）")
        result = self.run_script()
        self.assertIn("|  | 旧 | [#99](https://github.com/o/r/pull/99) | — |", self.page("2025-02.md"))
        self.assertIn("PR の列の参照が、この月の変更にない", result.stdout)
        self.assertNotIn("下に行がない", result.stdout)

    def test_rows_are_filled_even_when_they_break_the_rules(self):
        # 別の月の PR を書いても、決まりにない見出しの下に書いても、リンク・日付・Author は入れ、崩れとして知らせる
        self.run_script()
        self.fill("2025-01", "### security\n\n| | セッションを延ばした | #2 | |")
        result = self.run_script()
        self.assertIn("| 2025-02-01 | セッションを延ばした | [#2](https://github.com/o/r/pull/2) | — |", self.page("2025-01.md"))
        self.assertIn("分類 security は", result.stdout)
        self.assertIn("PR の列の参照が、この月の変更にない", result.stdout)

    def test_duplicate_and_unknown_references_are_kept(self):
        # 同じ PR を 2 度書いても、後ろの読めない参照を落とさない。どこにもないハッシュは書かれたまま
        self.run_script()
        self.fill("2025-02", "### 機能改善\n\n| | 重なり | #2、#2、#99 | |\n| | ハッシュ | deadbeef1 | |")
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
        self.fill("2025-02", "### 機能改善\n\n| | 後 | #3 | |\n| | 読めない | #99 | |\n| | 先 | #2 | |")
        self.fill("2025-01", "- 目立った変更なし（依存の更新のみ）")
        self.run_script()
        feb = self.page("2025-02.md")
        self.assertLess(feb.index("| 先 |"), feb.index("| 後 |"))
        self.assertLess(feb.index("| 後 |"), feb.index("| 読めない |"))
        self.assertIn("| [2025-01](2025-01.md) | 1 | 目立った変更なし（依存の更新のみ） |", self.page("README.md"))

    def test_too_many_references_in_a_row_are_reported(self):
        self.run_script()
        self.fill("2025-02", "### 運用改善\n\n| | 翻訳 | #2、#3、#91、#92、#93、#94 | |")
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
        # 前の形（「- 概要（#3）」と「## 一覧」）は、作り直すと表になり、一覧は消える
        self.run_script()
        path = self.repo / "docs/change-history/2025-02.md"
        path.write_text("# 2025-02\n\nマージされた変更 2 件。\n\n## 主な変更\n\n### 運用改善\n\n- 決済の再試行を a|b に（[#3](x)）\n"
                        "\n### 機能改善\n\n- セッションを延ばした（#2）\n\n## 一覧\n\n- 2025-02-01 Extend session\n", encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 1)  # 要約がまだ
        feb = self.page("2025-02.md")
        self.assertNotIn("一覧", feb)
        self.assertNotIn("マージされた変更", feb)
        self.assertIn("| 2025-02-04 | 決済の再試行を a\\|b に | [#3](https://github.com/o/r/pull/3) | @alice |", feb)
        self.assertIn("使う人に見える機能の追加と変更", feb)
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
        # 以前の 11 種の分類は、年でも月でも崩れとして出る
        path.write_text(text.replace("（まだ書いていない）", "### reliability\n\n- 決済の再試行を見直した（2025-02）"), encoding="utf-8")
        self.fill("2025-02", "### security\n\n| | セッションを延ばした | #2 | |")
        result = self.run_script("--check")
        self.assertIn("README.md の「## 2025」1 行目：分類 reliability は 機能改善・運用改善・バグ対応 のどれでもない", result.stdout)
        self.assertIn("2025-02.md の「## 主な変更」1 行目：分類 security は 機能改善・運用改善・バグ対応 のどれでもない", result.stdout)

    def test_broken_summaries_are_reported(self):
        self.run_script()
        folder = self.repo / "docs/change-history"
        self.fill("2025-02", "\n".join([
            "認証を変えた", "### セキュリティ", "| | x | #2 | |", "### 機能改善", "| | 5 月に延ばした | #2 | |",
            "| | ない PR | #99 | |", "| | PR がない | なし | |", "| | 列が 3 つ | #2 |", "### 機能改善", "| | もう 1 つ | #2 | |",
            "### 運用改善", "* 記号が違う", "### バグ対応"]))
        path = folder / "README.md"
        path.write_text(path.read_text(encoding="utf-8").replace("（まだ書いていない）", "### 機能改善\n\n- 期間がない\n- 3 月に始めた（2025-03）"), encoding="utf-8")
        result = self.run_script("--check")
        self.assertEqual(result.returncode, 1)
        for want in ["2025-02.md の「## 主な変更」1 行目：### <分類> と表の行だけを書く",
                     "行目：分類 セキュリティ は 機能改善・運用改善・バグ対応 のどれでもない",
                     "行目：日付は YYYY-MM-DD、月は YYYY-MM で書く",
                     "行目：PR の列の参照が、この月の変更にない",
                     "行目：PR の列に PR かコミット",
                     "行目：表の行は | 日付 | 概要 | PR | Author | の 4 列で書く",
                     "行目：分類 機能改善 が 2 度ある",
                     "行目：### <分類> と表の行だけを書く",
                     "行目：### バグ対応 の下に行がない",
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
        self.fill("2025-06", "### バグ対応\n\n| | キャッシュを直した | #20 | — |\n| | DB を変えた | #22 | @lead |")
        self.run_script()
        page = self.page("2025-06.md")
        self.assertIn("| キャッシュを直した | [#20](https://github.com/o/r/pull/20) | @bob-gh |", page)
        self.assertIn("| DB を変えた | [#22](https://github.com/o/r/pull/22) | @lead |", page)

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
        self.fill("2025-05", "### 機能改善\n\n| | 検索の上限を上げた | #10 | |")
        self.run_script("--branch", "main")
        self.assertIn("| 2025-05-03 | 検索の上限を上げた | [#10](https://github.com/o/r/pull/10) | @alice |", self.page("2025-05.md"))
        self.assertEqual(self.run_script("--branch", "nope").returncode, 2)

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
                    "git show --stat abc1234"):
            self.assertTrue(any(p.fullmatch(cmd) for p in allowed), cmd)
        for cmd in ("python3 .kiro/skills/change-history/scripts/build_history.py x; rm -rf ~", "python3 -c 'import os'", "git push"):
            self.assertFalse(any(p.fullmatch(cmd) for p in allowed), cmd)
        self.assertEqual(kiro["toolsSettings"]["write"]["allowedPaths"], ["docs/change-history/*.md"])

    def test_writer_names_the_scripts_categories(self):
        import re, sys
        sys.path.insert(0, str(SCRIPT.parent))
        import build_history
        body = (ROOT / "agents/claude/change-history-writer.md").read_text(encoding="utf-8")
        line = next(l for l in body.splitlines() if "分類は" in l)
        self.assertEqual(re.findall(r"`(.+?)`（", line), list(build_history.DESCRIPTIONS))

    def test_skill_calls_the_writer_by_name(self):
        self.assertIn("change-history-writer", (ROOT / "skills/change-history/SKILL.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
