#!/usr/bin/env python3
"""マージされた変更の一覧を、月ごとの Markdown に書き出す（change-history の 1 段目）。

  build_history.py <フォルダー> [--branch develop --branch main] [--depth 2] [--since YYYY-MM] [--until YYYY-MM]   書き出す
  build_history.py <フォルダー> --check                                                                         最新か確かめる（古ければ終了コード 1）
  build_history.py <フォルダー> --list YYYY-MM                                                                  その月の全変更を出す（書かない）

月ごとの YYYY-MM.md（主な変更の表）と、年表を兼ねた索引の README.md を書く。日付は YYYY-MM-DD、月は YYYY-MM で書く。
全変更の一覧はファイルに書かず、--list で出す（主な変更を選ぶ材料）。マージコミットの下には、取り込んだ側の
コミット（PR の中のコミットや、release/1.2 などの読んでいないブランチでマージされた PR）を並べる。
以前の timeline.md があれば、年ごとの要点を README.md に移して消す。

リポジトリのルートで動かす。手元の git の --first-parent の履歴を読む。ネットワークに出るのは、PR の作成者を取る gh api だけ
（--no-github で止める）。
開発の本流と本番の適用先のようにブランチが分かれていても取りこぼさないよう、--branch を言わなければ
長く続くブランチ（main・master・develop・development・dev・production）を全部読む。手元のものは古いことがあるので、
origin/ にあればそちらを読む。
どのブランチにも入ったコミットは 1 つにまとめ、ブランチ間のマージ（develop から main へのリリースなど）には印を付ける。
PR の番号はマージコミットの件名（Merge pull request #12）か、squash の件名の末尾（(#12)）から取る。
各月の「## 主な変更」と、README.md の各年の要点・各月の要約は、作り直しても残す（人か AI が書く）。月の主な変更と年の要点の分類は
機能改善・運用改善・バグ対応の 3 つ。分類の見出しの直下には
分類の説明を入れる。主な変更の表の日付と Author は、PR の列の変更から埋め直す（前の形の「- 概要（#12）」の行は表に移す）。
決まった形でなければ、どこが崩れているかを出し、終了コード 1 を返す。標準ライブラリだけを使う。
人はアカウント名（@login）で、Author の列にだけ書く。gh が使えれば、PR の作成者を GitHub から取る（gh api の GET だけ）。
取れない変更は、noreply のメール（.mailmap を通す）から取る。名前（git の author 名）は書き出さない。
"""
import argparse
import collections
import json
import os
import pathlib
import re
import subprocess
import sys

# 番号のないもの（Merge pull request from GHSA-…：セキュリティ修正のマージ）も、本文の 1 行目をタイトルにする
MERGE_RE = re.compile(r"^Merge pull request (?:#(\d+) )?from \S+")
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
# 月の主な変更と年表（README.md の年の要点）の分類。変更の性質で 3 つに分け、見出しの直下に説明を入れる
DESCRIPTIONS = {
    "機能改善": "使う人に見える機能の追加と変更",
    "運用改善": "開発・リリース・運用の進め方の改善（CI、デプロイ、監視、手順、文書など）",
    "バグ対応": "不具合の修正と、その再発を防ぐ変更",
}
HEADER, RULE = "| 日付 | 概要 | PR | Author |", "|---|---|---|---|"
NO_POINT = "まだ"
ROW_RE = re.compile(r"^\| \[(\d{4}-\d{2})\]\(\1\.md\) \| \d+ \| (.*) \|$")
# GitHub の noreply のメール（12345+alice@users.noreply.github.com）からアカウント名を取る。取れなければ UNKNOWN
NOREPLY_RE = re.compile(r"^(?:\d+\+)?([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\[bot\])?)@users\.noreply\.github\.com$", re.I)
UNKNOWN = "—"
CELL_RE = re.compile(r"(?<!\\)\|")
OLD_LINE_RE = re.compile(r"^- (.*)（([^（）]*)）$")
NOTHING_RE = re.compile(r"^- 目立った変更なし（(?:ブランチの取り込み|リリース|ブランチの取り込みとリリース)のみ）$")
# 月の行の末尾は PR かコミット（リンクでも、なくても）、年の行の末尾は月か期間
KEY_RE = re.compile(r"#(\d+)|\b([0-9a-f]{7,40})\b")
PERIOD_RE = re.compile(r"（\d{4}-\d{2}(?:〜\d{4}-\d{2})?）$")
# 略した日付（5 月、05-02）。YYYY-MM と YYYY-MM-DD には当たらない
SHORT_DATE_RE = re.compile(r"\d+\s*月|(?<![\d-])\d{1,2}-\d{1,2}(?![\d-])")
COMMIT, FIELD = "\x1e", "\x1f"
# GitHub から取った、PR の番号ごとの作成者（@login）。取れた PR は、メールより先にこれを使う
PR_AUTHORS = {}
# GitHub から取った、PR を入れたコミット（merge_commit_sha）から (番号, タイトル)。件名に番号のない変更
# （Rebase and merge など）を PR に結びつける
PR_SHAS = {}


