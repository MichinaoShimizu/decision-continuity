#!/usr/bin/env python3
"""マージされた変更の一覧を、月ごとの Markdown に書き出す（change-history の 1 段目）。

  build_history.py <フォルダー> [--branch develop --branch main] [--depth 2] [--since YYYY-MM] [--until YYYY-MM]   書き出す
  build_history.py <フォルダー> --check                                                                         最新か確かめる（古ければ終了コード 1）
  build_history.py <フォルダー> --list YYYY-MM                                                                  その月の全変更を出す（書かない）
  build_history.py <フォルダー> --show <コミット>                                                               変えたファイルを出す（書かない）

どれも --repo <クローン> で、いまのディレクトリでないリポジトリを読める（複数のリポジトリをまとめる build_many.py が使う）。

月ごとの YYYY-MM.md（主な変更の表）と、年表を兼ねた索引の README.md を書く。日付は YYYY-MM-DD、月は YYYY-MM で書く。
全変更の一覧はファイルに書かず、--list で出す（主な変更を選ぶ材料）。マージコミットの下には、取り込んだ側の
コミット（PR の中のコミットや、release/1.2 などの読んでいないブランチでマージされた PR）を並べる。
以前の timeline.md があれば、年ごとの要点を README.md に移して消す。

リポジトリのルート（--repo なら、そのクローン）で動かす。手元の git の --first-parent の履歴を読む。ネットワークに出るのは、PR の作成者を取る gh api だけ
（--no-github で止める）。
開発の本流と本番の適用先のようにブランチが分かれていても取りこぼさないよう、--branch を言わなければ
長く続くブランチ（main・master・develop・development・dev・production）を全部読む。手元のものは古いことがあるので、
origin/ にあればそちらを読む。
どのブランチにも入ったコミットは 1 つにまとめ、ブランチ間のマージ（develop から main へのリリースなど）には印を付ける。
PR の番号はマージコミットの件名（Merge pull request #12）か、squash の件名の末尾（(#12)）から取る。
年表の件数は PR と直接のコミットの数（PR の中のコミットは数えず、保守ブランチから取り込んだ変更は数える）。変更のなかった月も
「変更なし」の行で載せる。依存の更新・リリースだけの終わった月は、主な変更に「- 目立った変更なし（…のみ）」と書く。
各月の「## 主な変更」と、README.md の各年の要点・各月の要約は、作り直しても残す（人か AI が書く）。月の主な変更は 1 つの表、
年の要点は「- 」の行で、どちらも分類に分けない（前の形の ### <分類> の見出しと説明の文は外す）。主な変更の表の日付と Author は、
PR の列の変更から埋め直す（前の形の「- 概要（#12）」の行は表に移す）。
決まった形でなければ、どこが崩れているかを出し、終了コード 1 を返す。標準ライブラリだけを使う。
主な変更の表の PR の列には、その PR を挙げた Decision log（docs/decision-logs/ の 0001-*.md。--decision-logs で変える）への
リンクも、あれば PR の後ろに添える（[DL-3](…)）。
人はアカウント名（@login）で、Author の列にだけ書く。gh が使えれば、PR の作成者を GitHub から取る（gh api の GET だけ）。
取れない変更は、フォークからのマージの件名（Merge pull request #12 from alice/fix）か、noreply のメール（.mailmap を
通す）から取る。名前（git の author 名）は書き出さない。
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
import zoneinfo

# 番号のないもの（Merge pull request from GHSA-…：セキュリティ修正のマージ）も、本文の 1 行目をタイトルにする
# 2 つ目のグループは、取り込んだブランチのリポジトリの持ち主（フォークなら PR の作成者）
MERGE_RE = re.compile(r"^Merge pull request (?:#(\d+) )?from (?:([A-Za-z0-9-]+)/)?\S+")
SQUASH_RE = re.compile(r"^(.*?)\s*\(#(\d+)\)\s*$")
# PR を通さないブランチの同期（Merge branch '3.0.x'、Merge remote-tracking branch 'origin/stable'）
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
# 読んだブランチどうしのマージ。中身は元のブランチの一覧に 1 件ずつ出る
BETWEEN = "（{} から取り込み）"
LONG_LIVED = ("main", "master", "develop", "development", "dev", "production")
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
# GitHub の noreply のメール（12345+alice@users.noreply.github.com）からアカウント名を取る。取れなければ UNKNOWN
NOREPLY_RE = re.compile(r"^(?:\d+\+)?([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\[bot\])?)@users\.noreply\.github\.com$", re.I)
UNKNOWN = "—"
CELL_RE = re.compile(r"(?<!\\)\|")
OLD_LINE_RE = re.compile(r"^- (.*)（([^（）]*)）$")
# 書くことのない月：取り込みだけ、リリースだけ、依存の更新だけ、など。理由は（…のみ）に書く
NOTHING_RE = re.compile(r"^- 目立った変更なし（[^（）\n]+のみ）$")
# 書き手を呼ばずにスクリプトが「目立った変更なし（…のみ）」と書く変更の印と、（…のみ）に書く名前（この順に並べる）
QUIET = {DEPS: "依存の更新", RELEASE: "リリース"}
BETWEEN_NAME = "ブランチの取り込み"
# 変更のなかった月（年表の表の行）と年（年の要点）
NONE = "変更なし"
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
# PR の番号ごとの、その PR を挙げた Decision log の (番号, 月のファイルからの相対パス)。PR の列に PR の後ろに添える
DECISIONS = {}
# Decision log のファイル（0001-retry-limit.md）と、その中の PR（[PR #101][pr101] の文か、<origin>/pull/101 のリンク）
DL_FILE_RE = re.compile(r"^(\d{4})-[^/]*\.md$")
DL_PR_RE = re.compile(r"\bPR #(\d+)")
# origin の持ち主（https://github.com/<owner>/...）。フォークからのマージを見分ける
OWNER = None
# フォークからのマージでわかった、メールから @login。同じメールで noreply でない変更の Author に使う。
# 1 つのメールに 2 人以上が当たるか、同じリポジトリのブランチからのマージ（メンテナーが別の人の PR に足したコミットなど）
# にも出るメールは使わない（None を入れて印にする）
LEARNED = {}
# 読むリポジトリ（--repo）。None ならいまのディレクトリ
REPO = None


def git(*args, tz=None, stdin=None):
    env = dict(os.environ, TZ=tz) if tz else None
    out = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                         input=stdin, cwd=REPO)
    if out.returncode != 0:
        sys.exit(f"git {args[0]} が失敗した: {out.stderr.strip()}")
    return out.stdout


def repo_url():
    """origin から https://github.com/<owner>/<repo> の形を作る。作れなければ None。"""
    out = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, cwd=REPO)
    m = re.search(r"(?:github\.com[:/])([^/]+/[^/]+?)(?:\.git)?/?$", out.stdout.strip())
    return f"https://github.com/{m.group(1)}" if m else None


