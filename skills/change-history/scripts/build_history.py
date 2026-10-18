#!/usr/bin/env python3
"""マージされた変更の一覧を、月ごとの Markdown に書き出す（change-history の 1 段目）。

  build_history.py <フォルダー> [--depth 2] [--since YYYY-MM] [--tz Asia/Tokyo]   書き出す
  build_history.py <フォルダー> --check                                          最新か確かめる（古ければ終了コード 1）

月ごとの YYYY-MM.md、索引の README.md、年表の timeline.md を書く。

リポジトリのルートで動かす。手元の git の --first-parent の履歴だけを読み、ネットワークは使わない。
PR の番号はマージコミットの件名（Merge pull request #12）か、squash の件名の末尾（(#12)）から取る。
各月の「## 主な変更」と、年表の各年の要点は、作り直しても残す（人か AI が書く）。標準ライブラリだけを使う。
"""
import argparse
import collections
import os
import pathlib
import re
import subprocess
import sys

MERGE_RE = re.compile(r"^Merge pull request #(\d+) from \S+")
SQUASH_RE = re.compile(r"^(.*?)\s*\(#(\d+)\)\s*$")
# PR を通さないブランチの同期（Merge branch '3.0.x'、Merge remote-tracking branch 'origin/stable'）
SYNC_RE = re.compile(r"^Merge (?:remote-tracking )?branch ")
SYNC = "（ブランチの取り込み）"
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
SUMMARY = "## 主な変更"
EMPTY = "（まだ書いていない）"
COMMIT, FIELD = "\x1e", "\x1f"


def git(*args, tz=None):
    env = dict(os.environ, TZ=tz) if tz else None
    out = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if out.returncode != 0:
        sys.exit(f"git {args[0]} が失敗した: {out.stderr.strip()}")
    return out.stdout


def repo_url():
    """origin から https://github.com/<owner>/<repo> の形を作る。作れなければ None。"""
    out = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True)
    m = re.search(r"(?:github\.com[:/])([^/]+/[^/]+?)(?:\.git)?/?$", out.stdout.strip())
    return f"https://github.com/{m.group(1)}" if m else None


def area(path, depth):
    """変更したファイルの置き場所。depth 段までのフォルダー。ルートのファイルは「（ルート）」。"""
    parts = path.split("/")[:-1][:depth]
    return "/".join(parts) + "/" if parts else "（ルート）"


def changes(tz):
    """--first-parent の各変更を、古い順に返す。マージコミットは 1 つ目の親との差分でファイルを数える。"""
    fmt = FIELD.join(["%H", "%P", "%aN", "%ad", "%s", "%b"])
    out = git("log", "--first-parent", "--reverse", "--diff-merges=first-parent", "--name-only",
              "--date=format-local:%Y-%m-%d", f"--format={COMMIT}{fmt}{FIELD}", tz=tz)
    items = []
    for chunk in out.split(COMMIT)[1:]:
        sha, parents, author, date, subject, body, files = chunk.split(FIELD)
        parents = parents.split()
        m = MERGE_RE.match(subject)
        if m and len(parents) > 1:
            title = next((l.strip() for l in body.splitlines() if l.strip()), subject)
            item = dict(pr=m.group(1), title=title, second=parents[1])
        elif SQUASH_RE.match(subject):
            title, pr = SQUASH_RE.match(subject).groups()
            item = dict(pr=pr, title=title)
        elif SYNC_RE.match(subject):
            item = dict(pr=None, title=f"{SYNC}{subject}")
        else:
            item = dict(pr=None, title=subject)
        item.update(sha=sha, date=date, author=author, files=[f for f in files.splitlines() if f.strip()])
        items.append(item)
    # マージコミットの author はマージした人なので、取り込んだ側の先頭のコミットの author を作成者にする
    seconds = [i["second"] for i in items if "second" in i]
    names = {}
    for start in range(0, len(seconds), 500):
        for line in git("log", "--no-walk", "--format=%H" + FIELD + "%aN", *seconds[start:start + 500]).splitlines():
            sha, name = line.split(FIELD)
            names[sha] = name
    for i in items:
        if "second" in i:
            i["author"] = names.get(i.pop("second"), i["author"])
    return items


def link(item, url):
    if item["pr"]:
        return f"[#{item['pr']}]({url}/pull/{item['pr']})" if url else f"#{item['pr']}"
    short = item["sha"][:7]
    return f"[{short}]({url}/commit/{item['sha']})" if url else short


def summary_of(path):
    """いまのファイルの「## 主な変更」の中身。なければ None。"""
    if not path.exists():
        return None
    m = re.search(rf"^{re.escape(SUMMARY)}\n(.*?)(?=^## |\Z)", path.read_text(encoding="utf-8"), re.S | re.M)
    return m.group(1).strip() if m else None


