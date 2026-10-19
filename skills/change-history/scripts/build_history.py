#!/usr/bin/env python3
"""マージされた変更の一覧を、月ごとの Markdown に書き出す（change-history の 1 段目）。

  build_history.py <フォルダー> [--branch develop --branch main] [--depth 2] [--since YYYY-MM] [--tz Asia/Tokyo]   書き出す
  build_history.py <フォルダー> --check                                                                         最新か確かめる（古ければ終了コード 1）

月ごとの YYYY-MM.md と、年表を兼ねた索引の README.md を書く。日付は YYYY-MM-DD、月は YYYY-MM で書く。
以前の timeline.md があれば、年ごとの要点を README.md に移して消す。

リポジトリのルートで動かす。手元の git の --first-parent の履歴だけを読み、ネットワークは使わない。
開発の本流と本番の適用先のようにブランチが分かれていても取りこぼさないよう、--branch を言わなければ
長く続くブランチ（main・master・develop・development・dev・production）を全部読む。手元のものは古いことがあるので、
origin/ にあればそちらを読む。
どのブランチにも入ったコミットは 1 つにまとめ、ブランチ間のマージ（develop から main へのリリースなど）には印を付ける。
PR の番号はマージコミットの件名（Merge pull request #12）か、squash の件名の末尾（(#12)）から取る。
各月の「## 主な変更」と、README.md の各年の要点は、作り直しても残す（人か AI が書く）。標準ライブラリだけを使う。
人の名前（git の author）は書き出さない。
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
# 版を上げるだけの定型のリリース（Release v1.2.0、Bump version to 1.2.0、chore(release): 1.2.0、v1.2.0）
RELEASE_RE = re.compile(r"^(?:chore\(release\)|(?:chore:\s*)?(?:release|prepare release|bump version|version)\b).*?\bv?\d+\.\d+"
                        r"|^v?\d+\.\d+(?:\.\d+)*$", re.I)
RELEASE = "（リリース）"
# 読んだブランチどうしのマージ。中身は元のブランチの一覧に 1 件ずつ出る
BETWEEN = "（{} から取り込み）"
LONG_LIVED = ("main", "master", "develop", "development", "dev", "production")
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


def has_ref(ref):
    return subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], capture_output=True).returncode == 0


def long_lived():
    """長く続くブランチの (名前, ref)。origin/ にあればそれを、なければ手元のものを使う。どれもなければ HEAD。"""
    found = []
    for name in LONG_LIVED:
        ref = next((r for r in (f"refs/remotes/origin/{name}", f"refs/heads/{name}") if has_ref(r)), None)
        if ref:
            found.append((name, ref))
    return found or [("HEAD", "HEAD")]


def first_parent(ref, tz):
    """ref の --first-parent の各コミットを、古い順に返す。"""
    fmt = FIELD.join(["%H", "%P", "%ad", "%s", "%b"])
    out = git("log", "--first-parent", "--reverse", "--diff-merges=first-parent", "--name-only",
              "--date=format-local:%Y-%m-%d", f"--format={COMMIT}{fmt}{FIELD}", ref, "--", tz=tz)
    return [chunk.split(FIELD) for chunk in out.split(COMMIT)[1:]]


def changes(tz, branches):
    """各ブランチの --first-parent の変更を、古い順に返す。マージコミットは 1 つ目の親との差分でファイルを数える。
    どのブランチにも入ったコミットは 1 つにし、入ったブランチを並べる。"""
    logs = {name: first_parent(ref, tz) for name, ref in branches}
    shas = {name: {c[0] for c in log} for name, log in logs.items()}
    seen, items = {}, []
    for name, log in logs.items():
        for sha, parents, date, subject, body, files in log:
            if sha in seen:
                seen[sha]["branches"].append(name)
                continue
            item = parse(subject, body, parents.split(), name, shas)
            item.update(sha=sha, date=date, branches=[name], files=[f for f in files.splitlines() if f.strip()])
            seen[sha] = item
            items.append(item)
    return sorted(items, key=lambda i: i["date"])


def parse(subject, body, parents, branch, shas):
    """件名と本文から PR の番号とタイトルを取り、印を付ける。"""
    m = MERGE_RE.match(subject)
    if m and len(parents) > 1:
        item = dict(pr=m.group(1), title=next((l.strip() for l in body.splitlines() if l.strip()), subject))
    elif SQUASH_RE.match(subject):
        title, pr = SQUASH_RE.match(subject).groups()
        item = dict(pr=pr, title=title)
    elif SYNC_RE.match(subject):
        item = dict(pr=None, title=f"{SYNC}{subject}")
    else:
        item = dict(pr=None, title=subject)
    # 2 つ目の親がほかに読んだブランチの本流にあれば、ブランチ間のマージ
    source = next((n for n in shas if n != branch and len(parents) > 1 and parents[1] in shas[n]), None)
    if source:
        item["title"] = BETWEEN.format(source) + item["title"].removeprefix(SYNC)
    elif RELEASE_RE.match(item["title"]):
        item["title"] = RELEASE + item["title"]
    return item


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


def month_page(month, items, depth, url, summary, many):
    """月の変更を日付の順に並べる。各行に、いちばん多く変えた置き場所を添える。"""
    lines, totals = [], collections.Counter()
    for item in items:
        counts = collections.Counter(area(f, depth) for f in item["files"])
        places = sorted(counts, key=lambda a: (-counts[a], a))
        totals.update(places[:1])
        where = f"、{places[0]}" + (f" ほか {len(places) - 1}" if len(places) > 1 else "") if places else ""
        into = f"、{'・'.join(item['branches'])} へ" if many else ""
        lines.append(f"- {item['date']} {item['title']}（{link(item, url)}{where}{into}）")
    top = "、".join(f"{a} {n}" for a, n in sorted(totals.items(), key=lambda x: (-x[1], x[0]))[:5])
    out = [f"# {month}", "", f"マージされた変更 {len(items)} 件" + (f"（多い置き場所：{top}）" if top else "") + "。",
           "「## 一覧」は build_history.py が作り直す。", "", SUMMARY, "", summary or EMPTY, "", "## 一覧", ""]
    return "\n".join(out + lines) + "\n"


def read_from(branches):
    """main（origin/main）、develop（origin/develop）の形。"""
    shown = [(name, ref.removeprefix("refs/remotes/").removeprefix("refs/heads/")) for name, ref in branches]
    return "、".join(f"{name}（{ref}）" if ref != name else name for name, ref in shown)


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


def readme_page(months, folder, branches):
    """年表を兼ねた索引。年ごとに、要点（人か AI が書く）と、月ごとの主な変更の 1 行目の表を並べる。新しい年が上。"""
    # 以前の timeline.md に書いた要点も拾う。README.md に書いたものが先
    kept = {**year_summaries(folder / "timeline.md"),
            **{y: t for y, t in year_summaries(folder / "README.md").items() if t != EMPTY}}
    total = sum(len(v) for v in months.values())
    out = ["# 変更の履歴", "",
           f"マージされた変更 {total} 件を月ごとのファイルに並べ、年ごとに要点と各月の主な変更の 1 行目をまとめた。表は build_history.py が作り直す。", "",
           f"読んだブランチ：{read_from(branches)}。それぞれの --first-parent。"]
    for year in sorted({m[:4] for m in months}, reverse=True):
        out += ["", f"## {year}", "", kept.get(year) or EMPTY, "", "| 月 | 件数 | 主な変更 |", "|---|---|---|"]
        for month in sorted((m for m in months if m.startswith(year)), reverse=True):
            point = first_point(summary_of(folder / f"{month}.md")) or "まだ"
            out.append(f"| [{month}]({month}.md) | {len(months[month])} | {point} |")
    return "\n".join(out) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder", type=pathlib.Path)
    p.add_argument("--branch", action="append", help="読むブランチ（何度でも。既定は長く続くブランチを全部）")
    p.add_argument("--depth", type=int, default=2, help="置き場所として数えるフォルダーの段数（既定 2）")
    p.add_argument("--since", help="この月（YYYY-MM）から書く")
    p.add_argument("--tz", default="Asia/Tokyo", help="日付の時間帯（既定 Asia/Tokyo）")
    p.add_argument("--check", action="store_true", help="書かずに、最新かを確かめる")
    args = p.parse_args()
    if args.since and not MONTH_RE.match(args.since):
        p.error("--since は YYYY-MM で書く")
    for name in args.branch or []:
        if not has_ref(name):
            p.error(f"ブランチ {name} が見つからない")
    branches = [(name, name) for name in args.branch] if args.branch else long_lived()
    url = repo_url()
    months = collections.defaultdict(list)
    for item in changes(args.tz, branches):
        if not args.since or item["date"][:7] >= args.since:
            months[item["date"][:7]].append(item)
    pages = {f"{m}.md": month_page(m, items, args.depth, url, summary_of(args.folder / f"{m}.md"), len(branches) > 1)
             for m, items in months.items()}
    pages["README.md"] = readme_page(months, args.folder, branches)
    old = args.folder / "timeline.md"
    stale = [name for name, text in sorted(pages.items())
             if not (args.folder / name).exists() or (args.folder / name).read_text(encoding="utf-8") != text]
    if args.check:
        for name in stale:
            print(f"{args.folder / name} が古い")
        if old.exists():
            print(f"{old} は README.md に移った")
        bad = stale or old.exists()
        print(f"{len(pages) - 1} か月分は最新" if not bad else f"build_history.py {args.folder} で作り直す")
        return 1 if bad else 0
    args.folder.mkdir(parents=True, exist_ok=True)
    for name in stale:
        (args.folder / name).write_text(pages[name], encoding="utf-8")
    if old.exists():
        old.unlink()  # 年ごとの要点は README.md に移した
    total = sum(len(v) for v in months.values())
    print(f"{args.folder}：{len(months)} か月、{total} 件（書き換え {len(stale)} ファイル）。読んだブランチ：{read_from(branches)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