def area(path, depth):
    """変更したファイルの置き場所。depth 段までのフォルダー。ルートのファイルは「（ルート）」。"""
    parts = path.split("/")[:-1][:depth]
    return "/".join(parts) + "/" if parts else "（ルート）"


def has_ref(ref):
    return subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], capture_output=True, cwd=REPO).returncode == 0


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
    out = subprocess.run(["git", "rev-parse", "--git-common-dir"], capture_output=True, text=True, cwd=REPO)
    found = pathlib.Path(REPO or ".") / out.stdout.strip()  # 相対パスで返るので、読むリポジトリからたどる
    return found / "decision-continuity-prs.json" if out.returncode == 0 and url else None


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
    elif item["author"] == UNKNOWN and len(found := LEARNED.get(item.get("email", "").lower(), {None})) == 1 \
            and None not in found:
        item["author"], = found
    return item


def decision_logs(logs, folder, url):
    """Decision log の置き場所から、PR の番号 → [(DL の番号, 月のファイルからの相対パス)]。置き場所がなければ空。"""
    found = collections.defaultdict(list)
    if not logs or not logs.is_dir():
        return found
    pulls = re.compile(rf"{re.escape(url)}/pull/(\d+)\b") if url else None
    for path in sorted(logs.iterdir()):
        m = DL_FILE_RE.match(path.name)
        if not m:
            continue
        text = path.read_text(encoding="utf-8")
        prs = set(DL_PR_RE.findall(text)) | set(pulls.findall(text) if pulls else ())
        where = pathlib.PurePath(os.path.relpath(path, folder)).as_posix()
        for pr in prs:
            found[pr].append((int(m.group(1)), where))
    return found


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
            item.update(sha=sha, date=date, email=email, author=account(email), branches=[name],
                        files=[f for f in files.splitlines() if f.strip()])
            between = item["between"]
            if len(parents) > 1:
                tips[sha] = parents[1]
                if not between:
                    item["range"] = f"{parents[0]}..{parents[1]}"
            seen[sha] = item
            items.append(item)
    credit(seen, tips)
    return sorted((by_pr(i) for i in items), key=lambda i: i["date"])


