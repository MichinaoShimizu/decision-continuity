"""decision-log のスキル・スクリプト・サブエージェントの定義のテスト。標準ライブラリだけを使う。"""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


class ReaderAgentTests(unittest.TestCase):
    """decision-log-reader に固有の検査。3 つの定義が揃っているかは tests/test_docs.py が見る。"""
    ROOT = pathlib.Path(__file__).resolve().parents[1]

    def test_skill_calls_the_reader_by_name(self):
        self.assertIn("decision-log-reader", (self.ROOT / "skills/decision-log/SKILL.md").read_text(encoding="utf-8"))

    def test_kiro_reader_auto_approves_the_commands_it_needs(self):
        import re
        kiro = json.loads((self.ROOT / "agents/kiro/decision-log-reader.json").read_text(encoding="utf-8"))
        allowed = [re.compile(p) for p in kiro["toolsSettings"]["shell"]["allowedCommands"]]
        for cmd in ("gh pr view 101 --json number,title,body,author,createdAt,mergedAt,mergedBy,url,reviews,comments,files",
                    "git show --stat abc1234", "git show abc1234 -- src/payment/http/client.py",
                    "git show abc1234:src/payment/http/client.py", "git grep -n MAX_RETRIES abc1234",
                    "TZ=Asia/Tokyo git log --first-parent --date=short-local --format=%h",
                    "gh api repos/o/r/pulls/45", "gh api repos/o/r/pulls/45/reviews", "gh api repos/o/r/issues/45/comments",
                    "gh api repos/o/r/pulls/45/comments", "gh api repos/o/r/issues/42", "gh api repos/o/r/issues/42/comments",
                    "git log --format='%h %s%n%b' abc1234^1..abc1234", "git show -s --format=%B abc1234"):
            self.assertTrue(any(p.fullmatch(cmd) for p in allowed), cmd)
        for glob in kiro["permissions"]["rules"][0]["match"]:
            self.assertRegex(glob, r"^(TZ=Asia/Tokyo )?(git (show|log|grep|rev-parse)|gh pr view) \*$")


class PlannerAgentTests(unittest.TestCase):
    """decision-log-planner に固有の検査。メインの会話でコマンドを回さずに済むよう、手順 0〜1 のコマンドが確認なしで通るか。"""
    ROOT = pathlib.Path(__file__).resolve().parents[1]
    COMMANDS = ("git remote get-url origin", "git rev-parse HEAD", "git rev-parse --is-shallow-repository",
                "TZ=Asia/Tokyo git log --first-parent --date=short-local --format='@@ %h %ad %s' --name-only -- src/payment/",
                "git log --first-parent --merges --format='@@ %h %b'",
                "git log --first-parent -i -G 'timeout|retr(y|ies)|limit' --format='%h' -- . ':(exclude)*lock*' ':(exclude)*.snap'",
                "git log --first-parent -G '^[A-Z][A-Z0-9_]{2,} *[:=]' --format='%h' -- .",
                "git log --first-parent --format='%h' -- '*.yml' '*.yaml' ':(exclude)*lock*'",
                "git show --stat abc1234")

    def test_skill_calls_the_planner_by_name(self):
        self.assertIn("decision-log-planner", (self.ROOT / "skills/decision-log/SKILL.md").read_text(encoding="utf-8"))

    def test_kiro_planner_auto_approves_the_commands_it_needs(self):
        import re
        kiro = json.loads((self.ROOT / "agents/kiro/decision-log-planner.json").read_text(encoding="utf-8"))
        allowed = [re.compile(p) for p in kiro["toolsSettings"]["shell"]["allowedCommands"]]
        for cmd in self.COMMANDS:
            self.assertTrue(any(p.fullmatch(cmd) for p in allowed), cmd)
        for cmd in ("git log 'x'$(id)", "git log \"$(id)\"", "git log 'a\nb'", "gh pr view 1", "git fetch --unshallow"):
            self.assertFalse(any(p.fullmatch(cmd) for p in allowed), cmd)

    def test_planner_uses_the_same_words_as_the_fallback_steps(self):
        # 調べ役がないときはメインが investigation.md の手順を回すので、言葉と定数の正規表現を揃えておく
        import re
        planner = (self.ROOT / "agents/claude/decision-log-planner.md").read_text(encoding="utf-8")
        steps = (self.ROOT / "skills/decision-log/references/investigation.md").read_text(encoding="utf-8")
        for pattern in (r"既定：(`[^`]+`)", r"(`\^\[A-Z\]\[A-Z0-9_\]\{2,\} \*\[:=\]`)"):
            self.assertEqual(re.findall(pattern, planner), re.findall(pattern, steps), pattern)
            self.assertTrue(re.findall(pattern, planner), pattern)


