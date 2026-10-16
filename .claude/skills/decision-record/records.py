#!/usr/bin/env python3
"""決定の記録（記録のリポジトリの records/ にある Markdown）を読み書きする。標準ライブラリと git だけを使う。

  records.py index [--repo NAME] [--all]   探すための一覧（タイトル・状態・repos・paths・keywords）
  records.py show NUMBER                   本文と追記全部、この記録を参照している記録
  records.py config                        記録のリポジトリの config.yaml
  records.py create --category NAME --title TITLE --body-file FILE   新しい記録のファイルを作る（FILE 先頭のフロントマターはファイルの先頭に置く）
  records.py comment NUMBER --body-file FILE   記録の末尾に追記する（FILE が - なら標準入力）
  records.py check [--base REF]            ファイル名・番号の重複・追記だけで育っているかを確かめる

記録のリポジトリは --store、環境変数 DR_STORE、このスキルを置いたリポジトリの records/、
このファイルの隣の STORE の順で決める。値は手元のパスか owner/repo。owner/repo なら読むときだけ
キャッシュにクローンする。書く（create・comment）には手元のクローンが要る。
環境変数 DR_SNAPSHOT に JSON のパスがあれば、ファイルではなくそれを読み、書き込みはしない（評価用）。
読めなかったときは終了コード 2。「記録がない」と区別するため。
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
RECORDS = "records"
# フォルダー名 → 種類の名前。番号はフォルダーをまたいで一つの通し番号。
FOLDERS = {"decisions": "Decisions", "decision-flows": "Decision flows",
           "decision-logs": "Decision logs", "questions": "Q&A"}
ALIASES = {"q-a": "questions", "qa": "questions"}
CATEGORIES = ("Decisions", "Decision flows", "Decision logs")
# 番号は種類をまたいだ通し番号。参照は種類の接頭辞を付けて書く（DR-42）。GitHub の #42 の自動リンクとぶつけないため。
PREFIXES = {"Decisions": "DR", "Decision flows": "DF", "Decision logs": "DL", "Q&A": "Q"}
ID_RE = re.compile(r"^(?:(?:DR|DF|DL|Q)-)?0*(\d+)$", re.I)
LIST_KEYS = ("repos", "paths", "keywords")
SCALAR_KEYS = ("kind", "status", "entry", "domain", "touches_sensitive", "superseded_by", "category")
ROUTING_MARK = "**探し方を更新**"
DECIDED_MARK = "**決まった**"
PREMISE_MARK = "**前提が崩れた**"
CLOSED_MARK = "**終了**"
CATEGORY_MARK = "**分類を更新**"
LEARNED_MARK = "**分かった**"
BECAME_MARK = "**決定になった**"
FILE_RE = re.compile(r"^(\d{4,})(?:-[a-z0-9-]+)?\.md$")
TITLE_RE = re.compile(r"\A# (.+)\n")
# 記録データはファイル先頭の YAML フロントマター（--- と --- で挟む）。
FRONT_RE = re.compile(r"\A---\n(.*?)\n---[ \t]*\n+", re.S)
APPEND_RE = re.compile(r"^## 追記 (\d{4}-\d{2}-\d{2})(?:（(.*)）)?$", re.M)


class Unreadable(Exception):
    pass


def rid(category, number):
    return f"{PREFIXES.get(category, '')}-{number}"


def record_number(text):
    """DL-17、17、0017 のどれでも番号として受け取る。"""
    m = ID_RE.match(text.strip())
    if not m:
        raise argparse.ArgumentTypeError(f"番号は DR-42 か 42 の形: {text}")
    return int(m.group(1))


def run(argv, cwd=None):
    try:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Unreadable(f"{argv[0]} を実行できない: {exc}")
    if proc.returncode != 0:
        raise Unreadable(proc.stderr.strip() or f"{' '.join(argv[:2])} が終了コード {proc.returncode} で失敗")
    return proc.stdout


def clone(slug):
    """owner/repo を読むためだけのキャッシュにクローンし、毎回最新にそろえる。ここには書かない。"""
    cache = pathlib.Path(os.environ.get("XDG_CACHE_HOME") or pathlib.Path.home() / ".cache")
    path = cache / "decision-records" / slug.replace("/", "__")
    if (path / ".git").exists():
        run(["git", "-C", str(path), "fetch", "--depth", "1", "origin", "HEAD"])
        run(["git", "-C", str(path), "reset", "--hard", "FETCH_HEAD"])
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--depth", "1", f"https://github.com/{slug}.git", str(path)])
    return path


def store(args, writing=False):
    """記録のリポジトリのルート（手元のパス）を返す。"""
    value = args.store or os.environ.get("DR_STORE")
    if not value:
        root = HERE.parents[2]
        if (root / RECORDS).is_dir():
            return root
        if (HERE / "STORE").exists():
            value = (HERE / "STORE").read_text(encoding="utf-8").strip()
    if not value:
        raise Unreadable("記録のリポジトリが分からない（--store にパスか owner/repo、または STORE ファイルを用意する）")
    path = pathlib.Path(value).expanduser()
    if path.is_dir():
        return path.resolve()
    if re.fullmatch(r"[\w.-]+/[\w.-]+", value):
        if writing:
            raise Unreadable(f"{value} を手元にクローンし、そのパスを --store か DR_STORE で渡す（書くには手元のクローンが要る）")
        return clone(value)
    raise Unreadable(f"記録のリポジトリ {value} が見つからない")


def folder(category):
    want = category.strip().lower()
    want = ALIASES.get(want, want)
    for name, label in FOLDERS.items():
        if want in (name, label.lower()):
            return name
    raise Unreadable(f"種類 {category} がない（{', '.join(FOLDERS)} から選ぶ）")


def split_front(text):
    """先頭のフロントマターと、その後ろ（タイトルから）に分ける。フロントマターがなければ None。"""
    m = FRONT_RE.match(text)
    return (m.group(1), text[m.end():]) if m else (None, text)


def parse_file(path, category):
    front, text = split_front(path.read_text(encoding="utf-8"))
    m = TITLE_RE.match(text)
    title = m.group(1).strip() if m else path.stem
    rest = text[m.end():] if m else text
    parts = APPEND_RE.split(rest)
    body = re.sub(r"\n---\s*$", "", parts[0].strip()).strip()
    comments = []
    for i in range(1, len(parts), 3):
        comments.append(dict(author=parts[i + 1], created_at=parts[i], url=None, body=parts[i + 2].strip()))
    return dict(number=int(FILE_RE.match(path.name).group(1)), title=title, url=None, front=front,
                closed=False, state_reason=None, category=category, author=None, body=body, comments=comments)


def files(root):
    for name, label in FOLDERS.items():
        for path in sorted((root / RECORDS / name).glob("*.md")):
            if FILE_RE.match(path.name):
                yield path, label


def fetch(args):
    snapshot = os.environ.get("DR_SNAPSHOT")
    if snapshot:
        try:
            return json.loads(pathlib.Path(snapshot).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise Unreadable(f"DR_SNAPSHOT を読めない: {exc}")
    root = store(args)
    if not (root / RECORDS).is_dir():
        raise Unreadable(f"{root} に {RECORDS}/ がない")
    recs = []
    for path, label in files(root):
        try:
            rec = parse_file(path, label)
        except (OSError, UnicodeDecodeError) as exc:
            raise Unreadable(f"{path} を読めない: {exc}")
        rec["url"] = str(path.relative_to(root))
        recs.append(rec)
    return recs


def parse_value(raw):
    raw = raw.strip()
    if raw.startswith("["):
        inner = raw.strip("[]").strip()
        return [x.strip().strip("'\"") for x in inner.split(",") if x.strip()] if inner else []
    if raw in ("", "null", "~"):
        return None
    return raw.strip("'\"")


def parse_fields(text, keys):
    """トップレベルの `key: value` だけを読む。リストは一行の [a, b] で書く決まり。"""
    found = {}
    for line in text.splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*?)\s*(#.*)?$", line)
        if m and m.group(1) in keys:
            found[m.group(1)] = parse_value(m.group(2))
    return found


def record_data(rec):
    """フロントマターを読む。なければ本文の ```yaml ブロック（前の形）を読む。"""
    text = rec.get("front")
    if text is None:
        m = re.search(r"```ya?ml\s*\n(.*?)```", rec["body"], re.S)
        text = m.group(1) if m else ""
    return parse_fields(text, LIST_KEYS + SCALAR_KEYS)


def effective(rec):
    """本文の記録データに、追記の更新を古い順に重ねる。"""
    data = record_data(rec)
    notes = []
    closed, reason = rec["closed"], rec.get("state_reason")
    for c in rec.get("comments", []):
        body = c["body"].lstrip()
        first = body.split("\n", 1)[0].replace("*", "").strip()
        for mark in (ROUTING_MARK, DECIDED_MARK, PREMISE_MARK, CLOSED_MARK, CATEGORY_MARK, LEARNED_MARK, BECAME_MARK):
            if first.startswith(mark.strip("*")):
                body = mark + body.split(mark.strip("*"), 1)[1]
        day = c["created_at"][:10]
        if body.startswith(ROUTING_MARK):
            data.update(parse_fields(body, LIST_KEYS))
            notes.append(f"探し方を更新 {day}")
        elif body.startswith(DECIDED_MARK):
            data["status"] = "accepted"
            notes.append(f"決まった {day}" + (f" by {c['author']}" if c.get("author") else ""))
        elif body.startswith(CATEGORY_MARK):
            data.update(parse_fields(body, ("category",)))
            notes.append(f"分類を更新 {day}")
        elif body.startswith(LEARNED_MARK):
            notes.append(f"分かった {day}")
        elif body.startswith(BECAME_MARK):
            notes.append(f"決定になった {day}")
        elif body.startswith(PREMISE_MARK):
            notes.append(f"前提が崩れた {day}")
        elif body.startswith(CLOSED_MARK):
            closed = True
            reason = "OUTDATED" if "置き換え" in body.split("\n", 1)[0] else "RESOLVED"
    if rec["category"] == "Decision logs":
        state = "記録" if not closed else "取り下げ"
    elif closed:
        state = {"OUTDATED": "終了（置き換え）", "DUPLICATE": "終了（重複）"}.get(reason, "終了")
    else:
        state = "有効" if data.get("status") == "accepted" else "提案中"
    return data, state, notes, closed


def cmd_index(args):
    rows, others = [], []
    for rec in sorted(fetch(args), key=lambda r: r["number"]):
        if rec["category"] not in CATEGORIES:
            continue
        data, state, notes, closed = effective(rec)
        if closed and not args.all:
            continue
        repos = data.get("repos") or []
        line = f"{rid(rec['category'], rec['number'])} {state} [{rec['category']}] {rec['title']}"
        if args.repo and not (args.repo in repos or "all" in repos):
            others.append(line)
            continue
        parts = [line]
        for key in LIST_KEYS:
            parts.append(f"{key}: {', '.join(data.get(key) or []) or '-'}")
        parts.append(f"entry: {data.get('entry') or '-'}")
        if data.get("category"):
            parts.append(f"category: {data['category']}")
        if data.get("touches_sensitive") == "true":
            parts.append("sensitive")
        if notes:
            parts.append("; ".join(notes))
        rows.append(" | ".join(parts))
    head = f"このリポジトリ（{args.repo}）か全リポジトリ（all）に関係する記録" if args.repo else "記録"
    print(f"## {head}: {len(rows)} 件")
    print("\n".join(rows) if rows else "（なし）")
    if args.repo:
        print(f"\n## ほかの記録（タイトルだけ。意味で関係しそうなら show で読む）: {len(others)} 件")
        print("\n".join(others) if others else "（なし）")


def cmd_show(args):
    recs = fetch(args)
    rec = next((r for r in recs if r["number"] == args.number), None)
    if rec is None:
        print(f"{args.number} 番は見つからない")
        return 3
    data, state, notes, _ = effective(rec)
    print(f"{rid(rec['category'], rec['number'])} {rec['title']}\n{rec['url']}\n種類: {rec['category']} / 状態: {state}"
          + (f" / 立てた人: {rec['author']}" if rec.get("author") else ""))
    if notes:
        print("更新: " + "; ".join(notes))
    ref = re.compile(rf"\b(?:DR|DF|DL|Q)-0*{args.number}(?!\d)")
    linked = [rid(r["category"], r["number"]) for r in recs if r is not rec
              and any(ref.search(t) for t in [r["body"]] + [c["body"] for c in r.get("comments", [])])]
    if linked:
        print("参照している記録: " + ", ".join(linked))
    if rec.get("front") is not None:
        print("\n---\n" + rec["front"] + "\n---")
    print("\n" + rec["body"])
    for c in rec.get("comments", []):
        who = f" {c['author']}" if c.get("author") else ""
        print(f"\n--- 追記 {c['created_at'][:10]}{who}\n{c['body']}")
    return 0


def cmd_config(args):
    if os.environ.get("DR_SNAPSHOT"):
        path = pathlib.Path(os.environ["DR_SNAPSHOT"]).with_name("config.yaml")
        print(path.read_text(encoding="utf-8") if path.exists() else "（評価用の config.yaml なし）")
        return
    path = store(args) / "config.yaml"
    if not path.exists():
        raise Unreadable(f"{path} がない")
    print(path.read_text(encoding="utf-8"))


def read_body(path):
    return sys.stdin.read() if path == "-" else pathlib.Path(path).read_text(encoding="utf-8")


def today():
    import datetime
    return datetime.date.today().isoformat()


def author(root):
    try:
        return run(["git", "-C", str(root), "config", "user.name"]).strip() or None
    except Unreadable:
        return None


def cmd_create(args):
    body = read_body(args.body_file).strip()
    title = " ".join(args.title.split())
    if os.environ.get("DR_SNAPSHOT"):
        print(f"（評価中のため書いていない。書く内容）\ncreate [{args.category}] {title}\n\n{body}")
        return 0
    name = folder(args.category)
    root = store(args, writing=True)
    numbers = [int(FILE_RE.match(p.name).group(1)) for p, _ in files(root)]
    number = max(numbers, default=0) + 1
    slug = f"-{args.slug}" if args.slug else ""
    path = root / RECORDS / name / f"{number:04d}{slug}.md"
    if not FILE_RE.match(path.name):
        raise Unreadable(f"--slug は英小文字・数字・ハイフンだけ: {args.slug}")
    path.parent.mkdir(parents=True, exist_ok=True)
    front, body = split_front(body + "\n")
    head = f"---\n{front}\n---\n\n" if front is not None else ""
    path.write_text(f"{head}# {title}\n\n{body.strip()}\n", encoding="utf-8")
    print(f"{rid(FOLDERS[name], number)} {path.relative_to(root)}")
    return 0


def cmd_comment(args):
    body = read_body(args.body_file).strip()
    if os.environ.get("DR_SNAPSHOT"):
        print(f"（評価中のため書いていない。書く内容）\ncomment {args.number}\n\n{body}")
        return 0
    root = store(args, writing=True)
    path = next((p for p, _ in files(root) if int(FILE_RE.match(p.name).group(1)) == args.number), None)
    if path is None:
        raise Unreadable(f"{args.number} 番のファイルがない")
    who = args.author or author(root)
    text = path.read_text(encoding="utf-8").rstrip("\n")
    sep = "" if APPEND_RE.search(text) else "\n\n---"
    path.write_text(f"{text}{sep}\n\n## 追記 {today()}{f'（{who}）' if who else ''}\n\n{body}\n", encoding="utf-8")
    print(f"{rid(FOLDERS[path.parent.name], args.number)} {path.relative_to(root)} に追記した")
    return 0


def cmd_check(args):
    root = store(args, writing=True)
    problems, seen = [], {}
    for path in sorted((root / RECORDS).glob("*/*.md")):
        rel = path.relative_to(root).as_posix()
        if path.parent.name not in FOLDERS:
            problems.append(f"{rel}: フォルダーは {', '.join(FOLDERS)} のどれか")
            continue
        m = FILE_RE.match(path.name)
        if not m:
            problems.append(f"{rel}: ファイル名は 0042.md か 0042-slug.md（英小文字・数字・ハイフン）")
            continue
        number = int(m.group(1))
        if number in seen:
            problems.append(f"{rel}: 番号 {number} が {seen[number]} と重なっている。新しいほうの番号を振り直す")
        seen.setdefault(number, rel)
        if not TITLE_RE.match(split_front(path.read_text(encoding="utf-8"))[1]):
            problems.append(f"{rel}: 一行目は「# タイトル」（フロントマターがあればその直後）")
    if args.base:
        listed = run(["git", "-C", str(root), "ls-tree", "-r", "--name-only", args.base, "--", RECORDS])
        for rel in listed.split():
            if not FILE_RE.match(pathlib.PurePosixPath(rel).name):
                continue
            old = run(["git", "-C", str(root), "show", f"{args.base}:{rel}"])
            new = root / rel
            if not new.exists():
                problems.append(f"{rel}: 消したり名前を変えたりしない（閉じるときは「{CLOSED_MARK}」を追記する）")
            elif not new.read_text(encoding="utf-8").startswith(old.rstrip("\n")):
                problems.append(f"{rel}: 本文や過去の追記を書き換えている。末尾への追記だけにする")
    for p in problems:
        print(p)
    print(f"{len(seen)} 件の記録を確かめた。" + (f"直すところ {len(problems)} 件" if problems else "問題なし"))
    return 1 if problems else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--store", help="記録のリポジトリ（手元のパスか owner/repo）")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("index"); s.add_argument("--repo"); s.add_argument("--all", action="store_true")
    s = sub.add_parser("show"); s.add_argument("number", type=record_number)
    sub.add_parser("config")
    s = sub.add_parser("create"); s.add_argument("--category", required=True); s.add_argument("--title", required=True)
    s.add_argument("--body-file", required=True); s.add_argument("--slug", help="ファイル名に添える英語（任意）")
    s = sub.add_parser("comment"); s.add_argument("number", type=record_number); s.add_argument("--body-file", required=True)
    s.add_argument("--author", help="追記した人（既定は git の user.name）")
    s = sub.add_parser("check"); s.add_argument("--base", help="比べる基準（例：origin/main）")
    args = p.parse_args()
    try:
        return {"index": cmd_index, "show": cmd_show, "config": cmd_config, "create": cmd_create,
                "comment": cmd_comment, "check": cmd_check}[args.cmd](args) or 0
    except Unreadable as exc:
        print(f"記録を読めなかった（書けなかった）: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