def month_page(month, items, depth, url, summary):
    """月の変更を日付の順に並べる。各行に、いちばん多く変えた置き場所を添える。"""
    lines, totals = [], collections.Counter()
    for item in items:
        counts = collections.Counter(area(f, depth) for f in item["files"])
        places = sorted(counts, key=lambda a: (-counts[a], a))
        totals.update(places[:1])
        where = f"、{places[0]}" + (f" ほか {len(places) - 1}" if len(places) > 1 else "") if places else ""
        lines.append(f"- {item['date'][5:]} {item['title']}（{link(item, url)} {item['author']}{where}）")
    top = "、".join(f"{a} {n}" for a, n in sorted(totals.items(), key=lambda x: (-x[1], x[0]))[:5])
    out = [f"# {month}", "", f"マージされた変更 {len(items)} 件" + (f"（多い置き場所：{top}）" if top else "") + "。",
           "「## 一覧」は build_history.py が作り直す。", "", SUMMARY, "", summary or EMPTY, "", "## 一覧", ""]
    return "\n".join(out + lines) + "\n"


def index_page(months, url, folder):
    total = sum(len(v) for v in months.values())
    out = ["# 変更の履歴", "", f"マージされた変更 {total} 件を月ごとに並べた。build_history.py が作り直す。年ごとの流れは[年表](timeline.md)。", "",
           "| 月 | 件数 | 主な変更 |", "|---|---|---|"]
    for month in sorted(months, reverse=True):
        written = summary_of(folder / f"{month}.md") not in (None, "", EMPTY)
        out.append(f"| [{month}]({month}.md) | {len(months[month])} | {'あり' if written else 'まだ'} |")
    return "\n".join(out) + "\n"


def year_summaries(path):
    """いまの年表の、年ごとの要点（見出しの下から表の前まで）。"""
    if not path.exists():
        return {}
    found = re.findall(r"^## (\d{4})\n(.*?)(?=^\| 月 \||^## |\Z)", path.read_text(encoding="utf-8"), re.S | re.M)
    return {year: text.strip() for year, text in found}


def first_point(summary):
    """月の主な変更の 1 行目（「- 」を除く）。表に入れるので | を逃がす。"""
    line = next((l[2:].strip() for l in (summary or "").splitlines() if l.startswith("- ")), None)
    return line.replace("|", "\\|") if line else None


def timeline_page(months, folder):
    """年ごとに、要点（人か AI が書く）と、月ごとの主な変更の 1 行目の表を並べる。新しい年が上。"""
    kept = year_summaries(folder / "timeline.md")
    out = ["# 年表", "", "年ごとの要点の下に、各月の主な変更の 1 行目を並べた。表は build_history.py が作り直す。"]
    for year in sorted({m[:4] for m in months}, reverse=True):
        out += ["", f"## {year}", "", kept.get(year) or EMPTY, "", "| 月 | 件数 | 主な変更 |", "|---|---|---|"]
        for month in sorted((m for m in months if m.startswith(year)), reverse=True):
            point = first_point(summary_of(folder / f"{month}.md")) or "まだ"
            out.append(f"| [{int(month[5:])} 月]({month}.md) | {len(months[month])} | {point} |")
    return "\n".join(out) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder", type=pathlib.Path)
    p.add_argument("--depth", type=int, default=2, help="置き場所として数えるフォルダーの段数（既定 2）")
    p.add_argument("--since", help="この月（YYYY-MM）から書く")
    p.add_argument("--tz", default="Asia/Tokyo", help="日付の時間帯（既定 Asia/Tokyo）")
    p.add_argument("--check", action="store_true", help="書かずに、最新かを確かめる")
    args = p.parse_args()
    if args.since and not MONTH_RE.match(args.since):
        p.error("--since は YYYY-MM で書く")
    url = repo_url()
    months = collections.defaultdict(list)
    for item in changes(args.tz):
        if not args.since or item["date"][:7] >= args.since:
            months[item["date"][:7]].append(item)
    pages = {f"{m}.md": month_page(m, items, args.depth, url, summary_of(args.folder / f"{m}.md"))
             for m, items in months.items()}
    pages["README.md"] = index_page(months, url, args.folder)
    pages["timeline.md"] = timeline_page(months, args.folder)
    stale = [name for name, text in sorted(pages.items())
             if not (args.folder / name).exists() or (args.folder / name).read_text(encoding="utf-8") != text]
    if args.check:
        for name in stale:
            print(f"{args.folder / name} が古い")
        print(f"{len(pages) - 2} か月分は最新" if not stale else f"build_history.py {args.folder} で作り直す")
        return 1 if stale else 0
    args.folder.mkdir(parents=True, exist_ok=True)
    for name in stale:
        (args.folder / name).write_text(pages[name], encoding="utf-8")
    total = sum(len(v) for v in months.values())
    print(f"{args.folder}：{len(months)} か月、{total} 件（書き換え {len(stale)} ファイル）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