class SkillAllowedToolsTests(unittest.TestCase):
    """decision-log は信頼できない PR の本文を読むので、確認なしで通すのは読むだけのコマンドに限る。"""
    SKILL = pathlib.Path(__file__).resolve().parents[1] / "skills" / "decision-log" / "SKILL.md"

    def test_only_read_commands_are_preapproved(self):
        import re
        front = self.SKILL.read_text(encoding="utf-8").split("---", 2)[1]
        line = next(l for l in front.splitlines() if l.startswith("allowed-tools:"))
        rules = re.findall(r"Bash\(([^)]*)\)", line)
        self.assertTrue(rules)
        read_only = re.compile(r"^(TZ=Asia/Tokyo )?git (log|show|grep|rev-parse|remote get-url):\*$"
                               r"|^(gh (pr|issue|release)|glab (mr|issue)) view:\*$"
                               r"|^python3 (\.(claude|kiro)/skills/decision-log|\$\{CLAUDE_SKILL_DIR\})/scripts/build_index\.py:\*$")
        for rule in rules:
            self.assertRegex(rule, read_only)


class BuildIndexTests(unittest.TestCase):
    """decision-log の scripts/build_index.py が、決まりどおりの索引を作るかを確かめる。"""
    SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "skills" / "decision-log" / "scripts" / "build_index.py"

    @staticmethod
    def log(category, title, dates, reason, notes=""):
        claims = "\n".join(f"- C{i} {d} いまも同じ：x。履歴：y ／ 現在：z" for i, d in enumerate(dates, 1))
        return (f"---\nkind: log\ncategory: {category}\n---\n\n# [demo] {title}\n\n> 過去の観察である。\n\n"
                f"## 起きたこと\n\n{claims}\n\n## 理由\n\n{reason}\n{notes}")

    def run_script(self, folder, *extra):
        return subprocess.run([sys.executable, str(self.SCRIPT), str(folder), "--repo", "demo", *extra],
                              capture_output=True, text=True, check=False)

    def test_groups_orders_and_marks(self):
        with tempfile.TemporaryDirectory() as directory:
            d = pathlib.Path(directory)
            (d / "0001.md").write_text(self.log("reliability", "上限が 5 に", ["2025-03-04"], "不明（記録に書かれていない）。"), encoding="utf-8")
            (d / "0002.md").write_text(self.log("reliability", "タイムアウトが 5 秒に", ["2024-12-01", "2024-11-20"], "不明。",
                                                "\n---\n\n## 追記 2026-01-01（x）\n\n**分かった**（2026-01-01）：「なぜ」\n障害対応。\n"), encoding="utf-8")
            (d / "0003.md").write_text(self.log("security", "署名検証を追加", ["2025-05-01"], "記録あり（議論）：監査の指摘（PR #9）。",
                                                "\n---\n\n## 追記 2026-01-02（x）\n\n**分類を更新**（2026-01-02）\ncategory: data\n"), encoding="utf-8")
            (d / "0004.md").write_text(self.log("data", "重複", ["2023-01-01"], "不明。",
                                                "\n---\n\n## 追記 2026-01-03（x）\n\n**終了**（2026-01-03）：DL-3 と重複\n"), encoding="utf-8")
            result = self.run_script(d)
            self.assertEqual(result.returncode, 0, result.stderr)
            index = (d / "README.md").read_text(encoding="utf-8")
            self.assertIn("## データの意味・持ち方（data）\n\nスキーマ、値の意味と単位、保存先、保持期間（個人情報は privacy）\n\n"
                          "- 2025-05-01 [DL-3](0003.md) 署名検証を追加\n", index)
            self.assertIn("- 2024-11-20 [DL-2](0002.md) タイムアウトが 5 秒に\n- 2025-03-04 [DL-1](0001.md) 上限が 5 に・理由不明", index)
            self.assertIn("## 取り下げ\n\n- 2023-01-01 [DL-4](0004.md) 重複・理由不明", index)
            self.assertNotIn("security", index)
            self.assertLess(index.index("（data）"), index.index("（reliability）"))
            self.assertEqual(self.run_script(d, "--check").returncode, 0)
            (d / "README.md").write_text("old", encoding="utf-8")
            self.assertEqual(self.run_script(d, "--check").returncode, 1)

    def test_categories_match_the_reference_table(self):
        """索引に出す分類と中身が、references/categories.md の表と同じかを確かめる。"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("build_index", self.SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        table = (self.SCRIPT.parents[1] / "references" / "categories.md").read_text(encoding="utf-8").split("## 英語で書くとき")[0]
        rows = [[c.strip() for c in line.strip("|").split("|")] for line in table.splitlines()
                if line.startswith("| `") and not line.startswith("| `category`")]
        self.assertEqual([(k.strip("`"), l, d) for k, l, d in rows], [tuple(c) for c in module.CATEGORIES])

    def test_categories_en_match_the_reference_table(self):
        """英語の索引に出す分類と中身が、references/categories.md の英語の表と同じかを確かめる。"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("build_index", self.SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        table = (self.SCRIPT.parents[1] / "references" / "categories.md").read_text(encoding="utf-8").split("## 英語で書くとき")[1]
        rows = [[c.strip() for c in line.strip("|").split("|")] for line in table.splitlines()
                if line.startswith("| `") and not line.startswith("| `category`")]
        self.assertEqual({k.strip("`"): (l, d) for k, l, d in rows}, module.CATEGORIES_EN)
        self.assertEqual(list(module.CATEGORIES_EN), [k for k, _, _ in module.CATEGORIES])

    @staticmethod
    def log_en(category, title, dates, reason, notes=""):
        claims = "\n".join(f"- C{i} {d} Still true: x. History: y / Now: z" for i, d in enumerate(dates, 1))
        return (f"---\nkind: log\ncategory: {category}\n---\n\n# [demo] {title}\n\n> A past observation.\n\n"
                f"## What happened\n\n{claims}\n\n## Reason\n\n{reason}\n{notes}")

    def test_english_logs_and_index(self):
        with tempfile.TemporaryDirectory() as directory:
            d = pathlib.Path(directory)
            (d / "0001.md").write_text(self.log_en("reliability", "Limit became 5", ["2025-03-04"], "Unknown (not recorded)."), encoding="utf-8")
            (d / "0002.md").write_text(self.log_en("reliability", "Timeout became 5 s", ["2024-11-20"], "Unknown (not recorded).",
                                                   "\n---\n\n## Addendum 2026-01-01 (x)\n\n**Answered** (2026-01-01): \"why\"\nAn outage.\n"), encoding="utf-8")
            (d / "0003.md").write_text(self.log_en("security", "Signature check", ["2025-05-01"], "Documented (discussion): audit (PR #9).",
                                                   "\n---\n\n## Addendum 2026-01-02 (x)\n\n**Category updated** (2026-01-02)\ncategory: data\n"), encoding="utf-8")
            (d / "0004.md").write_text(self.log_en("data", "Duplicate", ["2023-01-01"], "Inferred: a copy.",
                                                   "\n---\n\n## Addendum 2026-01-03 (x)\n\n**Retired** (2026-01-03): duplicate of DL-3\n"), encoding="utf-8")
            result = self.run_script(d)
            self.assertEqual(result.returncode, 0, result.stdout)
            index = (d / "README.md").read_text(encoding="utf-8")
            self.assertTrue(index.startswith("# Decision logs (demo)\n"))
            self.assertIn("## Data meaning and storage (data)\n\n" + "Schemas, meaning and units of values, where data is stored, "
                          "retention (personal data is privacy)\n\n- 2025-05-01 [DL-3](0003.md) Signature check\n", index)
            self.assertIn("- 2024-11-20 [DL-2](0002.md) Timeout became 5 s\n- 2025-03-04 [DL-1](0001.md) Limit became 5 · reason unknown", index)
            self.assertIn("## Retired\n\n- 2023-01-01 [DL-4](0004.md) Duplicate\n", index)
            checked = subprocess.run([sys.executable, str(self.SCRIPT), str(d), "--check"], capture_output=True, text=True, check=False)
            self.assertEqual(checked.returncode, 0, checked.stdout)
            # 日本語の log が増えても、いまの索引の言語を保つ
            (d / "0005.md").write_text(self.log("data", "日本語", ["2025-06-01"], "不明。"), encoding="utf-8")
            (d / "0006.md").write_text(self.log("data", "日本語 2", ["2025-06-02"], "不明。"), encoding="utf-8")
            (d / "0007.md").write_text(self.log("data", "日本語 3", ["2025-06-03"], "不明。"), encoding="utf-8")
            (d / "0008.md").write_text(self.log("data", "日本語 4", ["2025-06-04"], "不明。"), encoding="utf-8")
            (d / "0009.md").write_text(self.log("data", "日本語 5", ["2025-06-05"], "不明。"), encoding="utf-8")
            self.assertEqual(self.run_script(d).returncode, 0)
            index = (d / "README.md").read_text(encoding="utf-8")
            self.assertIn("- 2025-06-01 [DL-5](0005.md) 日本語 · reason unknown", index)
            self.assertEqual(self.run_script(d, "--lang", "ja").returncode, 0)
            self.assertTrue((d / "README.md").read_text(encoding="utf-8").startswith("# Decision logs（demo）\n"))

    def test_reports_malformed_english_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            d = pathlib.Path(directory)
            (d / "0001.md").write_text(self.log_en("data", "x", ["2025-01-01"], "Because we wanted to."), encoding="utf-8")
            built = self.run_script(d)
            self.assertEqual(built.returncode, 1)
            self.assertIn("0001.md: 「## Reason」の 1 行目が「Documented」「Inferred」「Unknown」で始まっていない", built.stdout)

    def test_reads_older_file_names_and_reports_unnumbered(self):
        with tempfile.TemporaryDirectory() as directory:
            d = pathlib.Path(directory)
            for name in ("0001-Auth_PKCE.md", "0002-認証の変更.md", "DL-0003-retry.md", "DL-4.md"):
                (d / name).write_text(self.log("security", name, ["2025-01-01"], "不明。"), encoding="utf-8")
            (d / "notes.md").write_text("# メモ\n", encoding="utf-8")
            (d / "2025-03-04-retry.md").write_text("# 日付の名前\n", encoding="utf-8")
            built = self.run_script(d)
            index = (d / "README.md").read_text(encoding="utf-8")
            for number, name in ((1, "0001-Auth_PKCE.md"), (2, "0002-認証の変更.md"), (3, "DL-0003-retry.md"), (4, "DL-4.md")):
                self.assertIn(f"[DL-{number}]({name})", index)
            self.assertIn("DL-4.md: ファイル名に DL- を付けない", built.stdout)
            self.assertIn("0001-Auth_PKCE.md: ファイル名は 0001.md か", built.stdout)
            self.assertNotIn("0002-認証の変更.md: ファイル名に DL-", built.stdout)
            self.assertIn("notes.md: ファイル名の先頭に 4 桁の番号がない", built.stdout)
            self.assertIn("2025-03-04-retry.md: ファイル名の先頭に 4 桁の番号がない", built.stdout)
            self.assertNotEqual(built.returncode, 0)

    def test_reports_duplicate_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            d = pathlib.Path(directory)
            for name in ("0001.md", "0001-other.md"):
                (d / name).write_text(self.log("data", name, ["2025-01-01"], "不明。"), encoding="utf-8")
            built = self.run_script(d)
            self.assertEqual(built.returncode, 1)
            self.assertIn("0001-other.md, 0001.md: 番号が重なっている", built.stdout)
            self.assertEqual(self.run_script(d, "--check").returncode, 1)

    def test_check_without_repo_keeps_the_index_name(self):
        with tempfile.TemporaryDirectory() as directory:
            d = pathlib.Path(directory)
            (d / "0001.md").write_text(self.log("data", "x", ["2025-01-01"], "不明。"), encoding="utf-8")
            self.assertEqual(self.run_script(d).returncode, 0)
            checked = subprocess.run([sys.executable, str(self.SCRIPT), str(d), "--check"],
                                     capture_output=True, text=True, check=False)
            self.assertEqual(checked.returncode, 0, checked.stdout)

    def test_reports_malformed_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            d = pathlib.Path(directory)
            (d / "0001.md").write_text("# [demo] 形が崩れた log\n\n**起きたこと**\n- 上限が 5 に\n", encoding="utf-8")
            built = self.run_script(d)
            self.assertEqual(built.returncode, 1)
            self.assertIn("0001.md: フロントマターがない", built.stdout)
            self.assertIn("0001.md: 「## 起きたこと」", built.stdout)
            self.assertIn("0001.md: 「## 理由」", built.stdout)
            checked = self.run_script(d, "--check")
            self.assertEqual(checked.returncode, 1)
            self.assertNotIn("が古い", checked.stdout)


if __name__ == "__main__":
    unittest.main()
