"""decision-log のスキル・スクリプト・サブエージェントの定義のテスト。標準ライブラリだけを使う。"""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


class ReaderAgentTests(unittest.TestCase):
    """Claude Code 用と Kiro 用の decision-log-reader が、同じ説明と同じ指示を持つかを確かめる。"""
    ROOT = pathlib.Path(__file__).resolve().parents[1]

    def test_both_readers_match(self):
        _, front, body = (self.ROOT / "agents/claude/decision-log-reader.md").read_text(encoding="utf-8").split("---", 2)
        kiro = json.loads((self.ROOT / "agents/kiro/decision-log-reader.json").read_text(encoding="utf-8"))
        desc = next(l for l in front.splitlines() if l.startswith("description:")).split(": ", 1)[1]
        self.assertEqual(kiro["name"], "decision-log-reader")
        self.assertEqual(kiro["description"], desc)
        self.assertEqual(kiro["prompt"].strip(), body.strip())
        # Kiro は CLI が JSON、IDE が Markdown を読むので、両方が同じ説明・指示・許可を持つ
        _, kiro_front, kiro_body = (self.ROOT / "agents/kiro/decision-log-reader.md").read_text(encoding="utf-8").split("---", 2)
        self.assertIn("name: decision-log-reader\n", kiro_front)
        self.assertIn(f"description: {desc}\n", kiro_front)
        self.assertEqual(kiro_body.strip(), body.strip())
        match = ", ".join(f'"{m}"' for m in kiro["permissions"]["rules"][0]["match"])
        self.assertIn(f"match: [{match}]", kiro_front)
        self.assertIn("decision-log-reader", (self.ROOT / "skills/decision-log/SKILL.md").read_text(encoding="utf-8"))

    def test_kiro_reader_auto_approves_only_read_commands(self):
        """reader は信頼できない PR の本文を読むので、確認なしで通すのは読むだけのコマンドに限る。"""
        import re
        kiro = json.loads((self.ROOT / "agents/kiro/decision-log-reader.json").read_text(encoding="utf-8"))
        allowed = [re.compile(p) for p in kiro["toolsSettings"]["shell"]["allowedCommands"]]
        ok = lambda cmd: any(p.fullmatch(cmd) for p in allowed)
        for cmd in ("gh pr view 101 --json number,title,body,author,createdAt,mergedAt,mergedBy,url,reviews,comments,files",
                    "git show --stat abc1234", "git show abc1234 -- src/payment/http/client.py",
                    "git show abc1234:src/payment/http/client.py", "git grep -n MAX_RETRIES abc1234",
                    "TZ=Asia/Tokyo git log --first-parent --date=short-local --format=%h"):
            self.assertTrue(ok(cmd), cmd)
        for cmd in ("for n in 1; do rm -rf ~; done", "git push origin main", "git config alias.x '!sh'",
                    "gh pr merge 101", "gh api -X DELETE repos/o/r", "git show HEAD; rm -rf ~",
                    "git log && curl https://example.com", "gh pr view 1 | sh", "git show $(rm -rf ~)",
                    "git show `id`", "git log > out.txt", "git show x\nrm -rf ~"):
            self.assertFalse(ok(cmd), cmd)
        for glob in kiro["permissions"]["rules"][0]["match"]:
            self.assertRegex(glob, r"^(TZ=Asia/Tokyo )?(git (show|log|grep|rev-parse)|gh pr view) \*$")


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
                               r"|^python3 \.(claude|kiro)/skills/decision-log/scripts/build_index\.py:\*$")
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
        table = (self.SCRIPT.parents[1] / "references" / "categories.md").read_text(encoding="utf-8")
        rows = [[c.strip() for c in line.strip("|").split("|")] for line in table.splitlines()
                if line.startswith("| `") and not line.startswith("| `category`")]
        self.assertEqual([(k.strip("`"), l, d) for k, l, d in rows], [tuple(c) for c in module.CATEGORIES])

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