def credit(items, tips, learn=True):
    """マージコミットの Author を決める。フォークからのマージは件名のフォークの持ち主（PR の作成者）、
    ほかは取り込んだ側の先頭（2 つ目の親）のコミットのメールから。learn なら、フォークの持ち主を先頭のコミットのメールと
    結びつけて覚える（本流のマージだけから覚え、読む順で Author が変わらないようにする）。"""
    if not tips:
        return
    out = git("log", "--no-walk=unsorted", "--stdin", f"--format=%H{FIELD}%aE", stdin="\n".join(set(tips.values())) + "\n")
    emails = dict(line.split(FIELD, 1) for line in out.splitlines() if FIELD in line)
    for sha, tip in tips.items():
        item, email = items[sha], emails.get(tip, "")
        item["email"] = email
        known = email and learn and not NOREPLY_RE.match(email)
        head = item.get("head")
        if head and OWNER and head.lower() != OWNER.lower():
            item["author"] = f"@{head}"
            if known:
                LEARNED.setdefault(email.lower(), set()).add(item["author"])
        else:
            item["author"] = account(email)
            if known:
                LEARNED.setdefault(email.lower(), set()).add(None)


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
                inner.update(sha=sha, date=item["date"], email=email, author=account(email), branches=item["branches"], files=[])
                if len(parents) > 1:
                    tips[sha] = parents[1]
                found.append(inner)
            credit({i["sha"]: i for i in found}, tips, learn=False)
        item["inside"] = [by_pr(i) for i in found]
    return item["inside"]


def key(item):
    return f"#{item['pr']}" if item["pr"] else item["sha"]


def parse(subject, body, parents, branch, shas):
    """件名と本文から PR の番号とタイトルを取り、印を付ける。"""
    m = MERGE_RE.match(subject)
    if m and len(parents) > 1:
        item = dict(pr=m.group(1), head=m.group(2), merged_pr=True, title=next((l.strip() for l in body.splitlines() if l.strip()), subject))
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
    elif DEPS_RE.match(item["title"]):
        item["title"] = DEPS + item["title"]
    return item


def size(item):
    """1 つの変更（--first-parent の 1 コミット）が入れた変更の数。ブランチ間のマージは元のブランチで数えるので 0。
    PR のマージは 1 と、中でマージされた別の PR の数。PR を通さないブランチの取り込み（Merge branch '8.1.x'）は、
    取り込んだ側の変更（そのブランチでマージされた PR と、直接のコミット）の数。その中のブランチの取り込みは数えない
    （本流を保守ブランチに戻したマージなど。中身はほかで数えている）。"""
    if item["between"]:
        return 0
    if not item.get("range"):
        return 1
    if item.get("merged_pr"):
        return 1 + len({i["pr"] for i in inside(item) if i["pr"] and i["pr"] != item["pr"]})
    return len([i for i in inside(item) if not i["title"].startswith(SYNC)]) or 1


def count(items):
    return sum(size(i) for i in items)


