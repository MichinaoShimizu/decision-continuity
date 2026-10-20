#!/usr/bin/env python3
"""一覧にした複数のリポジトリの年表を、1 か所（中央のリポジトリ）にまとめて作る（change-history の複数リポジトリ版）。

  build_many.py <一覧> <フォルダー> [--cache .cache/change-history] [--since YYYY-MM] [--until YYYY-MM]   取って、書き出す
  build_many.py <一覧> <フォルダー> --check                                                            最新か確かめる（取らない）

一覧（repos.txt など）は 1 行に 1 つ。owner/repo（GitHub）か、clone できる URL。後ろに --branch・--depth を書ける。
# から後と空の行は読まない。

  pallets/click
  pallets/flask --branch main --branch stable
  https://gitlab.example.com/team/api.git

リポジトリごとに、--cache の下に bare のクローン（--filter=blob:none。ファイルの中身は取らない）を作るか、取り直し、
build_history.py（このファイルと同じフォルダーのもの）を --repo で回して <フォルダー>/<owner>/<repo>/ に月の表と年表を書く。
まとめの <フォルダー>/README.md には、年ごとに、リポジトリごとの年の要点（各リポジトリの README.md から写す）と、
月 × リポジトリの件数の表を書く。件数が空のマスは、そのリポジトリがまだなかった月。
--cache には、中身を git に入れない .gitignore を置く。標準ライブラリだけを使う。
"""
import argparse
import pathlib
import re
import shlex
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_history as bh  # noqa: E402

BUILD = pathlib.Path(__file__).resolve().parent / "build_history.py"
# 置き場所の名前にするので、owner と repo には英数字と . _ - だけを許す（.. などでフォルダーの外に出ない）
NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._-]*$")
# 各リポジトリの年表の、変更のなかった月の行（| 2024-01 | 0 | 変更なし |、| 2024-01〜2024-03 | 0 | 変更なし |）
GAP_RE = re.compile(rf"^\| (\d{{4}}-\d{{2}})(?:〜(\d{{4}}-\d{{2}}))? \| 0 \| {bh.NONE} \|$")
COUNT_RE = re.compile(r"^\| \[(\d{4}-\d{2})\]\(\1\.md\) \| (\d+) \|")
PASSED = ("--branch", "--depth")


def entries(path):
    """一覧の各行を (owner/repo, clone の URL, build_history.py に渡す引数) にする。おかしい行は理由を出して終わる。"""
    found, seen = [], set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        words = shlex.split(line, comments=True)
        if not words:
            continue
        spec, rest = words[0], words[1:]
        if "://" in spec or spec.startswith("git@"):
            url = spec
            parts = re.split(r"[/:]", spec.removesuffix("/").removesuffix(".git"))[-2:]
        else:
            url, parts = f"https://github.com/{spec}.git", spec.split("/")
        if len(parts) != 2 or not all(NAME_RE.match(p) for p in parts):
            sys.exit(f"{path} の {number} 行目：{spec} は owner/repo か clone できる URL で書く")
        key = "/".join(parts)
        if key.lower() in seen:
            sys.exit(f"{path} の {number} 行目：{key} が 2 度ある")
        seen.add(key.lower())
        for i, word in enumerate(rest):
            if word.startswith("--") and word not in PASSED:
                sys.exit(f"{path} の {number} 行目：書けるのは {'・'.join(PASSED)} だけ（{word}）")
            if word in PASSED and i + 1 >= len(rest):
                sys.exit(f"{path} の {number} 行目：{word} の値がない")
        found.append((key, url, rest))
    if not found:
        sys.exit(f"{path} にリポジトリがない")
    return found


def run(*args):
    out = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        sys.exit(f"{' '.join(args[:3])} が失敗した: {out.stderr.strip()}")


def fetch(url, clone):
    """bare のクローンを作るか、取り直す。ブランチは refs/heads/ にそのまま入る（消えたブランチは消す）。"""
    if (clone / "HEAD").exists():
        run("git", "-C", str(clone), "fetch", "-q", "--prune", "--filter=blob:none", "origin", "+refs/heads/*:refs/heads/*")
    else:
        clone.parent.mkdir(parents=True, exist_ok=True)
        run("git", "clone", "-q", "--bare", "--filter=blob:none", url, str(clone))


def timeline(text):
    """各リポジトリの年表から、(月 → 件数, 年 → 要点)。変更のなかった月は 0。"""
    counts = {}
    for line in text.splitlines():
        if m := COUNT_RE.match(line):
            counts[m.group(1)] = int(m.group(2))
        elif m := GAP_RE.match(line):
            counts.update((month, 0) for month in bh.month_range(m.group(1), m.group(2) or m.group(1)))
    return counts, bh.years_in(text)


