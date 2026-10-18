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

    def test_refuses_bad_arguments(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertNotEqual(install("cursor", d).returncode, 0)
            self.assertNotEqual(install("kiro", str(pathlib.Path(d) / "missing")).returncode, 0)
        self.assertNotEqual(install("kiro", str(ROOT)).returncode, 0)
        self.assertNotEqual(install().returncode, 0)


if __name__ == "__main__":
    unittest.main()
