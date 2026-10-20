#!/usr/bin/env python3
"""デフォルトブランチに入った変更を、月ごとの Markdown に書き出す（change-history の 1 段目）。

  build_history.py <フォルダー> [--branch main] [--depth 2] [--since YYYY-MM] [--until YYYY-MM]   GitHub から取り、書き出す
  build_history.py <フォルダー> --check                                                         最新か確かめる（古ければ終了コード 1）
  build_history.py <フォルダー> --list YYYY-MM                                                  その月の全変更を出す（書かない）
  build_history.py <フォルダー> --show <コミット>                                               変えたファイルを出す（書かない）

どれも --repo <クローン> で、いまのディレクトリでないリポジトリを読める（複数のリポジトリをまとめる build_many.py が使う）。

変更は 2 つ。GitHub でそのブランチにマージされた PR（日付はマージの日、Author は PR の作成者、gh api で取る）と、
PR を通さずにそのブランチへ入ったコミット（手元の git の --first-parent。Author は GitHub のコミットのアカウント）。
gh が要る。書き出すときだけ GitHub に問い合わせ、取ったものは .git/decision-continuity-prs.json に覚えておく
（--check・--list・--show は問い合わせず、覚えておいた分を使う）。
読むブランチは推測しない。--branch を言わなければ、GitHub のデフォルトブランチだけを読む。

月ごとの YYYY-MM.md（主な変更の表）と、年表を兼ねた索引の README.md を書く。日付は YYYY-MM-DD、月は YYYY-MM で書く。
全変更の一覧はファイルに書かず、--list で出す（主な変更を選ぶ材料）。年表の件数は、その月の PR と直接のコミットの数。
変更のなかった月も「変更なし」の行で載せる。依存の更新・リリースだけの終わった月は、主な変更に「- 目立った変更なし（…のみ）」と書く。
各月の「## 主な変更」と、README.md の各年の要点・各月の要約は、作り直しても残す（人か AI が書く）。月の主な変更は 1 つの表、
年の要点は「- 」の行で、どちらも分類に分けない（前の形の ### <分類> の見出しと説明の文は外す）。表は人か AI が概要と
PR の列だけを書き、日付・Author・PR のリンクと、その PR を挙げた Decision log へのリンクはスクリプトが入れる。
決まった形でなければ、どこが崩れているかを出し、終了コード 1 を返す。標準ライブラリだけを使う。
人はアカウント名（@login）で、Author の列にだけ書く。名前（git の author 名）は書き出さない。
"""
import argparse
import collections
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys
import unicodedata
import zoneinfo

SQUASH_RE = re.compile(r"^(.*?)\s*\(#(\d+)\)\s*$")
# PR を通さないマージ（Merge branch '3.0.x'、Merge remote-tracking branch 'origin/stable'）
SYNC_RE = re.compile(r"^Merge (?:remote-tracking )?branch ")
SYNC = "（ブランチの取り込み）"
# 版を上げるだけの定型のリリース（Release v1.2.0、Bump version to 1.2.0、chore(release): 1.2.0、v1.2.0）
RELEASE_RE = re.compile(r"^(?:chore\(release\)|(?:chore:\s*)?(?:release|prepare release|bump version|version)\b).*?\bv?\d+\.\d+"
                        r"|^v?\d+\.\d+(?:\.\d+)*$", re.I)
RELEASE = "（リリース）"
# 依存の更新（Dependabot・Renovate・pre-commit.ci などの定型の件名）
DEPS_RE = re.compile(r"^(?:(?:chore|build|fix|ci)\((?:deps|deps-dev)\)!?:|bump \S+ from \S+ to \S+|bump the \S+ group"
                     r"|update dependency \S+|\[pre-commit\.ci\] pre-commit autoupdate)", re.I)
