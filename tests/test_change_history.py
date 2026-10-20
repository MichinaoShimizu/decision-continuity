"""change-history の build_history.py を、合成のリポジトリと偽の gh（tests/fake_gh.py）で回す。"""
import datetime
import json
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
FAKE_GH = pathlib.Path(__file__).resolve().parent / "fake_gh.py"
URL = "https://github.com/o/r"


class BuildHistoryTests(unittest.TestCase):

    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.work.name) / "r"
        self.repo.mkdir()
        self.bin = pathlib.Path(self.work.name) / "bin"
        self.bin.mkdir()
        (self.bin / "gh").write_text(f"#!/bin/sh\nexec {sys.executable} {FAKE_GH} \"$@\"\n", encoding="utf-8")
        (self.bin / "gh").chmod(0o755)
        self.fixture = pathlib.Path(self.work.name) / "gh.json"
        self.gh = {"default": "main", "pulls": [], "commits": {}}
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Real Name")
        self.git("config", "user.email", "real@example.com")
        self.git("remote", "add", "origin", "git@github.com:o/r.git")
        # 2025-01-31 23:30 UTC は JST で 2025-02-01
        self.commit("README.md", "a", "Initial import", "2025-01-10T00:00:00Z", login="carol")
        self.commit("src/auth/session.py", "TTL = 24", "Extend session (#2)", "2025-01-31T23:30:00Z", pr=2, login="bob")
        self.git("switch", "-q", "-c", "feature")
        self.commit("src/payment/client.py", "MAX = 5", "Raise retries", "2025-02-03T00:00:00Z")
        self.commit("docs/retry.md", "5", "Document retries", "2025-02-03T00:00:00Z")
        self.git("switch", "-q", "main")
        self.merge("feature", "Merge pull request #3 from o/feature\n\nRaise payment retries", "2025-02-04T00:00:00Z",
                   pr=3, login="alice", title="Raise payment retries")
        # マージされずに閉じた PR は数えない
        self.gh["pulls"].append({"number": 4, "login": "dave", "merged_at": None, "title": "Abandoned"})

    def tearDown(self):
        self.work.cleanup()

    def git(self, *args, env=None):
        return subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True, check=True,
                              env=dict(os.environ, **(env or {}))).stdout

    def write(self, path, text):
        (self.repo / path).parent.mkdir(parents=True, exist_ok=True)
        (self.repo / path).write_text(text + "\n", encoding="utf-8")

    def head(self):
        return self.git("rev-parse", "HEAD").strip()

    def commit(self, path, text, subject, date, pr=None, login=None, base="main", title=None):
        """コミットを足す。pr を言えば、そのコミットを入れた PR（squash）として GitHub に載せる。言わなければ直接のコミット。"""
        self.write(path, text)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", subject, env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})
        self.register(pr, login, date, title or subject.rsplit(" (#", 1)[0], base)
        return self.head()

    def merge(self, branch, message, date, pr=None, login=None, title=None, base="main"):
        self.git("merge", "-q", "--no-ff", branch, "-m", message, env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})
        self.register(pr, login, date, title or message.splitlines()[0], base)
        return self.head()

    def register(self, pr, login, date, title, base):
        if pr:
            self.gh["pulls"].append({"number": pr, "login": login, "merged_at": date, "sha": self.head(), "title": title, "base": base})
        elif login:
            self.gh["commits"][self.head()] = [login, "", ""]

    def run_script(self, *args, gh=True):
        self.fixture.write_text(json.dumps(self.gh), encoding="utf-8")
        path = f"{self.bin}{os.pathsep}{os.environ['PATH']}" if gh else os.pathsep.join(
            p for p in os.environ["PATH"].split(os.pathsep) if not (pathlib.Path(p) / "gh").exists())
        env = dict(os.environ, PATH=path, FAKE_GH=str(self.fixture))
        return subprocess.run([sys.executable, str(SCRIPT), "docs/change-history", *args], cwd=self.repo,
                              capture_output=True, text=True, check=False, env=env)

    def calls(self):
        """偽の gh が呼ばれた引数（呼ばれるたびに消す）。"""
        log = pathlib.Path(f"{self.fixture}.log")
        lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        log.unlink(missing_ok=True)
        return lines

    def listing(self, month, *args):
        result = self.run_script("--list", month, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def fill(self, month, text, old="（まだ書いていない）"):
        path = self.repo / "docs/change-history" / f"{month}.md"
        path.write_text(path.read_text(encoding="utf-8").replace(old, text), encoding="utf-8")

    def point(self, month, text):
        """年表の表の、その月の「まだ」を要約にする。"""
        path = self.repo / "docs/change-history/README.md"
        lines = [l.replace("| まだ |", f"| {text} |") if l.startswith(f"| [{month}]") else l
                 for l in path.read_text(encoding="utf-8").splitlines()]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def page(self, name):
        return (self.repo / "docs/change-history" / name).read_text(encoding="utf-8")

    def test_prs_and_direct_commits(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("読んだブランチ：main", result.stdout)
        # 月のファイルは見出しと主な変更だけ。全変更の一覧はファイルに書かない
        self.assertEqual(self.page("2025-02.md"), "# 2025-02\n\n## 主な変更\n\n（まだ書いていない）\n")
        jan, feb = self.listing("2025-01"), self.listing("2025-02")
        # 直接のコミットは、ハッシュのリンクと GitHub のコミットのアカウント
        sha = self.git("log", "-1", "--format=%H", "--grep", "Initial").strip()
        self.assertIn(f"- 2025-01-10 Initial import（[{sha[:7]}]({URL}/commit/{sha})、（ルート）、@carol）", jan)
        # PR は、マージの日（JST）・GitHub のタイトル・作成者。置き場所は PR を入れたコミットの変えたファイルから
        self.assertIn(f"- 2025-02-01 Extend session（[#2]({URL}/pull/2)、src/auth/、@bob）", feb)
        self.assertIn(f"- 2025-02-04 Raise payment retries（[#3]({URL}/pull/3)、docs/ ほか 1、@alice）", feb)
        self.assertIn("2025-02：2 件。読んだブランチ：main", feb)
        # PR の中のコミット、マージされずに閉じた PR、人の名前は出さない
        for text in ("Raise retries（", "Abandoned", "Real Name", "real@example.com"):
            self.assertNotIn(text, feb)
        index = self.page("README.md")
        self.assertTrue(index.startswith("# 変更の履歴\n\n## 2025\n\n（まだ書いていない）\n\n| 月 | 件数 | 主な変更 |"))
        self.assertIn("| [2025-02](2025-02.md) | 2 | まだ |\n| [2025-01](2025-01.md) | 1 | まだ |", index)
        self.assertEqual(self.run_script("--list", "2025-2").returncode, 2)

    def test_rebase_merged_commits_belong_to_their_pr(self):
        # Rebase and merge は、PR のコミットがそのまま並ぶ。GitHub が PR に結びつけるので、1 件にまとめる
        first = self.commit("src/search/a.py", "1", "Add index", "2025-03-02T00:00:00Z")
        self.commit("tests/test_a.py", "1", "Test index", "2025-03-02T00:00:00Z", pr=5, login="erin", title="Search index")
        self.gh["commits"][first] = ["erin", "5", "main"]
        mar = self.listing("2025-03") if self.run_script().returncode == 0 else ""
        self.assertIn(f"- 2025-03-02 Search index（[#5]({URL}/pull/5)、src/search/ ほか 1、@erin）", mar)
        self.assertIn("2025-03：1 件", mar)

    def test_prs_outside_the_local_history_are_listed(self):
        # 浅いクローンなどで手元にないコミットでも、GitHub の PR は載る（置き場所は分からない）
        self.gh["pulls"].append({"number": 1, "login": "bob", "merged_at": "2024-12-20T00:00:00Z", "sha": "f" * 40, "title": "Old"})
        self.run_script()
        self.assertIn(f"- 2024-12-20 Old（[#1]({URL}/pull/1)、@bob）", self.listing("2024-12"))

    def test_summary_table_is_filled_from_github(self):
        # 概要と PR だけ書けば、日付・Author・PR のリンクはスクリプトが入れる。書いてある Author も GitHub の値に直す
        self.run_script()
        self.fill("2025-02", "| 日付 | 概要 | PR | Author |\n|---|---|---|---|\n|  | 決済の再試行を増やした | #3 | @someone |")
        self.assertEqual(self.run_script("--check").returncode, 1)  # 表と索引が古い
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("README.md の 2025-02：主な変更の要約（表の「主な変更」の列）がない", result.stdout)
        self.point("2025-02", "決済の再試行とセッションを見直した")
        self.assertEqual(self.run_script().returncode, 0)
        self.assertEqual(self.page("2025-02.md"), "\n".join([
            "# 2025-02", "", "## 主な変更", "", "| 日付 | 概要 | PR | Author |", "|---|---|---|---|",
            f"| 2025-02-04 | 決済の再試行を増やした | [#3]({URL}/pull/3) | @alice |"]) + "\n")
        self.assertIn("| [2025-02](2025-02.md) | 2 | 決済の再試行とセッションを見直した |", self.page("README.md"))
        self.assertEqual(self.run_script("--check").returncode, 0)
        # いくつかの PR をまとめた行の日付は最初の PR の日
        self.fill("2025-02", f"| 2025-02-09 | 決済とセッション | #2、#3 | @carol |",
                  old=f"| 2025-02-04 | 決済の再試行を増やした | [#3]({URL}/pull/3) | @alice |")
        self.run_script()
        self.assertIn(f"| 2025-02-01 | 決済とセッション | [#2]({URL}/pull/2)、[#3]({URL}/pull/3) | @bob、@alice |", self.page("2025-02.md"))

    def test_pr_column_variants_are_read(self):
        # 全角の ＃、PR の URL、数字だけの列、PR を入れたコミットのハッシュも、日付・リンク・Author を埋める
        self.run_script()
        squash = self.git("log", "-1", "--format=%h", "--grep", "Extend session").strip()
        sha = self.git("log", "-1", "--format=%H", "--grep", "Initial").strip()
        self.fill("2025-02", "\n".join([
            "|  | 全角 | ＃３ |  |",
            f"|  | URL | {URL}/pull/3 |  |",
            "|  | 数字だけ | 2、3 |  |",
            f"|  | PR のコミットのハッシュ | {squash} |  |",
            "|  | 概要の数字は PR にしない | #3 ほか 2 件 |  |"]))
        self.fill("2025-01", f"|  | 直接のコミット | {sha[:9]} |  |")
        result = self.run_script()
        self.assertNotIn("参照", result.stdout)
        feb = self.page("2025-02.md")
        for summary in ("全角", "URL", "概要の数字は PR にしない"):
            self.assertIn(f"| 2025-02-04 | {summary} | [#3]({URL}/pull/3) | @alice |", feb)
        self.assertIn(f"| 2025-02-01 | 数字だけ | [#2]({URL}/pull/2)、[#3]({URL}/pull/3) | @bob、@alice |", feb)
        self.assertIn(f"| 2025-02-01 | PR のコミットのハッシュ | [#2]({URL}/pull/2) | @bob |", feb)
        self.assertIn(f"| 2025-01-10 | 直接のコミット | [{sha[:7]}]({URL}/commit/{sha}) | @carol |", self.page("2025-01.md"))

    def test_unknown_and_misplaced_references_are_reported(self):
        # 別の月の PR は日付・リンク・Author を入れて崩れとして、どこにもない PR はリンクだけ入れて崩れとして知らせる
        self.run_script()
        self.fill("2025-01", "| | セッションを延ばした | #2 | |\n| | ない PR | #99 | |\n| | 重なり | #2、#2、#99 | |")
        result = self.run_script()
        jan = self.page("2025-01.md")
        self.assertIn(f"| 2025-02-01 | セッションを延ばした | [#2]({URL}/pull/2) | @bob |", jan)
        self.assertIn(f"|  | ない PR | [#99]({URL}/pull/99) | — |", jan)
        self.assertIn(f"| [#2]({URL}/pull/2)、[#99]({URL}/pull/99) | @bob、— |", jan)
        self.assertEqual(result.stdout.count("PR の列の参照が、この月の変更にない"), 3)

    def test_decision_logs_that_cite_a_pr_are_linked_after_it(self):
        # PR を挙げた Decision log へのリンクを、PR の後ろに番号の順に添える。書き手が書かなくても、作り直すたびに入れ直す
        self.write("docs/decision-logs/0007-retry.md", "# 再試行\n\n- 2025-02-04 上限を 5 に（[PR #3][pr3]）\n\n"
                                                      f"[pr3]: {URL}/pull/3")
        self.write("docs/decision-logs/0002-retry-again.md", f"# 再試行の続き\n\n- [リンクだけ]({URL}/pull/3)")
        # 索引、ほかのリポジトリの PR、#3 の文だけのものは当たらない
        self.write("docs/decision-logs/README.md", f"- [PR #3]({URL}/pull/3)")
        self.write("docs/decision-logs/0003-other.md", "# ほか\n\n- https://github.com/x/y/pull/3 と #3")
        self.run_script()
        self.fill("2025-02", "|  | 決済の再試行を増やした | #3 |  |\n|  | セッションを延ばした | #2 |  |")
        self.run_script()
        rows = self.page("2025-02.md")
        self.assertIn(f"| [#3]({URL}/pull/3)、[DL-2](../decision-logs/0002-retry-again.md)、"
                      "[DL-7](../decision-logs/0007-retry.md) | @alice |", rows)
        self.assertIn(f"| [#2]({URL}/pull/2) | @bob |", rows)
        # リンクは PR の列の参照に数えない。作り直しても変わらず、Decision log が消えればリンクも消える
        self.point("2025-02", "再試行を増やした")
        self.assertEqual(self.run_script().returncode, 0)
        self.assertEqual(self.page("2025-02.md"), rows)
        self.assertEqual(self.run_script("--check").returncode, 0)
        (self.repo / "docs/decision-logs/0002-retry-again.md").unlink()
        self.assertEqual(self.run_script("--check").returncode, 1)
        self.run_script()
        self.assertIn(f"| [#3]({URL}/pull/3)、[DL-7](../decision-logs/0007-retry.md) |", self.page("2025-02.md"))
        # 置き場所は --decision-logs で変えられる
        shutil.move(self.repo / "docs/decision-logs", self.repo / "decisions")
        self.run_script("--decision-logs", "decisions")
        self.assertIn("、[DL-7](../../decisions/0007-retry.md) |", self.page("2025-02.md"))
        # --repo のとき（中央にまとめる）は、言われなければリンクしない
        self.write("docs/decision-logs/0007-retry.md", "- [PR #3][pr3]")
        self.run_script("--repo", ".")
        self.assertIn(f"| [#3]({URL}/pull/3) | @alice |", self.page("2025-02.md"))

    def test_github_is_asked_only_when_writing_and_only_for_new_things(self):
        self.run_script()
        first = self.calls()
        self.assertIn("api repos/o/r", first)
        self.assertTrue(any("pulls?state=closed&base=main" in c for c in first))
        self.assertTrue(any(c.startswith("api graphql") for c in first))  # 直接のコミットの Author と、Rebase の PR
        # --check・--list・--show は問い合わせない。覚えておいた分を使う
        self.run_script("--check")
        self.listing("2025-02")
        self.run_script("--show", "HEAD")
        self.assertEqual(self.calls(), [])
        # 2 回目からは、新しい PR のページだけを取り、知っているコミットは聞かない
        self.commit("src/a.py", "1", "Add a (#6)", "2025-03-01T00:00:00Z", pr=6, login="bob")
        self.run_script()
        again = self.calls()
        self.assertEqual(sum("pulls?" in c for c in again), 1)
        self.assertFalse(any(c.startswith("api graphql") for c in again))
        self.assertIn("Add a（", self.listing("2025-03"))
        # 覚えておいた分がなければ、--list は先に書き出すよう言う
        cache = pathlib.Path(self.git("rev-parse", "--git-common-dir").strip())
        (self.repo / cache / "decision-continuity-prs.json").unlink()
        result = self.run_script("--list", "2025-02")
        self.assertEqual(result.returncode, 2)
        self.assertIn("まだ GitHub から取っていない", result.stderr)

    def test_gh_and_a_github_origin_are_required(self):
        result = self.run_script(gh=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("gh が要る", result.stderr)
        self.gh["fail"] = True
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("gh api repos/o/r が失敗した: HTTP 502", result.stderr)
        self.assertFalse((self.repo / "docs/change-history").exists())
        self.gh["fail"] = False
        self.git("remote", "set-url", "origin", "https://gitlab.example.com/o/r.git")
        result = self.run_script()
        self.assertEqual(result.returncode, 2)
        self.assertIn("origin が GitHub でない", result.stderr)
        self.assertEqual(self.run_script("--github-repo", "o/r").returncode, 0)

    def test_default_branch_only_unless_branches_are_named(self):
        # GitHub のデフォルトブランチだけを読む。ほかのブランチの PR と直接のコミットは、言われたときだけ
        self.git("switch", "-q", "-c", "develop")
        self.commit("src/search/index.py", "LIMIT = 50", "Raise search limit (#10)", "2025-05-01T00:00:00Z",
                    pr=10, login="alice", base="develop")
        self.git("switch", "-q", "main")
        self.git("update-ref", "refs/remotes/origin/develop", "develop")
        self.git("branch", "-q", "-D", "develop")
        self.run_script()
        self.assertNotIn("2025-05", self.page("README.md"))
        # GitHub から取っていないブランチは、--list でも先に取るよう言う
        result = self.run_script("--list", "2025-05", "--branch", "develop")
        self.assertEqual(result.returncode, 2)
        self.assertIn("まだ GitHub から取っていない", result.stderr)
        self.run_script("--branch", "develop")
        result = self.run_script("--list", "2025-05", "--branch", "develop")
        self.assertIn(f"- 2025-05-01 Raise search limit（[#10]({URL}/pull/10)、src/search/、@alice）", result.stdout)
        self.assertIn("読んだブランチ：develop（origin/develop）", result.stdout)
        result = self.run_script("--branch", "nope")
        self.assertEqual(result.returncode, 2)
        self.assertIn("ブランチ nope が手元にない", result.stderr)
        # デフォルトブランチは GitHub の設定に従う。origin/ にあればそれを読む
        self.gh["default"] = "trunk"
        self.git("update-ref", "refs/remotes/origin/trunk", "main")
        self.assertIn("読んだブランチ：trunk（origin/trunk）", self.run_script().stdout)

    def test_quiet_months_are_written_by_the_script(self):
        subjects = ["Bump requests from 2.31 to 2.32", "build(deps): bump the pip group with 3 updates",
                    "chore(deps): update dependency ruff to v0.5", "Update dependency eslint to v9",
                    "[pre-commit.ci] pre-commit autoupdate"]
        for i, subject in enumerate(subjects):
            self.commit("requirements.txt", str(i), f"{subject} (#{20 + i})", f"2025-05-0{i + 1}T00:00:00Z", pr=20 + i, login="bot")
        self.commit("pyproject.toml", "1", "Release v0.9.0", "2025-05-09T00:00:00Z")
        self.commit("requirements.txt", "x", "Bump requests from 2.32 to 2.33 (#30)", "2025-06-01T00:00:00Z", pr=30, login="bot")
        self.git("switch", "-q", "-c", "stable")
        self.commit("src/a.py", "1", "Fix on stable", "2025-07-01T00:00:00Z")
        self.git("switch", "-q", "main")
        self.merge("stable", "Merge branch 'stable'", "2025-07-02T00:00:00Z")
        self.run_script()
        may = self.listing("2025-05")
        for subject in subjects:
            self.assertIn(f"（依存の更新）{subject}（", may)
        self.assertIn("（リリース）Release v0.9.0（", may)
        # 依存の更新・リリース・ブランチの取り込みだけの月は、書き手を呼ばずにスクリプトが書く
        self.assertIn("- 目立った変更なし（依存の更新・リリースのみ）", self.page("2025-05.md"))
        self.assertIn("- 目立った変更なし（依存の更新のみ）", self.page("2025-06.md"))
        self.assertIn("- 目立った変更なし（ブランチの取り込みのみ）", self.page("2025-07.md"))
        self.assertIn("| [2025-06](2025-06.md) | 1 | 目立った変更なし（依存の更新のみ） |", self.page("README.md"))
        self.assertIn("主な変更をまだ書いていない月（2）：2025-01、2025-02", self.run_script().stdout)
        # 書いたものは上書きしない
        self.fill("2025-06", "| | requests を上げた | #30 | |", old="- 目立った変更なし（依存の更新のみ）")
        self.run_script()
        self.assertIn("requests を上げた", self.page("2025-06.md"))
        # 終わっていない月は、あとから変更が増えるので書かない
        now = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Tokyo"))
        self.commit("requirements.txt", "y", "Bump requests from 2.33 to 2.34 (#31)",
                    now.astimezone(datetime.timezone.utc).isoformat(), pr=31, login="bot")
        self.run_script()
        self.assertIn("（まだ書いていない）", self.page(f"{now:%Y-%m}.md"))

    def test_quiet_months_and_years_stay_in_the_timeline(self):
        self.commit("src/a.py", "1", "Pick it up again (#7)", "2027-03-01T00:00:00Z", pr=7, login="bob")
        self.assertEqual(self.run_script().returncode, 0)
        index = self.page("README.md")
        # 変更のなかった月も 0 件の行で載せ（月のファイルは作らない）、年ごと変更のない年は要点を「変更なし」にする
        self.assertIn("| [2027-03](2027-03.md) | 1 | まだ |\n| 2027-01〜2027-02 | 0 | 変更なし |\n", index)
        self.assertIn("## 2026\n\n変更なし\n\n| 月 | 件数 | 主な変更 |\n|---|---|---|\n| 2026-01〜2026-12 | 0 | 変更なし |\n", index)
        self.assertIn("| 2025-03〜2025-12 | 0 | 変更なし |\n| [2025-02](2025-02.md) | 2 | まだ |", index)
        self.assertFalse((self.repo / "docs/change-history/2025-03.md").exists())
        self.assertEqual(self.run_script("--check").returncode, 0)

    def test_old_forms_are_rewritten(self):
        # 前の形（分類の見出しと説明、「- 概要（#3）」、「## 一覧」、timeline.md）は、作り直すと今の形になる
        self.run_script()
        folder = self.repo / "docs/change-history"
        (folder / "2025-02.md").write_text(
            "# 2025-02\n\nマージされた変更 2 件。\n\n## 主な変更\n\n### 運用改善\n\n- 決済の再試行を a|b に（[#3](x)）\n"
            "\n### 機能改善\n\n使う人に見える機能の追加と変更\n\n- セッションを延ばした（#2）\n\n## 一覧\n\n- 2025-02-01 Extend session\n",
            encoding="utf-8")
        (folder / "README.md").write_text("# 変更の履歴\n\n| 月 | 件数 | 主な変更を書いたか |\n", encoding="utf-8")
        (folder / "timeline.md").write_text("# 年表\n\n## 2025\n\n### バグ対応\n\n不具合の修正と、その再発を防ぐ変更\n\n"
                                            "- 前に書いた要点（2025-02）\n\n| 月 | 件数 | 主な変更 |\n", encoding="utf-8")
        self.run_script()
        self.assertEqual(self.page("2025-02.md"), "\n".join([
            "# 2025-02", "", "## 主な変更", "", "| 日付 | 概要 | PR | Author |", "|---|---|---|---|",
            f"| 2025-02-01 | セッションを延ばした | [#2]({URL}/pull/2) | @bob |",
            f"| 2025-02-04 | 決済の再試行を a\\|b に | [#3]({URL}/pull/3) | @alice |"]) + "\n")
        self.assertIn("## 2025\n\n- 前に書いた要点（2025-02）\n\n| 月 |", self.page("README.md"))
        self.assertFalse((folder / "timeline.md").exists())

    def test_broken_summaries_are_reported(self):
        self.run_script()
        self.fill("2025-02", "\n".join([
            "認証を変えた", "| | 5 月に延ばした | #2 | |", "| | PR がない | なし | |", "| | 列が 3 つ | #2 |",
            "| | 翻訳 | #2、#3、#91、#92、#93、#94 | |", "| |  | #3 | |"]))
        path = self.repo / "docs/change-history/README.md"
        path.write_text(path.read_text(encoding="utf-8").replace("（まだ書いていない）", "- 期間がない\n- 3 月に始めた（2025-03）"),
                        encoding="utf-8")
        result = self.run_script("--check")
        self.assertEqual(result.returncode, 1)
        for want in ["2025-02.md の「## 主な変更」1 行目：表の行だけを書く",
                     "行目：日付は YYYY-MM-DD、月は YYYY-MM で書く",
                     "行目：PR の列に PR かコミット",
                     "行目：表の行は | 日付 | 概要 | PR | Author | の 4 列で書く",
                     "行目：PR は 1 行に 5 件まで",
                     "行目：概要の列が空",
                     "README.md の「## 2025」1 行目：行の末尾に（YYYY-MM）か（YYYY-MM〜YYYY-MM）がない",
                     "README.md の「## 2025」2 行目：日付は YYYY-MM-DD"]:
            self.assertIn(want, result.stdout)
        self.assertEqual(self.run_script().returncode, 1)
        # まだ書いていない・目立った変更なしは通す
        (self.repo / "docs/change-history/2025-02.md").write_text("# 2025-02\n\n## 主な変更\n\n- 目立った変更なし（リリースのみ）\n",
                                                                  encoding="utf-8")
        path.write_text(path.read_text(encoding="utf-8").replace("- 期間がない\n- 3 月に始めた（2025-03）", "- 始めた（2025-01〜2025-02）"),
                        encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 0)
        self.assertIn("| [2025-02](2025-02.md) | 2 | 目立った変更なし（リリースのみ） |", self.page("README.md"))
        self.assertEqual(self.run_script("--check").returncode, 0)

    def test_rebuilding_twice_changes_nothing(self):
        self.run_script()
        sha = self.git("log", "-1", "--format=%H", "--grep", "Initial").strip()
        self.fill("2025-02", "\n".join(["### security", f"| | 別の月のコミット | {sha[:9]} | |", "- 前の形（#3）",
                                         "- 読めない（#99）", "| | まとめ | [#2](x)、#3 | @someone |", "| | 後 | #3 | |"]))
        self.run_script()
        first = {p.name: p.read_text(encoding="utf-8") for p in (self.repo / "docs/change-history").glob("*.md")}
        self.run_script()
        second = {p.name: p.read_text(encoding="utf-8") for p in (self.repo / "docs/change-history").glob("*.md")}
        self.assertEqual(first, second)
        rows = [l for l in second["2025-02.md"].splitlines() if l.startswith("| 20") or l.startswith("|  |")]
        self.assertEqual([r.split(" | ")[0] for r in rows], ["| 2025-01-10", "| 2025-02-01", "| 2025-02-04", "| 2025-02-04", "| "])
        self.assertNotIn("が古い", self.run_script("--check").stdout)

    def test_since_until_and_depth(self):
        self.commit("src/a/b/c.py", "1", "Deep (#8)", "2025-04-01T00:00:00Z", pr=8, login="bob")
        self.run_script("--since", "2025-02", "--until", "2025-03")
        folder = self.repo / "docs/change-history"
        self.assertFalse((folder / "2025-01.md").exists())
        self.assertFalse((folder / "2025-04.md").exists())
        self.assertTrue((folder / "2025-02.md").exists())
        self.assertIn("Deep（[#8](https://github.com/o/r/pull/8)、src/、@bob）", self.listing("2025-04", "--depth", "1"))
        self.assertIn("Deep（[#8](https://github.com/o/r/pull/8)、src/a/b/、@bob）", self.listing("2025-04", "--depth", "3"))
        self.assertEqual(self.run_script("--since", "2025-2").returncode, 2)
        # 前から年表にある月は、絞っても消さない
        self.run_script()
        self.run_script("--since", "2025-04")
        self.assertIn("| [2025-01](2025-01.md) | 1 | まだ |", self.page("README.md"))

    def test_show_hides_names(self):
        self.run_script()
        shown = self.run_script("--show", "HEAD~1").stdout
        self.assertIn("Extend session (#2)", shown)
        self.assertIn("src/auth/session.py", shown)
        self.assertNotIn("Real Name", shown)

    def test_empty_repository(self):
        with tempfile.TemporaryDirectory() as empty:
            subprocess.run(["git", "init", "-q", empty], check=True)
            result = subprocess.run([sys.executable, str(SCRIPT), "docs/change-history"], cwd=empty, capture_output=True, text=True)
            self.assertEqual((result.returncode, result.stdout.strip()), (0, "コミットがまだないので、書くものはない"))


class WriterAgentTests(unittest.TestCase):
    """change-history-writer が、使うコマンドを Kiro で確認なしに通せるか。"""

    def test_kiro_writer_auto_approves_the_commands_it_needs(self):
        import re
        kiro = json.loads((ROOT / "agents/kiro/change-history-writer.json").read_text(encoding="utf-8"))
        allowed = [re.compile(p) for p in kiro["toolsSettings"]["shell"]["allowedCommands"]]
        for cmd in ("python3 .kiro/skills/change-history/scripts/build_history.py docs/change-history --list 2025-02",
                    "python3 .kiro/skills/change-history/scripts/build_history.py docs/change-history --list 2025-02 --branch main",
                    "python3 .kiro/skills/change-history/scripts/build_history.py docs/change-history --show abc1234",
                    "python3 .kiro/skills/change-history/scripts/build_history.py docs/change-history/o/r --list 2025-02"
                    " --repo .cache/change-history/o/r --github-repo o/r --branch main",
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