def quiet(items):
    """依存の更新・ブランチ間の取り込み・リリースだけの月なら、「- 目立った変更なし（…のみ）」の文。ほかがあれば None。"""
    kinds = {BETWEEN_NAME if i["between"] else next((n for mark, n in QUIET.items() if i["title"].startswith(mark)), None)
             for i in items}
    if not kinds or None in kinds:
        return None
    return f"- 目立った変更なし（{'・'.join(n for n in (*QUIET.values(), BETWEEN_NAME) if n in kinds)}のみ）"


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
        inner = inside(item)
        # 1 コミットだけの PR（中のコミットが同じタイトル）は、同じ行を 2 度出さない
        if len(inner) == 1 and inner[0]["title"] == item["title"] and inner[0]["pr"] in (None, item["pr"]):
            inner = []
        lines += [f"  - {i['title']}（{link(i, url)}、{i['author']}）" for i in inner]
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
    """日付は最初の変更の日、Author は変更ごとのアカウント名（重なりは 1 つ）。GitHub から取れなかった変更があり、
    書いてある Author のほうが取れていない（—）が少なければ、書いてある方を残す（gh が使えるかどうかで --check の
    結果が変わらないように。取れるようになった名前は、— の代わりに入る）。"""
    authors = "、".join(dict.fromkeys(i["author"] for i in items))
    if written and not all(i["pr"] in PR_AUTHORS for i in items) \
            and written.split("、").count(UNKNOWN) < authors.split("、").count(UNKNOWN):
        authors = written
    date = next((i["date"] for i in items if i["date"]), "")
    # PR を挙げた Decision log は、PR の後ろに番号の順に添える（参照の数には入れない）
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
            rows.append(row(parts[1], found, url, parts[3]) if found else line)
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
    """main（origin/main）、develop（origin/develop）の形。"""
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
            out.append(f"| [{month}]({month}.md) | {count(months[month])} | {point or NO_POINT} |")
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
    p.add_argument("--show", metavar="コミット", help="書かずに、そのコミットの件名・本文と変えたファイルを出す（人の名前は出さない）")
    p.add_argument("--repo", type=pathlib.Path, help="読むリポジトリ（既定はいまのディレクトリ）")
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
    for name in args.branch or []:
        if not has_ref(name):
            p.error(f"ブランチ {name} が見つからない")
    branches = [(name, name) for name in args.branch] if args.branch else long_lived()
    if branches == [("HEAD", "HEAD")] and not has_ref("HEAD"):
        print("コミットがまだないので、書くものはない")
        return 0
    global OWNER
    url = repo_url()
    OWNER = url.split("/")[3] if url else None
    if not args.no_github:
        # --list（書き手が月ごとに呼ぶ）は問い合わせず、覚えておいた分だけを使う
        use_prs(github_prs(url, args.github, online=not args.list))
    # --repo のクローン（中央にまとめるとき）は git に入らないので、その中の Decision log へは既定でリンクしない
    DECISIONS.update(decision_logs(args.decision_logs or (None if REPO else pathlib.Path("docs/decision-logs")), args.folder, url))
    months = collections.defaultdict(list)
    for item in changes(args.tz, branches):
        months[item["date"][:7]].append(item)
    # --since・--until は書き直す月を絞る。年表には、その月と前から載っている月を載せる（人が書いた行と要約を消さない）
    shown = sorted(m for m in months if (not args.since or m >= args.since) and (not args.until or m <= args.until))
    if args.list:
        for line in list_lines(months.get(args.list, []), args.depth, url, len(branches) > 1):
            print(line)
        print(f"{args.list}：{count(months.get(args.list, []))} 件。読んだブランチ：{read_from(branches)}")
        return 0
    indexes, summaries = {}, {}
    this_month = datetime.datetime.now(zoneinfo.ZoneInfo(args.tz)).strftime("%Y-%m")
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
        # 依存の更新・リリース・ブランチ間の取り込みだけの月は、書き手を呼ばずにスクリプトが書く
        # （終わっていない月は、あとから変更が増えるので書き手に任せる）
        if summary in (None, "", EMPTY) and m < this_month and m in shown:
            summary = quiet(items) or summary
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
    total = sum(count(months[m]) for m in shown)
    print(f"{args.folder}：{len(shown)} か月、{total} 件（書き換え {len(stale)} ファイル、形の崩れ {len(broken)} 件）。"
          f"読んだブランチ：{read_from(branches)}")
    return 1 if broken else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # 読む側が途中でやめた（head など）。黙って終える
        sys.stderr.close()
        sys.exit(0)