DEPS = "（依存の更新）"
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
SUMMARY = "## 主な変更"
EMPTY = "（まだ書いていない）"
# 前の形で、月の主な変更と年の要点を分けていた分類の説明（見出しの直下にスクリプトが入れていた）。作り直すときに外す
OLD_DESCRIPTIONS = {
    "使う人に見える機能の追加と変更",
    "開発・リリース・運用の進め方の改善（CI、デプロイ、監視、手順、文書など）",
    "不具合の修正と、その再発を防ぐ変更",
}
HEADER, RULE = "| 日付 | 概要 | PR | Author |", "|---|---|---|---|"
# 1 行の PR の列に書く参照の上限（多すぎる行は読めない）
MAX_REFS = 5
NO_POINT = "まだ"
ROW_RE = re.compile(r"^\| \[(\d{4}-\d{2})\]\(\1\.md\) \| \d+ \| (.*) \|$")
UNKNOWN = "—"
CELL_RE = re.compile(r"(?<!\\)\|")
OLD_LINE_RE = re.compile(r"^- (.*)（([^（）]*)）$")
# 書くことのない月：取り込みだけ、リリースだけ、依存の更新だけ、など。理由は（…のみ）に書く
NOTHING_RE = re.compile(r"^- 目立った変更なし（[^（）\n]+のみ）$")
# 書き手を呼ばずにスクリプトが「目立った変更なし（…のみ）」と書く変更の印と、（…のみ）に書く名前（この順に並べる）
QUIET = {DEPS: "依存の更新", RELEASE: "リリース", SYNC: "ブランチの取り込み"}
# 変更のなかった月（年表の表の行）と年（年の要点）
NONE = "変更なし"
# 月の行の末尾は PR かコミット（リンクでも、なくても）、年の行の末尾は月か期間
KEY_RE = re.compile(r"#(\d+)|\b([0-9a-f]{7,40})\b")
PERIOD_RE = re.compile(r"（\d{4}-\d{2}(?:〜\d{4}-\d{2})?）$")
# 略した日付（5 月、05-02）。YYYY-MM と YYYY-MM-DD には当たらない
SHORT_DATE_RE = re.compile(r"\d+\s*月|(?<![\d-])\d{1,2}-\d{1,2}(?![\d-])")
COMMIT, FIELD = "\x1e", "\x1f"
# PR の番号ごとの、その PR を挙げた Decision log の (番号, 月のファイルからの相対パス)。PR の列に PR の後ろに添える
DECISIONS = {}
# Decision log のファイル（0001-retry-limit.md）と、その中の PR（[PR #101][pr101] の文か、<origin>/pull/101 のリンク）
DL_FILE_RE = re.compile(r"^(\d{4})-[^/]*\.md$")
DL_PR_RE = re.compile(r"\bPR #(\d+)")
# GraphQL で 1 回に聞くコミットの数
BATCH = 50
# 読むリポジトリ（--repo）。None ならいまのディレクトリ
REPO = None


def git(*args, tz=None):
    env = dict(os.environ, TZ=tz) if tz else None
    out = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=REPO)
    if out.returncode != 0:
        sys.exit(f"git {args[0]} が失敗した: {out.stderr.strip()}")
    return out.stdout


def gh(*args):
    """gh api の GET（GraphQL は問い合わせだけ）。gh がないか失敗したら、理由を出して止まる（change-history は gh が要る）。"""
    try:
        out = subprocess.run(["gh", "api", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        sys.exit("change-history は gh が要る（GitHub の PR から作る）。gh を入れ、gh auth login する")
    if out.returncode != 0:
        sys.exit(f"gh api {args[0]} が失敗した: {out.stderr.strip()}")
    return json.loads(out.stdout or "null")


def github_repo():
    """origin の URL から owner/repo。GitHub でなければ None。"""
    out = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, cwd=REPO)
    m = re.search(r"(?:github\.com[:/])([^/]+/[^/]+?)(?:\.git)?/?$", out.stdout.strip())
    return m.group(1) if m else None


def area(path, depth):
    """変更したファイルの置き場所。depth 段までのフォルダー。ルートのファイルは「（ルート）」。"""
    parts = path.split("/")[:-1][:depth]
    return "/".join(parts) + "/" if parts else "（ルート）"


def has_ref(ref):
    return subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], capture_output=True, cwd=REPO).returncode == 0