def overview(folder, keys):
    """まとめの年表。年ごとに、リポジトリごとの年の要点と、月 × リポジトリの件数の表。新しい年が上。"""
    repos = {}
    for key in keys:
        path = folder / key / "README.md"
        if path.exists():
            repos[key] = timeline(path.read_text(encoding="utf-8"))
    months = sorted({m for counts, _ in repos.values() for m in counts})
    every = bh.month_range(months[0], months[-1]) if months else []
    out = ["# 変更の履歴"]
    for year in sorted({m[:4] for m in every}, reverse=True):
        out += ["", f"## {year}"]
        # その年までに始まっていたリポジトリ。最後の変更より後の年も、変更なしとして載せる
        here = [k for k, (counts, _) in repos.items() if counts and min(counts)[:4] <= year]
        for key in here:
            # 各リポジトリの年の要点を写す
            out += ["", f"### [{key}]({key}/README.md)", "", repos[key][1].get(year, bh.NONE)]
        out += ["", "| 月 | " + " | ".join(here) + " |", "|---|" + "---|" * len(here)]
        # どこにも変更のなかった月が続けば、マスが同じあいだ 1 行にまとめる（新しい順）
        rows = []
        for month in sorted((m for m in every if m.startswith(year)), reverse=True):
            cells = [cell(repos[k][0], k, month) for k in here]
            quiet = not any(c.startswith("[") for c in cells)
            if quiet and rows and rows[-1][2] and rows[-1][1] == cells:
                rows[-1][0].append(month)
            else:
                rows.append(([month], cells, quiet))
        for span, cells, _ in rows:
            out.append(f"| {span[0] if len(span) == 1 else f'{span[-1]}〜{span[0]}'} | " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


def cell(counts, key, month):
    """その月の件数。変更があれば月の表へのリンク、なければ 0、リポジトリがまだなかった月（最初の変更より前）は空。"""
    if month < min(counts):
        return ""
    return f"[{counts[month]}]({key}/{month}.md)" if counts.get(month) else "0"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("repos", type=pathlib.Path, help="リポジトリの一覧（repos.txt など）")
    p.add_argument("folder", type=pathlib.Path)
    p.add_argument("--cache", type=pathlib.Path, default=pathlib.Path(".cache/change-history"),
                   help="クローンを置く場所（既定 .cache/change-history。中身は git に入れない）")
    p.add_argument("--since", help="この月（YYYY-MM）から書く")
    p.add_argument("--until", help="この月（YYYY-MM）まで書く")
    p.add_argument("--no-github", action="store_true", help="GitHub に問い合わせない（Author はメールから取る）")
    p.add_argument("--no-fetch", action="store_true", help="取り直さず、いまのクローンを読む")
    p.add_argument("--check", action="store_true", help="取らず、書かずに、最新かを確かめる")
    args = p.parse_args()
    for flag, value in (("--since", args.since), ("--until", args.until)):
        if value and not bh.MONTH_RE.match(value):
            p.error(f"{flag} は YYYY-MM で書く")
    repos = entries(args.repos)
    if not args.check:
        args.cache.mkdir(parents=True, exist_ok=True)
        (args.cache / ".gitignore").write_text("*\n", encoding="utf-8")
    bad = False
    for key, url, extra in repos:
        clone = args.cache / key
        if not args.check and not args.no_fetch:
            fetch(url, clone)
        if not (clone / "HEAD").exists():
            print(f"== {key}：{clone} がまだない（--check と --no-fetch の前に、一度取る）")
            bad = True
            continue
        flags = [*extra, *(["--since", args.since] if args.since else []), *(["--until", args.until] if args.until else []),
                 *(["--no-github"] if args.no_github else []), *(["--check"] if args.check else [])]
        out = subprocess.run([sys.executable, str(BUILD), str(args.folder / key), "--repo", str(clone), *flags],
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
        # 書き手に渡すもの（置き場所・--repo・--branch）を添える
        print(f"== {key}（置き場所 {args.folder / key}、--repo {clone}{''.join(' ' + w for w in extra)}）")
        print((out.stdout + out.stderr).rstrip())
        bad = bad or out.returncode != 0
    readme = args.folder / "README.md"
    page = overview(args.folder, [key for key, _, _ in repos])
    if args.check:
        if not readme.exists() or readme.read_text(encoding="utf-8") != page:
            print(f"{readme} が古い。build_many.py {args.repos} {args.folder} で作り直す")
            bad = True
    elif not readme.exists() or readme.read_text(encoding="utf-8") != page:
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text(page, encoding="utf-8")
    print(f"{readme}：{len(repos)} リポジトリ")
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # 読む側が途中でやめた（head など）。黙って終える
        sys.stderr.close()
        sys.exit(0)
