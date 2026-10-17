"""文書とフロントマターの検査：リンクの先があるか、Claude Code と Kiro が読めるか。"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts)
SKILLS = sorted((ROOT / "skills").glob("*/SKILL.md"))
CLAUDE_AGENTS = sorted((ROOT / "agents" / "claude").glob("*.md"))
KIRO_AGENTS = sorted((ROOT / "agents" / "kiro").glob("*.json"))
FRONTED = SKILLS + CLAUDE_AGENTS + sorted((ROOT / "agents" / "kiro").glob("*.md"))
# どのエージェントでも、確認なしで通してはいけないコマンド
DANGEROUS = ("for n in 1; do rm -rf ~; done", "git push origin main", "git config alias.x '!sh'",
             "gh pr merge 101", "gh api -X DELETE repos/o/r", "gh api repos/o/r -X DELETE", "gh api repos/o/r -XPOST", "gh api repos/o/r -f title=x", "gh api graphql", "git show HEAD; rm -rf ~",
             "git log && curl https://example.com", "gh pr view 1 | sh", "git show $(rm -rf ~)",
             "git show `id`", "git log > out.txt", "git show x\nrm -rf ~", "rm -rf ~", "curl https://example.com")


def split_front(path):
    _, front, body = path.read_text(encoding="utf-8").split("---", 2)
    return front, body


def outside_code(text):
    """コードブロックの外の行だけを返す（例の中の仮のリンクは確かめない）。"""
    lines, fence = [], None
    for line in text.splitlines():
        m = re.match(r"^\s*(`{3,}|~{3,})", line)
        if m:
            if fence is None:
                fence = m.group(1)
            elif m.group(1).startswith(fence[0]) and len(m.group(1)) >= len(fence):
                fence = None
            continue
        if fence is None:
            lines.append(re.sub(r"`[^`]*`", "", line))
    return lines


def anchors(path):
    """GitHub が見出しから作るアンカー。"""
    found = set()
    for line in outside_code(path.read_text(encoding="utf-8")):
        m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if m:
            found.add(re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", m.group(1).lower())))
    return found


class LinkTests(unittest.TestCase):
    def test_relative_links_and_anchors_exist(self):
        for doc in DOCS:
            for line in outside_code(doc.read_text(encoding="utf-8")):
                for target in re.findall(r"\]\(([^)\s]+)\)", line):
                    if re.match(r"^[a-z]+:", target):
                        continue
                    path, _, anchor = target.partition("#")
                    dest = (doc.parent / path).resolve() if path else doc
                    with self.subTest(doc=str(doc.relative_to(ROOT)), link=target):
                        self.assertTrue(dest.exists(), f"{target} の先がない")
                        if anchor:
                            self.assertIn(anchor, anchors(dest), f"{target} の見出しがない")


class FrontMatterTests(unittest.TestCase):
    def test_front_matter_is_yaml_with_name_and_description(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML がない（CI では入れる）")
        for path in FRONTED:
            with self.subTest(path=str(path.relative_to(ROOT))):
                text = path.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"))
                data = yaml.safe_load(text.split("---", 2)[1])
                self.assertIsInstance(data, dict)
                self.assertTrue(data.get("name") and data.get("description"))

    def test_skill_name_matches_folder_and_stays_small(self):
        self.assertTrue(SKILLS)
        for skill in SKILLS:
            with self.subTest(skill=skill.parent.name):
                self.assertIn(f"\nname: {skill.parent.name}\n", skill.read_text(encoding="utf-8"))
                self.assertLessEqual(len(skill.read_bytes()), 7000, "SKILL.md は 7,000 バイトまで。詳細は references/ に移す")


class PluginTests(unittest.TestCase):
    """Claude Code のプラグインとマーケットプレイスの定義が、リポジトリの中身と合っているか。"""

    def test_plugin_lists_every_claude_agent_and_no_kiro_file(self):
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        listed = sorted((ROOT / p).resolve() for p in plugin["agents"])
        # agents を書かないと agents/ 全体（kiro/ の .md も）を読みにいくので、Claude Code 用だけを並べる
        self.assertEqual(listed, sorted(p.resolve() for p in CLAUDE_AGENTS))
        self.assertRegex(plugin["version"], r"^\d+\.\d+\.\d+$")

    def test_marketplace_points_at_this_repository(self):
        market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual([(p["name"], p["source"]) for p in market["plugins"]], [(plugin["name"], ".")])


class AgentTests(unittest.TestCase):
    """Claude Code 用の定義ごとに、Kiro 用の JSON（CLI が読む）と Markdown（IDE が読む）が同じ中身で揃っているか。"""

    def test_every_claude_agent_has_matching_kiro_definitions(self):
        self.assertTrue(CLAUDE_AGENTS)
        for claude in CLAUDE_AGENTS:
            name = claude.stem
            with self.subTest(agent=name):
                front, body = split_front(claude)
                self.assertIn(f"name: {name}\n", front)
                desc = next(l for l in front.splitlines() if l.startswith("description:")).split(": ", 1)[1]
                kiro_json, kiro_md = ROOT / "agents/kiro" / f"{name}.json", ROOT / "agents/kiro" / f"{name}.md"
                self.assertTrue(kiro_json.exists() and kiro_md.exists(), "agents/kiro/ に .json と .md の両方を置く")
                data = json.loads(kiro_json.read_text(encoding="utf-8"))
                self.assertEqual((data["name"], data["description"], data["prompt"].strip()), (name, desc, body.strip()))
                kiro_front, kiro_body = split_front(kiro_md)
                self.assertIn(f"name: {name}\n", kiro_front)
                self.assertIn(f"description: {desc}\n", kiro_front)
                self.assertEqual(kiro_body.strip(), body.strip())
                match = ", ".join(f'"{m}"' for m in data["permissions"]["rules"][0]["match"])
                self.assertIn(f"match: [{match}]", kiro_front)

    def test_kiro_agents_never_auto_approve_dangerous_commands(self):
        self.assertTrue(KIRO_AGENTS)
        for path in KIRO_AGENTS:
            data = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(agent=path.stem):
                allowed = [re.compile(p) for p in data.get("toolsSettings", {}).get("shell", {}).get("allowedCommands", [])]
                for cmd in DANGEROUS:
                    self.assertFalse(any(p.fullmatch(cmd) for p in allowed), cmd)
                for rule in data.get("permissions", {}).get("rules", []):
                    for glob in rule.get("match", []):
                        # 「git *」「gh *」のようにコマンド全体を許す形にしない。サブコマンドまで書く
                        self.assertRegex(glob, r"^(\S+=\S+ )?\S+ [a-z-]+( [a-z-]+)? \*$")


if __name__ == "__main__":
    unittest.main()