def local_ref(name):
    """ブランチの手元の ref。origin/ にあればそれ（手元のものは古いことがある）、なければ手元のもの。なければ None。"""
    return next((r for r in (f"refs/remotes/origin/{name}", f"refs/heads/{name}") if has_ref(r)), None)


def cache_file():
    """GitHub から取ったものを覚えておく場所。.git の中なので、リポジトリには入らない。"""
    out = subprocess.run(["git", "rev-parse", "--git-common-dir"], capture_output=True, text=True, cwd=REPO)
    return pathlib.Path(REPO or ".") / out.stdout.strip() / "decision-continuity-prs.json"


def load_cache(slug):
    path = cache_file()
    try:
        saved = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except ValueError:
        saved = {}
    if saved.get("repo") != slug or saved.get("version") != 2:
        saved = {}
    return {"repo": slug, "version": 2, "default": saved.get("default"), "prs": saved.get("prs", {}),
            "commits": saved.get("commits", {})}


def save_cache(cache):
    try:
        cache_file().write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def fetch_prs(slug, base, known):
    """base にマージされた PR の 番号 → [作成者, マージの日時, PR を入れたコミット, タイトル]（マージされずに閉じた PR は None）。
    覚えておいた分に、更新の新しい順に 100 件ずつ足し、全部を覚えている PR のページが来たら止める。"""
    found, page = dict(known), 1
    while True:
        rows = gh(f"repos/{slug}/pulls?state=closed&base={base}&sort=updated&direction=desc&per_page=100&page={page}") or []
        fresh = [r for r in rows if str(r["number"]) not in known]
        for r in rows:
            found[str(r["number"])] = [(r.get("user") or {}).get("login") or "", r["merged_at"], r.get("merge_commit_sha") or "",
                                       r.get("title") or ""] if r.get("merged_at") else None
        if len(rows) < 100 or not fresh:
            return found
        page += 1


def fetch_commits(slug, shas, base):
    """コミットの ハッシュ → [GitHub のアカウント, そのコミットを入れた base への PR の番号（なければ ""）]。
    Rebase and merge の PR のコミットは、その PR に結びつく。GraphQL で BATCH 件ずつ聞く。"""
    owner, name = slug.split("/", 1)
    found = {}
    for start in range(0, len(shas), BATCH):
        part = shas[start:start + BATCH]
        fields = "".join(f' c{i}: object(oid: "{sha}") {{ ... on Commit {{ author {{ user {{ login }} }} '
                         f'associatedPullRequests(first: 10) {{ nodes {{ number mergedAt baseRefName }} }} }} }}'
                         for i, sha in enumerate(part))
        data = gh("graphql", "-f", f'query=query {{ repository(owner: "{owner}", name: "{name}") {{{fields} }} }}')
        repo = ((data or {}).get("data") or {}).get("repository") or {}
        for i, sha in enumerate(part):
            node = repo.get(f"c{i}") or {}
            login = (((node.get("author") or {}).get("user")) or {}).get("login") or ""
            prs = [p for p in ((node.get("associatedPullRequests") or {}).get("nodes") or [])
                   if p.get("mergedAt") and p.get("baseRefName") == base]
            found[sha] = [login, str(prs[0]["number"]) if prs else ""]
    return found


