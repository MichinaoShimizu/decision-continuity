"""文書とフロントマターの検査：リンクの先があるか、Claude Code と Kiro が読めるか。"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts)
FRONTED = [ROOT / "skills/decision-log/SKILL.md", ROOT / "agents/claude/decision-log-reader.md",
           ROOT / "agents/kiro/decision-log-reader.md"]


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
        skill = ROOT / "skills/decision-log/SKILL.md"
        self.assertIn("\nname: decision-log\n", skill.read_text(encoding="utf-8"))
        self.assertLessEqual(len(skill.read_bytes()), 7000, "SKILL.md は 7,000 バイトまで。詳細は references/ に移す")

    def test_kiro_json_is_valid(self):
        data = json.loads((ROOT / "agents/kiro/decision-log-reader.json").read_text(encoding="utf-8"))
        for key in ("name", "description", "prompt", "tools"):
            self.assertIn(key, data)


if __name__ == "__main__":
    unittest.main()
