"""版の仕組みの検査：changes/ の断片、CHANGELOG.md、plugin.json の版が揃っているか（決まりは docs/release.md）。"""
import json
import pathlib
import re
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SH = shutil.which("sh")


def run(*args):
    return subprocess.run(["sh", *args], cwd=ROOT, capture_output=True, text=True)


def top_section():
    return next(l.split()[1] for l in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines() if l.startswith("## "))


@unittest.skipIf(SH is None, "sh がない")
class ReleaseTests(unittest.TestCase):
    def test_fragments_are_valid(self):
        out = run("tools/changelog.sh", "--check")
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_changelog_tools(self):
        out = run("tools/changelog_test.sh")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)

    def test_plugin_version_is_the_latest_release(self):
        # Claude Code は plugin.json の version で更新を見分けるので、いちばん上の版の節と同じにする
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        latest = re.search(r"^## v(\d+\.\d+\.\d+) - \d{4}-\d{2}-\d{2}$", text, re.M)
        self.assertIsNotNone(latest, "CHANGELOG.md に「## vX.Y.Z - YYYY-MM-DD」の節がない")
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["version"], latest.group(1))

    def test_release_notes_of_the_top_section(self):
        top = top_section()
        if top == "Unreleased":
            return
        out = run("tools/release-notes.sh", top)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue(out.stdout.strip())


if __name__ == "__main__":
    unittest.main()