def first_parent(ref, tz):
    """ref の --first-parent の各コミットを、古い順に (ハッシュ, 親, ブランチに入った日, 入った日時, 件名, 変えたファイル) で返す。"""
    fmt = FIELD.join(["%H", "%P", "%cd", "%cI", "%s"])
    out = git("log", "--first-parent", "--reverse", "--diff-merges=first-parent", "--name-only",
              "--date=format-local:%Y-%m-%d", f"--format={COMMIT}{fmt}{FIELD}", ref, "--", tz=tz)
    found = []
    for chunk in out.split(COMMIT)[1:]:
        sha, parents, date, at, subject, files = chunk.split(FIELD)
        found.append((sha, parents.split(), date, at, subject, [f for f in files.splitlines() if f.strip()]))
    return found


def mark(title, merge=False):
    """定型の変更に印を付ける。PR を通さないマージは（ブランチの取り込み）。"""
    if merge and SYNC_RE.match(title):
        return SYNC + title
    if RELEASE_RE.match(title):
        return RELEASE + title
    if DEPS_RE.match(title):
        return DEPS + title
    return title


def moment(stamp):
    return datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def local_date(stamp, tz):
    return moment(stamp).astimezone(zoneinfo.ZoneInfo(tz)).strftime("%Y-%m-%d")


def changes(cache, branches, tz, online, slug):
    """読むブランチの変更を、古い順に返す。PR は GitHub の、直接のコミットは手元の git の --first-parent のもの。"""
    items = {}
    for base, ref in branches:
        if online:
            cache["prs"][base] = fetch_prs(slug, base, cache["prs"].get(base, {}))
        prs = {n: v for n, v in cache["prs"].get(base, {}).items() if v}
        merged = {v[2]: n for n, v in prs.items() if v[2]}
        for n, (login, at, sha, title) in prs.items():
            items.setdefault(f"#{n}", dict(pr=n, sha=sha, date=local_date(at, tz), at=moment(at), title=mark(title),
                                           author=f"@{login}" if login else UNKNOWN, files=[]))
        log = first_parent(ref, tz)
        # PR を入れたコミットでも、件名の (#12) が base の PR でもないもの。Rebase and merge のコミットもここに入る
        rest = [c for c in log if c[0] not in merged and not (SQUASH_RE.match(c[4]) and SQUASH_RE.match(c[4]).group(2) in prs)]
        unknown = [c[0] for c in rest if c[0] not in cache["commits"]]
        if online and unknown:
            cache["commits"].update(fetch_commits(slug, unknown, base))
        for sha, parents, date, at, subject, files in log:
            squash = SQUASH_RE.match(subject)
            pr = merged.get(sha) or (squash.group(2) if squash and squash.group(2) in prs else None) \
                or (cache["commits"].get(sha) or ["", ""])[1] or None
            if pr in prs:
                items[f"#{pr}"]["files"] += files
            elif sha not in items:
                login = (cache["commits"].get(sha) or [""])[0]
                items[sha] = dict(pr=None, sha=sha, date=date, at=moment(at), title=mark(subject, len(parents) > 1),
                                  author=f"@{login}" if login else UNKNOWN, files=files)
    return sorted(items.values(), key=lambda i: i["at"])


def decision_logs(logs, folder, url):
    """Decision log の置き場所から、PR の番号 → [(DL の番号, 月のファイルからの相対パス)]。置き場所がなければ空。"""
    found = collections.defaultdict(list)
    if not logs or not logs.is_dir():
        return found
    pulls = re.compile(rf"{re.escape(url)}/pull/(\d+)\b")
    for path in sorted(logs.iterdir()):
        m = DL_FILE_RE.match(path.name)
        if not m:
            continue
        text = path.read_text(encoding="utf-8")
        prs = set(DL_PR_RE.findall(text)) | set(pulls.findall(text))
        where = pathlib.PurePath(os.path.relpath(path, folder)).as_posix()
        for pr in prs:
            found[pr].append((int(m.group(1)), where))
    return found


def key(item):
    return f"#{item['pr']}" if item["pr"] else item["sha"]