def git(*args, tz=None, stdin=None):
    env = dict(os.environ, TZ=tz) if tz else None
    out = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                         input=stdin)
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
    # %aE は .mailmap を通したメール、%cd はブランチに入った日（rebase や cherry-pick でも、書いた日ではなく入った日）
    fmt = FIELD.join(["%H", "%P", "%aE", "%cd", "%s", "%b"])
    out = git("log", "--first-parent", "--reverse", "--diff-merges=first-parent", "--name-only",
              "--date=format-local:%Y-%m-%d", f"--format={COMMIT}{fmt}{FIELD}", ref, "--", tz=tz)
    return [chunk.split(FIELD) for chunk in out.split(COMMIT)[1:]]


def cache_file(url):
    """GitHub から取った PR を覚えておく場所。.git の中なので、リポジトリには入らない。"""
    out = subprocess.run(["git", "rev-parse", "--git-common-dir"], capture_output=True, text=True)
    return pathlib.Path(out.stdout.strip()) / "decision-continuity-prs.json" if out.returncode == 0 and url else None


def github_prs(url, asked, online):
    """閉じた PR の 番号 → [作成者, PR を入れたコミット, タイトル]。覚えておいた分に、GitHub の REST API（gh api）で
    更新の新しい順に 100 件ずつ足し、全部を覚えている PR のページが来たら止める（2 回目からは新しい分だけ取る）。
    --paginate は次のページを repositories/<ID>/… の形で引き、通さない中継があるので使わず、ページを数える。
    途中で失敗しても、取れた分は使う。online でなければ、覚えておいた分だけを返す。gh がないか origin が GitHub で
    ないときは、--github と言われたときだけ理由を出す。gh が失敗したときはいつも出す。"""
    path = cache_file(url)
    try:
        saved = json.loads(path.read_text(encoding="utf-8")) if path and path.exists() else {}
    except ValueError:
        saved = {}
    known = saved.get("prs", {}) if saved.get("repo") == url else {}
    if not online or not url:
        if asked and not url:
            print("--github：origin が GitHub でないので、PR の作成者は取らない", file=sys.stderr)
        return known
    found, page = dict(known), 1
    jq = '.[] | [(.number | tostring), .user.login, (if .merged_at then .merge_commit_sha else "" end), .title] | @tsv'
    while True:
        api = f"repos/{url.removeprefix('https://github.com/')}/pulls?state=closed&sort=updated&direction=desc&per_page=100&page={page}"
        try:
            out = subprocess.run(["gh", "api", api, "--jq", jq], capture_output=True, text=True, encoding="utf-8", errors="replace")
        except FileNotFoundError:
            if asked:
                print("--github：gh がないので、PR の作成者は取らない", file=sys.stderr)
            break
        if out.returncode != 0:
            print(f"gh api が失敗したので、{'以降の ' if page > 1 else ''}PR の作成者は覚えておいた分とメールから取る"
                  f"（{out.stderr.strip()}。止めるなら --no-github）", file=sys.stderr)
            break
        rows = [l.split("\t", 3) for l in out.stdout.splitlines()]
        rows = [r + [""] * (4 - len(r)) for r in rows if len(r) >= 2]
        fresh = [r for r in rows if r[0] not in known]
        found.update((r[0], r[1:]) for r in rows)
        if len(rows) < 100 or not fresh:
            break
        page += 1
    if path and found != known:
        try:
            path.write_text(json.dumps({"repo": url, "prs": found}, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return found


def use_prs(prs):
    PR_AUTHORS.update((n, f"@{login}") for n, (login, _, _) in prs.items())
    PR_SHAS.update((sha, (n, title)) for n, (_, sha, title) in prs.items() if sha)


def by_pr(item):
    """件名に番号のない変更は、PR を入れたコミットから PR に結びつける。GitHub から取った PR の作成者があれば、Author にする。"""
    if not item["pr"] and item.get("sha") in PR_SHAS and not item["title"].startswith(("（", SYNC)):
        item["pr"], title = PR_SHAS[item["sha"]]
        item["title"] = title or item["title"]
    if item["pr"] in PR_AUTHORS:
        item["author"] = PR_AUTHORS[item["pr"]]
    return item


def account(email):
    m = NOREPLY_RE.match(email.strip())
    return f"@{m.group(1)}" if m else UNKNOWN


def changes(tz, branches):
    """各ブランチの --first-parent の変更を、古い順に返す。マージコミットは 1 つ目の親との差分でファイルを数え、
    Author は取り込んだ側の先頭（2 つ目の親）のコミットの author から取る。
    どのブランチにも入ったコミットは 1 つにし、入ったブランチを並べる。"""
    logs = {name: first_parent(ref, tz) for name, ref in branches}
    shas = {name: {c[0] for c in log} for name, log in logs.items()}
    seen, items, tips = {}, [], {}
    for name, log in logs.items():
        for sha, parents, email, date, subject, body, files in log:
            if sha in seen:
                seen[sha]["branches"].append(name)
                continue
            parents = parents.split()
            item = parse(subject, body, parents, name, shas)
            item.update(sha=sha, date=date, author=account(email), branches=[name],
                        files=[f for f in files.splitlines() if f.strip()])
            between = item.pop("between")
            if len(parents) > 1:
                tips[sha] = parents[1]
                if not between:
                    item["range"] = f"{parents[0]}..{parents[1]}"
            seen[sha] = item
            items.append(item)
    for sha, who in tip_authors(tips).items():
        seen[sha]["author"] = who
    return sorted((by_pr(i) for i in items), key=lambda i: i["date"])


def tip_authors(tips):
    """マージコミットごとの、取り込んだ側の先頭（2 つ目の親）のコミットの Author。"""
    if not tips:
        return {}
    out = git("log", "--no-walk=unsorted", "--stdin", f"--format=%H{FIELD}%aE", stdin="\n".join(set(tips.values())) + "\n")
    emails = dict(line.split(FIELD, 1) for line in out.splitlines() if FIELD in line)
    return {sha: account(emails[tip]) for sha, tip in tips.items() if tip in emails}


def inside(item):
    """マージコミットが取り込んだ側の --first-parent のコミットを、古い順に返す。PR の中のコミットや、
    読んでいないブランチ（release/1.2 など）でマージされた PR が、実際の改修の中身として見える。
    読んだブランチどうしのマージは、中身が元のブランチに 1 件ずつ出るので返さない。日付はマージの日。"""
    if "inside" not in item:
        found, tips = [], {}
        if item.get("range"):
            fmt = FIELD.join(["%H", "%P", "%aE", "%s", "%b"])
            out = git("log", "--first-parent", "--reverse", f"--format={COMMIT}{fmt}", item["range"])
            for sha, parents, email, subject, body in (c.split(FIELD) for c in out.split(COMMIT)[1:]):
                parents = parents.split()
                inner = parse(subject, body, parents, None, {})
                inner.pop("between")
                inner.update(sha=sha, date=item["date"], author=account(email), branches=item["branches"], files=[])
                if len(parents) > 1:
                    tips[sha] = parents[1]
                found.append(inner)
            by_sha = {i["sha"]: i for i in found}
            for sha, who in tip_authors(tips).items():
                by_sha[sha]["author"] = who
        item["inside"] = [by_pr(i) for i in found]
    return item["inside"]


def key(item):
    return f"#{item['pr']}" if item["pr"] else item["sha"]


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
    item["between"] = bool(source)
    if source:
        item["title"] = BETWEEN.format(source) + item["title"].removeprefix(SYNC)
    elif RELEASE_RE.match(item["title"]):
        item["title"] = RELEASE + item["title"]
    return item


def link(item, url):
    if item["pr"]:
        return f"[#{item['pr']}]({url}/pull/{item['pr']})" if url else f"#{item['pr']}"
    short = item.get("short") or item["sha"][:7]  # どこにもないハッシュは、書かれたまま（作り直しても変わらない）
    return f"[{short}]({url}/commit/{item['sha']})" if url else short


def summary_of(path):
    """いまのファイルの「## 主な変更」の中身。なければ None。"""
    if not path.exists():
        return None
    m = re.search(rf"^{re.escape(SUMMARY)}\n(.*?)(?=^## |\Z)", path.read_text(encoding="utf-8"), re.S | re.M)
    return m.group(1).strip() if m else None


def list_lines(items, depth, url, many):
    """その月の全変更を日付の順に。各行に、いちばん多く変えた置き場所と Author を添え、マージコミットの下には
    取り込んだ側のコミット（inside）を字下げして並べる（--list が出す）。"""
    lines = []
    for item in items:
        counts = collections.Counter(area(f, depth) for f in item["files"])
        places = sorted(counts, key=lambda a: (-counts[a], a))
        where = f"、{places[0]}" + (f" ほか {len(places) - 1}" if len(places) > 1 else "") if places else ""
        into = f"、{'・'.join(item['branches'])} へ" if many else ""
        lines.append(f"- {item['date']} {item['title']}（{link(item, url)}{where}、{item['author']}{into}）")
        lines += [f"  - {i['title']}（{link(i, url)}、{i['author']}）" for i in inside(item)]
    return lines


def month_page(month, summary):
    return "\n".join([f"# {month}", "", SUMMARY, "", summary or EMPTY]) + "\n"


def cells(line):
    return [c.strip() for c in CELL_RE.split(line.strip())[1:-1]]


def pr_cells(summary):
    """主な変更の表の PR の列と、前の形の行の括弧の中だけ（概要の言葉の #12 や英数字を参照と取り違えない）。"""
    found = []
    for line in summary.splitlines():
        parts = cells(line) if line.strip().startswith("|") else []
        m = OLD_LINE_RE.match(line.strip())
        found += [parts[2]] if len(parts) == 4 and is_row(parts) else [m.group(2)] if m else []
    return "\n".join(found)


def is_row(parts):
    """表の中身の行か（見出しの行と区切りの行は除く）。"""
    return len(parts) == 4 and parts[0] != "日付" and not all(c and set(c) <= set("-:") for c in parts)


def lookup(text, index):
    """PR の列の文から、その月の変更を順に返す。見つからない参照は None。"""
    found = []
    for m in KEY_RE.finditer(re.sub(r"\]\([^)]*\)", "]", text)):  # リンク先の URL の中は見ない
        pr, sha = m.groups()
        item = index.get(f"#{pr}") if pr else next((i for k, i in index.items() if k.startswith(sha)), None)
        if item is None or item not in found:
            found.append(item)
    return found


def resolve(text, index, everything):
    """PR の列の参照を、その月の変更、なければ全部の月の変更から探す。どこにもなければ、番号かハッシュだけの変更にする
    （リンクと、GitHub から取れた Author は入れる）。その月にない参照は、problems が崩れとして知らせる。"""
    found = []
    for m in KEY_RE.finditer(re.sub(r"\]\([^)]*\)", "]", text)):  # 参照ごとに探す（重なっても、後ろの参照を落とさない）
        pr, sha = m.groups()
        item = lookup(m.group(0), index)[0] or lookup(m.group(0), everything)[0] or {
            "pr": pr, "sha": sha or "", "short": sha, "date": "", "author": PR_AUTHORS.get(pr, UNKNOWN) if pr else UNKNOWN}
        if item not in found:
            found.append(item)
    return found


def row(summary, items, url, written=""):
    """日付は最初の変更の日、Author は変更ごとのアカウント名（重なりは 1 つ）。GitHub から取れなかった変更があれば、
    書いてある Author を残す（gh が使えるかどうかで --check の結果が変わらないように）。"""
    authors = "、".join(dict.fromkeys(i["author"] for i in items))
    if written and not all(i["pr"] in PR_AUTHORS for i in items):
        authors = written
    date = next((i["date"] for i in items if i["date"]), "")
    return f"| {date} | {summary} | {'、'.join(link(i, url) for i in items)} | {authors} |"


def tidy(text, kind, index=None, url=None, everything=None):
    """分類の見出しの直下に説明を入れ、月の表の日付・Author・PR の列を、その月の変更から埋め直す。
    前の形の「- 概要（#12）」の行は表の行に移す。中身の言葉（概要・年の要点）は変えない。"""
    if text in (None, "", EMPTY) or NOTHING_RE.match(text):
        return text
    blocks, head = [], []
    for line in text.splitlines():
        if line.strip().startswith("### "):
            blocks.append((line.strip()[4:].strip(), []))
        elif blocks:
            blocks[-1][1].append(line.strip())
        else:
            head.append(line.strip())
    out = [l for l in head if l]
    for heading, lines in blocks:
        lines = [l for l in lines if l]
        desc = DESCRIPTIONS.get(heading)
        if lines and lines[0] == desc:
            lines = lines[1:]
        if kind == "month":  # 分類が決まりと違っても、表の行は埋める（分類の崩れは problems が知らせる）
            rows = []
            for line in lines:
                m = OLD_LINE_RE.match(line)
                parts = cells(line) if line.startswith("|") else None
                if parts and is_row(parts):
                    found = resolve(parts[2], index, everything or {})
                    rows.append(row(parts[1], found, url, parts[3]) if found else line)
                elif m:
                    found = resolve(m.group(2), index, everything or {})
                    summary = m.group(1).replace("|", "\\|")
                    rows.append(row(summary, found, url) if found else f"|  | {summary} | {m.group(2)} |  |")
                elif not parts or len(parts) != 4:
                    rows.append(line)
            lines = [HEADER, RULE] + rows if rows else []
        out += [""] * bool(out) + [f"### {heading}", ""] + ([desc, ""] if desc else []) + lines
    return "\n".join(out).strip()


def read_from(branches):
    """main（origin/main）、develop（origin/develop）の形。"""
    shown = [(name, ref.removeprefix("refs/remotes/").removeprefix("refs/heads/")) for name, ref in branches]
    return "、".join(f"{name}（{ref}）" if ref != name else name for name, ref in shown)


def problems(text, kind, index=None):
    """主な変更（kind="month"）か年の要点（kind="year"）の形の崩れを、(行, 中身) で返す。tidy を通したあとの文に使う。"""
    if text in (None, "", EMPTY) or NOTHING_RE.match(text):
        return []
    found, seen, heading, at, items = [], set(), None, 0, 0
    names = DESCRIPTIONS
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or (heading and line in (names.get(heading), HEADER, RULE)):
            continue
        if line.startswith("### "):
            if heading and not items:
                found.append((at, f"### {heading} の下に行がない"))
            heading, at, items = line[4:].strip(), number, 0
            if heading not in names:
                found.append((number, f"分類 {heading} は {'・'.join(names)} のどれでもない"))
            elif heading in seen:
                found.append((number, f"分類 {heading} が 2 度ある"))
            seen.add(heading)
        elif kind == "month" and line.startswith("|"):
            items += 1
            parts = cells(line)
            if not heading:
                found.append((number, "行の前に ### <分類> がない"))
            if len(parts) != 4:
                found.append((number, f"表の行は {HEADER} の 4 列で書く"))
                continue
            refs = lookup(parts[2], index or {})
            if not refs:
                found.append((number, "PR の列に PR かコミット（[#123](…) など）がない"))
            elif None in refs:
                found.append((number, "PR の列の参照が、この月の変更にない"))
            if not parts[1]:
                found.append((number, "概要の列が空"))
            if SHORT_DATE_RE.search(parts[1]):
                found.append((number, "日付は YYYY-MM-DD、月は YYYY-MM で書く"))
        elif kind == "year" and line.startswith("- "):
            items += 1
            if not heading:
                found.append((number, "行の前に ### <分類> がない"))
            if not PERIOD_RE.search(line):
                found.append((number, "行の末尾に（YYYY-MM）か（YYYY-MM〜YYYY-MM）がない"))
            if SHORT_DATE_RE.search(line.split("（")[0]):
                found.append((number, "日付は YYYY-MM-DD、月は YYYY-MM で書く"))
        else:
            found.append((number, f"### <分類> と{'表の行' if kind == 'month' else '「- 」で始まる行'}だけを書く"))
    if heading and not items:
        found.append((at, f"### {heading} の下に行がない"))
    return sorted(found)


def year_summaries(path):
    """いまの年表の、年ごとの要点。"""
    return years_in(path.read_text(encoding="utf-8")) if path.exists() else {}


def years_in(text):
    """年表の文から、年ごとの要点（見出しの下から表の前まで）を取る。"""
    found = re.findall(r"^## (\d{4})\n(.*?)(?=^\| 月 \||^## |\Z)", text, re.S | re.M)
    return {year: body.strip() for year, body in found}


def points_in(text):
    """年表の表の、月ごとの主な変更の要約（人か AI が書く）。"""
    found = (ROW_RE.match(l) for l in (text or "").splitlines())
    return {m.group(1): m.group(2).strip() for m in found if m and m.group(2).strip() != NO_POINT}


def needs_point(summary):
    """月の主な変更を書いたのに、年表の要約がまだ要るか（目立った変更なしは、その文をそのまま入れる）。"""
    return summary not in (None, "", EMPTY) and not NOTHING_RE.match(summary)


def readme_page(months, folder, summaries, shown):
    """年表を兼ねた索引。年ごとに、要点と、月ごとの主な変更の要約（どちらも人か AI が書く）の表を並べる。新しい年が上。
    載せるのは、書き直す月（shown）と、前から年表にある月（人が書いた要約を消さない）。"""
    # 以前の timeline.md に書いた要点も拾う。README.md に書いたものが先
    kept = {**year_summaries(folder / "timeline.md"),
            **{y: t for y, t in year_summaries(folder / "README.md").items() if t != EMPTY}}
    readme = folder / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    points = points_in(text)
    listed = {m.group(1) for m in (ROW_RE.match(l) for l in text.splitlines()) if m}
    months = {m: months[m] for m in months if m in set(shown) | listed}
    out = ["# 変更の履歴"]
    for year in sorted({m[:4] for m in months}, reverse=True):
        out += ["", f"## {year}", "", tidy(kept.get(year), "year") or EMPTY, "", "| 月 | 件数 | 主な変更 |", "|---|---|---|"]
        for month in sorted((m for m in months if m.startswith(year)), reverse=True):
            summary = summaries[month]
            point = summary[2:] if summary and NOTHING_RE.match(summary) else points.get(month) if needs_point(summary) else None
            out.append(f"| [{month}]({month}.md) | {len(months[month])} | {point or NO_POINT} |")
    return "\n".join(out) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder", type=pathlib.Path)
    p.add_argument("--branch", action="append", help="読むブランチ（何度でも。既定は長く続くブランチを全部）")
    p.add_argument("--depth", type=int, default=2, help="置き場所として数えるフォルダーの段数（既定 2）")
    p.add_argument("--since", help="この月（YYYY-MM）から書く")
    p.add_argument("--until", help="この月（YYYY-MM）まで書く")
    p.add_argument("--tz", default="Asia/Tokyo", help="日付の時間帯（既定 Asia/Tokyo）")
    p.add_argument("--github", action="store_true", help="PR の作成者が取れないとき、理由を出す（既定でも gh があれば取る）")
    p.add_argument("--no-github", action="store_true", help="GitHub に問い合わせない（Author はメールから取る）")
    p.add_argument("--check", action="store_true", help="書かずに、最新かを確かめる")
    p.add_argument("--list", metavar="YYYY-MM", help="書かずに、その月の全変更を出す")
    args = p.parse_args()
    for flag, value in (("--since", args.since), ("--until", args.until), ("--list", args.list)):
        if value and not MONTH_RE.match(value):
            p.error(f"{flag} は YYYY-MM で書く")
    for name in args.branch or []:
        if not has_ref(name):
            p.error(f"ブランチ {name} が見つからない")
    branches = [(name, name) for name in args.branch] if args.branch else long_lived()
    if branches == [("HEAD", "HEAD")] and not has_ref("HEAD"):
        print("コミットがまだないので、書くものはない")
        return 0
    url = repo_url()
    if not args.no_github:
        # --list（書き手が月ごとに呼ぶ）は問い合わせず、覚えておいた分だけを使う
        use_prs(github_prs(url, args.github, online=not args.list))
    months = collections.defaultdict(list)
    for item in changes(args.tz, branches):
        months[item["date"][:7]].append(item)
    # --since・--until は書き直す月を絞る。年表には、その月と前から載っている月を載せる（人が書いた行と要約を消さない）
    shown = sorted(m for m in months if (not args.since or m >= args.since) and (not args.until or m <= args.until))
    if args.list:
        for line in list_lines(months.get(args.list, []), args.depth, url, len(branches) > 1):
            print(line)
        print(f"{args.list}：{len(months.get(args.list, []))} 件。読んだブランチ：{read_from(branches)}")
        return 0
    indexes, summaries = {}, {}
    everything = {key(i): i for items in months.values() for i in items}
    for m, items in months.items():
        index = {key(i): i for i in items}
        summary = summary_of(args.folder / f"{m}.md")
        # 表の PR の列がマージの中の PR やコミットを指していれば、そこまで探す（マージごとに git を 1 回回すので、要るときだけ）
        if summary and None in lookup(pr_cells(summary), index):
            for i in items:
                for j in inside(i):
                    index.setdefault(key(j), j)
        indexes[m] = index
        summaries[m] = tidy(summary, "month", index, url, everything)
    pages = {f"{m}.md": month_page(m, summaries[m]) for m in shown}
    pages["README.md"] = readme_page(months, args.folder, summaries, shown)
    old = args.folder / "timeline.md"
    stale = [name for name, text in sorted(pages.items())
             if not (args.folder / name).exists() or (args.folder / name).read_text(encoding="utf-8") != text]
    broken = [f"{args.folder / f'{m}.md'} の「{SUMMARY}」{n} 行目：{what}"
              for m in shown for n, what in problems(summaries[m], "month", indexes[m])]
    broken += [f"{args.folder / 'README.md'} の「## {y}」{n} 行目：{what}"
               for y, text in sorted(years_in(pages["README.md"]).items()) for n, what in problems(text, "year")]
    points = points_in(pages["README.md"])
    broken += [f"{args.folder / 'README.md'} の {m}：主な変更の要約（表の「主な変更」の列）がない"
               for m in shown if needs_point(summaries[m]) and m not in points]
    for line in broken:
        print(line)
    if args.check:
        for name in stale:
            print(f"{args.folder / name} が古い")
        if old.exists():
            print(f"{old} は README.md に移った")
        bad = stale or old.exists()
        print(f"{len(pages) - 1} か月分は最新" if not bad else f"build_history.py {args.folder} で作り直す")
        if broken:
            print(f"形の崩れ {len(broken)} 件")
        return 1 if bad or broken else 0
    args.folder.mkdir(parents=True, exist_ok=True)
    for name in stale:
        (args.folder / name).write_text(pages[name], encoding="utf-8")
    if old.exists():
        old.unlink()  # 年ごとの要点は README.md に移した
    total = sum(len(months[m]) for m in shown)
    print(f"{args.folder}：{len(shown)} か月、{total} 件（書き換え {len(stale)} ファイル、形の崩れ {len(broken)} 件）。"
          f"読んだブランチ：{read_from(branches)}")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
