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
                    if rule.get("effect") != "allow" or rule.get("match") == ["gh api repos/*"]:
                        continue
                    for glob in rule.get("match", []):
                        # 「git *」「gh *」のようにコマンド全体を許す形にしない。サブコマンドまで書く
                        self.assertRegex(glob, r"^(\S+=\S+ )?\S+ [a-z-]+( [a-z-]+)? \*$")


    def test_kiro_v3_rules_allow_rest_reads_but_deny_writes(self):
        """Kiro 3.x の照合をまねる：* は何にでも当たり、deny が allow に勝つ。`gh api repos/*` を許すなら、書き込みの指定を deny で止める。"""
        def allowed(cmd, rules):
            globs = lambda effect: [re.compile(re.escape(g).replace(r"\*", ".*")) for r in rules if r.get("effect") == effect
                                    for g in r.get("match", [])]
            return any(p.fullmatch(cmd) for p in globs("allow")) and not any(p.fullmatch(cmd) for p in globs("deny"))
        for path in KIRO_AGENTS:
            rules = json.loads(path.read_text(encoding="utf-8")).get("permissions", {}).get("rules", [])
            if not any(r.get("match") == ["gh api repos/*"] for r in rules):
                continue
            with self.subTest(agent=path.stem):
                for cmd in ("gh api repos/o/r/pulls/45", "gh api repos/o/r/pulls/45/comments", "gh api repos/o/my-flow/issues/42/comments"):
                    self.assertTrue(allowed(cmd, rules), cmd)
                for cmd in [c for c in DANGEROUS if c.startswith("gh api")] + [
                        "gh api repos/o/r/issues --method POST", "gh api repos/o/r/issues -F title=x",
                        "gh api repos/o/r/issues --raw-field title=x", "gh api repos/o/r/issues --input body.json"]:
                    self.assertFalse(allowed(cmd, rules), cmd)


    def test_change_history_uses_the_decision_log_categories(self):
        # change-history の主な変更は decision-log と同じ分類で書く。表を変えたら両方を直す
        table = (ROOT / "skills/decision-log/references/format.md").read_text(encoding="utf-8")
        want = [c for c in re.findall(r"^\| `([a-z]+)` \|", table, re.M) if c != "category"]
        skill = (ROOT / "skills/change-history/SKILL.md").read_text(encoding="utf-8")
        line = next(l for l in skill.splitlines() if "分類は decision-log と同じ" in l)
        got = re.findall(r"`([a-z]+)`", line.split("分類は decision-log と同じ", 1)[1].split("で、", 1)[0])
        self.assertEqual(len(want), 11)
        self.assertEqual(got, want)
        script = (ROOT / "skills/change-history/scripts/build_history.py").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r'"([a-z]+)"', re.search(r"CATEGORIES = \((.*?)\)", script, re.S).group(1)), want)
        # 分類の見出しの直下に入れる説明は、format.md の表の「見出し：中身」と同じ
        rows = dict((c, f"{h}：{d}") for c, h, d in re.findall(r"^\| `([a-z]+)` \| (.*?) \| (.*?) \|$", table, re.M) if c != "category")
        got = dict(re.findall(r'^    "([a-z]+)": "(.*?)",$', re.search(r"DESCRIPTIONS = \{(.*?)\n\}", script, re.S).group(1), re.M))
        self.assertEqual(got, rows)

    def test_both_skills_skip_the_same_routine_releases(self):
        # 版を上げるだけのリリースは、change-history の主な変更にも decision-log の候補にも入れない
        script = (ROOT / "skills/change-history/scripts/build_history.py").read_text(encoding="utf-8")
        forms = re.search(r"# 版を上げるだけの定型のリリース（(.*?)）", script).group(1).split("、")
        for path in ("skills/change-history/SKILL.md", "skills/decision-log/SKILL.md", "agents/claude/decision-log-planner.md"):
            text = (ROOT / path).read_text(encoding="utf-8")
            line = next(l for l in text.splitlines() if "定型のリリース" in l and "`Release v1.2.0`" in l)
            self.assertEqual(re.findall(r"`([^`]+)`", line.split("定型のリリース", 1)[1])[:4], forms, path)

if __name__ == "__main__":
    unittest.main()