def quiet(items):
    """依存の更新・ブランチの取り込み・リリースだけの月なら、「- 目立った変更なし（…のみ）」の文。ほかがあれば None。"""
    kinds = {next((n for mark_, n in QUIET.items() if i["title"].startswith(mark_)), None) for i in items}
    if not kinds or None in kinds:
        return None
    return f"- 目立った変更なし（{'・'.join(n for n in QUIET.values() if n in kinds)}のみ）"


def link(item, url):
    if item["pr"]:
        return f"[#{item['pr']}]({url}/pull/{item['pr']})"
    short = item.get("short") or item["sha"][:7]  # どこにもないハッシュは、書かれたまま（作り直しても変わらない）
    return f"[{short}]({url}/commit/{item['sha']})"


def summary_of(path):
    """いまのファイルの「## 主な変更」の中身。なければ None。"""
    if not path.exists():
        return None
    m = re.search(rf"^{re.escape(SUMMARY)}\n(.*?)(?=^## |\Z)", path.read_text(encoding="utf-8"), re.S | re.M)
    return m.group(1).strip() if m else None


def list_lines(items, depth, url):
    """その月の全変更を日付の順に。各行に、いちばん多く変えた置き場所と Author を添える（--list が出す）。"""
    lines = []
    for item in items:
        counts = collections.Counter(area(f, depth) for f in item["files"])
        places = sorted(counts, key=lambda a: (-counts[a], a))
        where = f"、{places[0]}" + (f" ほか {len(places) - 1}" if len(places) > 1 else "") if places else ""
        lines.append(f"- {item['date']} {item['title']}（{link(item, url)}{where}、{item['author']}）")
    return lines


def month_page(month, summary):
    return "\n".join([f"# {month}", "", SUMMARY, "", summary or EMPTY]) + "\n"


def cells(line):
    return [c.strip() for c in CELL_RE.split(line.strip())[1:-1]]


def is_row(parts):
    """表の中身の行か（見出しの行と区切りの行は除く）。"""
    return len(parts) == 4 and parts[0] != "日付" and not all(c and set(c) <= set("-:") for c in parts)


def ref_text(text):
    """PR の列の文を、参照（#12 かコミットのハッシュ）を拾える形にする。リンク先の URL の中は見ない。書き方の揺れも読む：
    全角（＃１２）、PR の URL（…/pull/12）、数字だけの列（12、13）。"""
    text = unicodedata.normalize("NFKC", re.sub(r"\]\([^)]*\)", "]", text))
    text = re.sub(r"https?://\S*?/pull/(\d+)\S*", r"#\1", text)
    return re.sub(r"\d+", r"#\g<0>", text) if re.fullmatch(r"[\d\s、,]+", text) else text


def lookup(text, index):
    """PR の列の文から、その月の変更を順に返す。見つからない参照は None。ハッシュは、PR を入れたコミットにも当てる。"""
    found = []
    for m in KEY_RE.finditer(ref_text(text)):
        pr, sha = m.groups()
        item = index.get(f"#{pr}") if pr else next((i for i in index.values() if i.get("sha", "").startswith(sha)), None)
        if item is None or item not in found:
            found.append(item)
    return found


def resolve(text, index, everything):
    """PR の列の参照を、その月の変更、なければ全部の月の変更から探す。どこにもなければ、番号かハッシュだけの変更にする
    （リンクは入れる）。その月にない参照は、problems が崩れとして知らせる。"""
    found = []
    for m in KEY_RE.finditer(ref_text(text)):  # 参照ごとに探す（重なっても、後ろの参照を落とさない）
        pr, sha = m.groups()
        item = lookup(m.group(0), index)[0] or lookup(m.group(0), everything)[0] or {
            "pr": pr, "sha": sha or "", "short": sha, "date": "", "author": UNKNOWN}
        if item not in found:
            found.append(item)
    return found


