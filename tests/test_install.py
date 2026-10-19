"""tools/install.sh の検査：スキルとサブエージェントを、決まった場所に入れ、入れ直すと更新するか。"""
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "install.sh"


def install(*args):
    return subprocess.run(["sh", str(SCRIPT), *args], capture_output=True, text=True, check=False)


class InstallTests(unittest.TestCase):

    def test_kiro_gets_the_skill_and_both_agent_formats(self):
        with tempfile.TemporaryDirectory() as d:
            result = install("kiro", d)
            self.assertEqual(result.returncode, 0, result.stderr)
            dest = pathlib.Path(d) / ".kiro"
            self.assertTrue((dest / "skills/decision-log/SKILL.md").exists())
            self.assertTrue((dest / "skills/decision-log/scripts/build_index.py").exists())
            self.assertTrue((dest / "skills/change-history/scripts/build_history.py").exists())
            agents = sorted(p.name for p in (dest / "agents").iterdir())
            want = sorted(p.name for p in (ROOT / "agents/kiro").iterdir())
            self.assertEqual(agents, want)
            self.assertFalse((pathlib.Path(d) / ".claude").exists())

    def test_claude_gets_only_claude_agents(self):
        with tempfile.TemporaryDirectory() as d:
            result = install("claude", d)
            self.assertEqual(result.returncode, 0, result.stderr)
            agents = sorted(p.name for p in (pathlib.Path(d) / ".claude/agents").iterdir())
            self.assertEqual(agents, sorted(p.name for p in (ROOT / "agents/claude").glob("*.md")))

    def test_reinstall_replaces_the_skill(self):
        with tempfile.TemporaryDirectory() as d:
            install("kiro", d)
            stale = pathlib.Path(d) / ".kiro/skills/decision-log/references/old.md"
            stale.write_text("old", encoding="utf-8")
            mine = pathlib.Path(d) / ".kiro/agents/my-agent.json"
            mine.write_text("{}", encoding="utf-8")
            self.assertEqual(install("kiro", d).returncode, 0)
            self.assertFalse(stale.exists())
            self.assertTrue(mine.exists(), "ほかのエージェントは消さない")

    def test_reinstall_drops_this_kits_removed_agents(self):
        # 前の版にあって、いまの版で消したサブエージェントは残さない。書き手も入る
        for tool, ext in (("claude", ".md"), ("kiro", ".json")):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as d:
                install(tool, d)
                agents = pathlib.Path(d) / f".{tool}/agents"
                self.assertTrue((agents / f"change-history-writer{ext}").exists())
                for gone in ("decision-log-old", "change-history-old"):
                    (agents / f"{gone}{ext}").write_text("{}", encoding="utf-8")
                self.assertEqual(install(tool, d).returncode, 0)
                self.assertEqual(sorted(p.name for p in agents.glob("*-old*")), [])

    def test_cdpath_does_not_break_the_paths(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "target").mkdir()
            env = dict(os.environ, CDPATH=f".:{d}")
            result = subprocess.run(["sh", str(SCRIPT), "kiro", "target"], capture_output=True, text=True, cwd=d, env=env, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((pathlib.Path(d) / "target/.kiro/skills/decision-log/SKILL.md").exists())

    def test_refuses_bad_arguments(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertNotEqual(install("cursor", d).returncode, 0)
            self.assertNotEqual(install("kiro", str(pathlib.Path(d) / "missing")).returncode, 0)
        self.assertNotEqual(install("kiro", str(ROOT)).returncode, 0)
        self.assertNotEqual(install().returncode, 0)


if __name__ == "__main__":
    unittest.main()
