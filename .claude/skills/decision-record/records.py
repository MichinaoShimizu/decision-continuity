#!/usr/bin/env python3
"""決定の記録（GitHub Discussions）を読み書きする。標準ライブラリと gh だけを使う。

  records.py index [--repo NAME] [--all]   探すための一覧（タイトル・状態・repos・paths・keywords）
  records.py show NUMBER                   本文とコメント全部
  records.py config                        記録のリポジトリの config.yaml
  records.py create --category NAME --title TITLE --body-file FILE
  records.py comment NUMBER --body-file FILE

記録のリポジトリは --store、環境変数 DR_STORE、このファイルの隣の STORE の順で決める。
環境変数 DR_SNAPSHOT に JSON のパスがあれば、GitHub ではなくそれを読み、書き込みはしない（評価用）。
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
CATEGORIES = ("Decisions", "Decision flows", "Decision logs")
LIST_KEYS = ("repos", "paths", "keywords")
SCALAR_KEYS = ("kind", "status", "entry", "domain", "touches_sensitive", "superseded_by")
ROUTING_MARK = "**探し方を更新**"
DECIDED_MARK = "**決まった**"
PREMISE_MARK = "**前提が崩れた**"

QUERY = """query($owner:String!,$name:String!,$after:String){repository(owner:$owner,name:$name){
discussions(first:50,after:$after){pageInfo{hasNextPage endCursor}nodes{number title url closed stateReason
category{name} author{login} body comments(first:100){nodes{author{login} createdAt url body}}}}}}"""


class Unreadable(Exception):
    pass


def store(args):
    value = args.store or os.environ.get("DR_STORE")
    if not value and (HERE / "STORE").exists():
        value = (HERE / "STORE").read_text(encoding="utf-8").strip()
    if not value or "/" not in value:
        raise Unreadable("記録のリポジトリが分からない（--store owner/repo か STORE ファイルを用意する）")
    return value.split("/", 1)


def gh(argv, stdin=None):
    try:
        proc = subprocess.run(["gh", *argv], input=stdin, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Unreadable(f"gh を実行できない: {exc}")
    if proc.returncode != 0:
        raise Unreadable(proc.stderr.strip() or f"gh が終了コード {proc.returncode} で失敗")
    return proc.stdout


def fetch(args):
    snapshot = os.environ.get("DR_SNAPSHOT")
    if snapshot:
        try:
            return json.loads(pathlib.Path(snapshot).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise Unreadable(f"DR_SNAPSHOT を読めない: {exc}")
    owner, name = store(args)
    nodes, after = [], None
    while True:
        argv = ["api", "graphql", "-f", f"query={QUERY}", "-F", f"owner={owner}", "-F", f"name={name}"]
        if after:
            argv += ["-F", f"after={after}"]
        try:
            page = json.loads(gh(argv))["data"]["repository"]["discussions"]
        except (KeyError, TypeError, ValueError) as exc:
            raise Unreadable(f"GitHub の応答を読めない: {exc}")
        for n in page["nodes"]:
            nodes.append(dict(number=n["number"], title=n["title"], url=n["url"], closed=n["closed"],
                              state_reason=n.get("stateReason"), category=n["category"]["name"],
                              author=(n.get("author") or {}).get("login"), body=n["body"],
                              comments=[dict(author=(c.get("author") or {}).get("login"), created_at=c["createdAt"],
                                             url=c["url"], body=c["body"]) for c in n["comments"]["nodes"]]))
        if not page["pageInfo"]["hasNextPage"]:
            return nodes
        after = page["pageInfo"]["endCursor"]


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


def record_data(body):
    m = re.search(r"```ya?ml\s*\n(.*?)```", body, re.S)
    return parse_fields(m.group(1), LIST_KEYS + SCALAR_KEYS) if m else {}


def effective(rec):
    """本文の記録データに、コメントの更新を古い順に重ねる。"""
    data = record_data(rec["body"])
    notes = []
    for c in rec.get("comments", []):
        body = c["body"].lstrip()
        first = body.split("\n", 1)[0].replace("*", "").strip()
        for mark in (ROUTING_MARK, DECIDED_MARK, PREMISE_MARK):
            if first.startswith(mark.strip("*")):
                body = mark + body.split(mark.strip("*"), 1)[1]
        if body.startswith(ROUTING_MARK):
            data.update(parse_fields(body, LIST_KEYS))
            notes.append(f"探し方を更新 {c['created_at'][:10]}")
        elif body.startswith(DECIDED_MARK):
            data["status"] = "accepted"
            notes.append(f"決まった {c['created_at'][:10]} by {c['author']}")
        elif body.startswith(PREMISE_MARK):
            notes.append(f"前提が崩れた {c['created_at'][:10]}")
    if rec["category"] == "Decision logs":
        state = "記録" if not rec["closed"] else "取り下げ"
    elif rec["closed"]:
        state = {"OUTDATED": "終了（置き換え）", "DUPLICATE": "終了（重複）"}.get(rec.get("state_reason"), "終了")
    else:
        state = "有効" if data.get("status") == "accepted" else "提案中"
    return data, state, notes


def cmd_index(args):
    rows, others = [], []
    for rec in sorted(fetch(args), key=lambda r: r["number"]):
        if rec["category"] not in CATEGORIES or (rec["closed"] and not args.all):
            continue
        data, state, notes = effective(rec)
        repos = data.get("repos") or []
        line = f"#{rec['number']} {state} [{rec['category']}] {rec['title']}"
        if args.repo and not (args.repo in repos or "all" in repos):
            others.append(line)
            continue
        parts = [line]
        for key in LIST_KEYS:
            parts.append(f"{key}: {', '.join(data.get(key) or []) or '-'}")
        parts.append(f"entry: {data.get('entry') or '-'}")
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
    rec = next((r for r in fetch(args) if r["number"] == args.number), None)
    if rec is None:
        print(f"#{args.number} は見つからない")
        return 3
    data, state, notes = effective(rec)
    print(f"#{rec['number']} {rec['title']}\n{rec['url']}\nカテゴリ: {rec['category']} / 状態: {state} / 立てた人: {rec['author']}")
    if notes:
        print("更新: " + "; ".join(notes))
    print("\n" + rec["body"])
    for c in rec.get("comments", []):
        print(f"\n--- コメント {c['created_at'][:10]} {c['author']} {c['url']}\n{c['body']}")
    return 0


def cmd_config(args):
    if os.environ.get("DR_SNAPSHOT"):
        path = pathlib.Path(os.environ["DR_SNAPSHOT"]).with_name("config.yaml")
        print(path.read_text(encoding="utf-8") if path.exists() else "（評価用の config.yaml なし）")
        return
    owner, name = store(args)
    print(gh(["api", f"repos/{owner}/{name}/contents/config.yaml", "-H", "Accept: application/vnd.github.raw"]))


def write(args, mutation_text):
    if os.environ.get("DR_SNAPSHOT"):
        print("（評価中のため書いていない。書く内容）\n" + mutation_text)
        return 0
    return None


def cmd_create(args):
    body = pathlib.Path(args.body_file).read_text(encoding="utf-8")
    if write(args, f"create [{args.category}] {args.title}\n\n{body}") is not None:
        return 0
    owner, name = store(args)
    q = "query($o:String!,$n:String!){repository(owner:$o,name:$n){id discussionCategories(first:25){nodes{id name slug}}}}"
    repo = json.loads(gh(["api", "graphql", "-f", f"query={q}", "-F", f"o={owner}", "-F", f"n={name}"]))["data"]["repository"]
    want = args.category.lower()
    cat = next((c for c in repo["discussionCategories"]["nodes"] if want in (c["name"].lower(), c["slug"].lower())), None)
    if cat is None:
        raise Unreadable(f"カテゴリ {args.category} がない（GitHub の画面で作る）")
    m = "mutation($r:ID!,$c:ID!,$t:String!,$b:String!){createDiscussion(input:{repositoryId:$r,categoryId:$c,title:$t,body:$b}){discussion{number url}}}"
    out = json.loads(gh(["api", "graphql", "-f", f"query={m}", "-F", f"r={repo['id']}", "-F", f"c={cat['id']}",
                         "-f", f"t={args.title}", "-f", f"b={body}"]))
    d = out["data"]["createDiscussion"]["discussion"]
    print(f"#{d['number']} {d['url']}")
    return 0


def cmd_comment(args):
    body = pathlib.Path(args.body_file).read_text(encoding="utf-8")
    if write(args, f"comment #{args.number}\n\n{body}") is not None:
        return 0
    owner, name = store(args)
    q = "query($o:String!,$n:String!,$k:Int!){repository(owner:$o,name:$n){discussion(number:$k){id}}}"
    did = json.loads(gh(["api", "graphql", "-f", f"query={q}", "-F", f"o={owner}", "-F", f"n={name}",
                         "-F", f"k={args.number}"]))["data"]["repository"]["discussion"]["id"]
    m = "mutation($d:ID!,$b:String!){addDiscussionComment(input:{discussionId:$d,body:$b}){comment{url}}}"
    out = json.loads(gh(["api", "graphql", "-f", f"query={m}", "-F", f"d={did}", "-f", f"b={body}"]))
    print(out["data"]["addDiscussionComment"]["comment"]["url"])
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--store", help="記録のリポジトリ owner/repo")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("index"); s.add_argument("--repo"); s.add_argument("--all", action="store_true")
    s = sub.add_parser("show"); s.add_argument("number", type=int)
    sub.add_parser("config")
    s = sub.add_parser("create"); s.add_argument("--category", required=True); s.add_argument("--title", required=True)
    s.add_argument("--body-file", required=True)
    s = sub.add_parser("comment"); s.add_argument("number", type=int); s.add_argument("--body-file", required=True)
    args = p.parse_args()
    try:
        return {"index": cmd_index, "show": cmd_show, "config": cmd_config,
                "create": cmd_create, "comment": cmd_comment}[args.cmd](args) or 0
    except Unreadable as exc:
        print(f"記録を読めなかった（書けなかった）: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