def row(summary, items, url):
    """日付は最初の変更の日、Author は変更ごとのアカウント名（重なりは 1 つ）。PR を挙げた Decision log を PR の後ろに添える。"""
    authors = "、".join(dict.fromkeys(i["author"] for i in items))
    date = next((i["date"] for i in items if i["date"]), "")
    logs = sorted({d for i in items for d in DECISIONS.get(i["pr"] or "", ())})
    refs = [link(i, url) for i in items] + [f"[DL-{n}]({where})" for n, where in logs]
    return f"| {date} | {summary} | {'、'.join(refs)} | {authors} |"


def tidy(text, kind, index=None, url=None, everything=None):
    """月の表の日付・Author・PR の列を、その月の変更から埋め直し、日付の順に 1 つの表に並べる。前の形の「- 概要（#12）」の行は
    表の行に移し、前の形の ### <分類> の見出しと説明の文は外す。中身の言葉（概要・年の要点）は変えない。"""
    if text in (None, "", EMPTY, NONE) or NOTHING_RE.match(text):
        return text
    lines = [l.strip() for l in text.splitlines()]
    lines = [l for l in lines if l and not l.startswith("### ") and l not in OLD_DESCRIPTIONS]
    if kind != "month":
        return "\n".join(lines)
    rows, rest = [], []
    for line in lines:
        m = OLD_LINE_RE.match(line)
        parts = cells(line) if line.startswith("|") else None
        if parts and is_row(parts):
            found = resolve(parts[2], index, everything or {})
            rows.append(row(parts[1], found, url) if found else line)
        elif m:
            found = resolve(m.group(2), index, everything or {})
            summary = m.group(1).replace("|", "\\|")
            rows.append(row(summary, found, url) if found else f"|  | {summary} | {m.group(2)} |  |")
        elif not parts or len(parts) != 4:
            (rows if parts else rest).append(line)
    # 表の行は日付の順に（日付のない行は後ろ）。同じ日は書いた順のまま。表でない行は、表の前に残す（problems が知らせる）
    rows.sort(key=lambda r: (cells(r)[0] or "9999") if r.startswith("|") and len(cells(r)) == 4 else "9999")
    return "\n".join(rest + ([""] if rest and rows else []) + ([HEADER, RULE] + rows if rows else [])).strip()


def read_from(branches):
    """main（origin/main）の形。"""
    shown = [(name, ref.removeprefix("refs/remotes/").removeprefix("refs/heads/")) for name, ref in branches]
    return "、".join(f"{name}（{ref}）" if ref != name else name for name, ref in shown)


def problems(text, kind, index=None):
    """主な変更（kind="month"）か年の要点（kind="year"）の形の崩れを、(行, 中身) で返す。tidy を通したあとの文に使う。"""
    if text in (None, "", EMPTY, NONE) or NOTHING_RE.match(text):
        return []
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or (kind == "month" and line in (HEADER, RULE)):
            continue
        if kind == "month" and line.startswith("|"):
            parts = cells(line)
            if len(parts) != 4:
                found.append((number, f"表の行は {HEADER} の 4 列で書く"))
                continue
            refs = lookup(parts[2], index or {})
            if not refs:
                found.append((number, "PR の列に PR かコミット（[#123](…) など）がない"))
            elif None in refs:
                found.append((number, "PR の列の参照が、この月の変更にない"))
            if len(refs) > MAX_REFS:
                found.append((number, f"PR は 1 行に {MAX_REFS} 件まで（多いときは代表を書き、件数は概要に書く）"))
            if not parts[1]:
                found.append((number, "概要の列が空"))
            if SHORT_DATE_RE.search(parts[1]):
                found.append((number, "日付は YYYY-MM-DD、月は YYYY-MM で書く"))
        elif kind == "year" and line.startswith("- "):
            if not PERIOD_RE.search(line):
                found.append((number, "行の末尾に（YYYY-MM）か（YYYY-MM〜YYYY-MM）がない"))
            if SHORT_DATE_RE.search(line.split("（")[0]):
                found.append((number, "日付は YYYY-MM-DD、月は YYYY-MM で書く"))
        else:
            found.append((number, f"{'表の行' if kind == 'month' else '「- 」で始まる行'}だけを書く"))
    return found


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


def month_range(first, last):
    """first から last までの月（YYYY-MM）を全部。"""
    y, m = map(int, first.split("-"))
    found = []
    while f"{y:04d}-{m:02d}" <= last:
        found.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return found


def readme_page(months, folder, summaries, shown):
    """年表を兼ねた索引。年ごとに、要点と、月ごとの主な変更の要約（どちらも人か AI が書く）の表を並べる。新しい年が上。
    載せるのは、書き直す月（shown）と、前から年表にある月（人が書いた要約を消さない）。"""
    # 以前の timeline.md に書いた要点も拾う。README.md に書いたものが先
    kept = {**year_summaries(folder / "timeline.md"),
            **{y: t for y, t in year_summaries(folder / "README.md").items() if t not in (EMPTY, NONE)}}
    readme = folder / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    points = points_in(text)
    listed = {m.group(1) for m in (ROW_RE.match(l) for l in text.splitlines()) if m}
    months = {m: months[m] for m in months if m in set(shown) | listed}
    out = ["# 変更の履歴"]
    every = month_range(min(months), max(months)) if months else []
    for year in sorted({m[:4] for m in every}, reverse=True):
        # 変更のなかった年は、要点の代わりに「変更なし」
        quiet_year = not any(m.startswith(year) for m in months)
        out += ["", f"## {year}", "", NONE if quiet_year else tidy(kept.get(year), "year") or EMPTY, "",
                "| 月 | 件数 | 主な変更 |", "|---|---|---|"]
        gap = []  # 続けて変更のなかった月（新しい順）
        for month in sorted((m for m in every if m.startswith(year)), reverse=True) + [None]:
            if month and month not in months:
                gap.append(month)
                continue
            if gap:  # 変更のなかった月も載せ、空いた期間が分かるようにする（続いた月は 1 行。月のファイルはない）
                out.append(f"| {gap[-1] if len(gap) == 1 else f'{gap[-1]}〜{gap[0]}'} | 0 | {NONE} |")
                gap = []
            if not month:
                break
            summary = summaries[month]
            point = summary[2:] if summary and NOTHING_RE.match(summary) else points.get(month) if needs_point(summary) else None
            out.append(f"| [{month}]({month}.md) | {len(months[month])} | {point or NO_POINT} |")
    return "\n".join(out) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder", type=pathlib.Path)
    p.add_argument("--branch", action="append", help="読むブランチ（何度でも。既定は GitHub のデフォルトブランチだけ）")
    p.add_argument("--depth", type=int, default=2, help="置き場所として数えるフォルダーの段数（既定 2）")
    p.add_argument("--since", help="この月（YYYY-MM）から書く")
    p.add_argument("--until", help="この月（YYYY-MM）まで書く")
    p.add_argument("--tz", default="Asia/Tokyo", help="日付の時間帯（既定 Asia/Tokyo）")
    p.add_argument("--check", action="store_true", help="書かずに、最新かを確かめる（GitHub に問い合わせない）")
    p.add_argument("--list", metavar="YYYY-MM", help="書かずに、その月の全変更を出す（GitHub に問い合わせない）")
    p.add_argument("--show", metavar="コミット", help="書かずに、そのコミットの件名・本文と変えたファイルを出す（人の名前は出さない）")
    p.add_argument("--repo", type=pathlib.Path, help="読むリポジトリ（既定はいまのディレクトリ）")
    p.add_argument("--github-repo", metavar="OWNER/REPO", help="GitHub のリポジトリ（既定は origin の URL から）")
    p.add_argument("--decision-logs", type=pathlib.Path,
                   help="PR の列にリンクを添える Decision log の置き場所（既定は docs/decision-logs。--repo のときは言われたときだけ）")
    args = p.parse_args()
    global REPO
    if args.repo:
        if not (args.repo / "HEAD").exists() and not (args.repo / ".git").exists():
            p.error(f"{args.repo} は git のリポジトリではない")
        REPO = args.repo
    if args.show:
        # git show --stat と同じ中身。author の名前とメールは出さない。マージは 1 つ目の親との差分
        print(git("show", "--stat", "--diff-merges=first-parent", "--date=short", "--format=%h %cd %s%n%n%b", args.show), end="")
        return 0
    for flag, value in (("--since", args.since), ("--until", args.until), ("--list", args.list)):
        if value and not MONTH_RE.match(value):
            p.error(f"{flag} は YYYY-MM で書く")
    if not has_ref("HEAD") and not args.branch:
        print("コミットがまだないので、書くものはない")
        return 0
    slug = args.github_repo or github_repo()
    if not slug:
        p.error("origin が GitHub でない（change-history は GitHub の PR から作る）。--github-repo OWNER/REPO で言う")
    url = f"https://github.com/{slug}"
    online = not (args.check or args.list)
    cache = load_cache(slug)
    if online and not args.branch:
        cache["default"] = (gh(f"repos/{slug}") or {}).get("default_branch")
    names = args.branch or ([cache["default"]] if cache["default"] else [])
    if not names or (not online and any(n not in cache["prs"] for n in names)):
        flags = "".join(f" --branch {n}" for n in args.branch or [])
        p.error(f"まだ GitHub から取っていない。先に build_history.py {args.folder}{flags} を回す")
    branches = []
    for name in names:
        ref = local_ref(name)
        if not ref:
            p.error(f"ブランチ {name} が手元にない（git fetch origin {name}）")
        branches.append((name, ref))
    items = changes(cache, branches, args.tz, online, slug)
    if online:
        save_cache(cache)
    # --repo のクローン（中央にまとめるとき）は git に入らないので、その中の Decision log へは既定でリンクしない
    DECISIONS.update(decision_logs(args.decision_logs or (None if REPO else pathlib.Path("docs/decision-logs")), args.folder, url))
    months = collections.defaultdict(list)
    for item in items:
        months[item["date"][:7]].append(item)
    # --since・--until は書き直す月を絞る。年表には、その月と前から載っている月を載せる（人が書いた行と要約を消さない）
    shown = sorted(m for m in months if (not args.since or m >= args.since) and (not args.until or m <= args.until))
    if args.list:
        for line in list_lines(months.get(args.list, []), args.depth, url):
            print(line)
        print(f"{args.list}：{len(months.get(args.list, []))} 件。読んだブランチ：{read_from(branches)}")
        return 0
    indexes, summaries = {}, {}
    this_month = datetime.datetime.now(zoneinfo.ZoneInfo(args.tz)).strftime("%Y-%m")
    everything = {key(i): i for i in items}
    for m, month_items in months.items():
        indexes[m] = {key(i): i for i in month_items}
        summary = summary_of(args.folder / f"{m}.md")
        # 依存の更新・リリース・ブランチの取り込みだけの月は、書き手を呼ばずにスクリプトが書く
        # （終わっていない月は、あとから変更が増えるので書き手に任せる）
        if summary in (None, "", EMPTY) and m < this_month and m in shown:
            summary = quiet(month_items) or summary
        summaries[m] = tidy(summary, "month", indexes[m], url, everything)
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
    waiting = [m for m in shown if summaries[m] in (None, "", EMPTY)]
    if waiting:
        print(f"主な変更をまだ書いていない月（{len(waiting)}）：{'、'.join(waiting)}")
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
    try:
        sys.exit(main())
    except BrokenPipeError:  # 読む側が途中でやめた（head など）。黙って終える
        sys.stderr.close()
        sys.exit(0)
