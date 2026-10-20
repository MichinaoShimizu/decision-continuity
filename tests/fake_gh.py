"""テストで PATH の先頭に置く偽の gh。FAKE_GH の JSON から、build_history.py が使う GitHub の応答を返す。

JSON の形：{"default": "main", "fail": false,
           "pulls": [{"number": 2, "base": "main", "login": "bob", "merged_at": "2025-02-01T00:00:00Z", "sha": "…", "title": "…"}],
           "commits": {"<ハッシュ>": ["<アカウント>", "<PR の番号か空>", "<PR の base>"]}}
"repos": {"owner/repo": {…同じ形…}} があれば、リポジトリごとにそちらを使う。
呼ばれた引数は FAKE_GH に .log を付けたファイルに 1 行ずつ足す。
"""
import json
import os
import re
import sys

FIXTURE = os.environ["FAKE_GH"]
with open(FIXTURE + ".log", "a", encoding="utf-8") as log:
    log.write(" ".join(sys.argv[1:]) + "\n")
with open(FIXTURE, encoding="utf-8") as f:
    data = json.load(f)
args = sys.argv[1:]
if data.get("fail") or args[:1] != ["api"]:
    print("HTTP 502: Bad Gateway", file=sys.stderr)
    sys.exit(1)
path = args[1]


def repo(slug):
    return data.get("repos", {}).get(slug, data)


if path == "graphql":
    query = next(a for a in args if a.startswith("query="))
    data = repo("/".join(re.search(r'repository\(owner: "([^"]+)", name: "([^"]+)"\)', query).groups()))
    found = {}
    for alias, sha in re.findall(r'(c\d+): object\(oid: "([0-9a-f]+)"\)', query):
        login, pr, base = data.get("commits", {}).get(sha) or ["", "", ""]
        found[alias] = {"author": {"user": {"login": login} if login else None},
                        "associatedPullRequests": {"nodes": [{"number": int(pr), "mergedAt": "2000-01-01T00:00:00Z",
                                                              "baseRefName": base}] if pr else []}}
    print(json.dumps({"data": {"repository": found}}))
    sys.exit(0)
m = re.fullmatch(r"repos/([^/]+/[^/?]+)(?:/pulls\?(.*))?", path)
if not m:
    print(f"HTTP 404: {path}", file=sys.stderr)
    sys.exit(1)
data = repo(m.group(1))
m = re.fullmatch(r"repos/[^/]+/[^/?]+(?:/pulls\?(.*))?", path)
if m.group(1) is None:
    print(json.dumps({"default_branch": data.get("default", "main")}))
    sys.exit(0)
query = dict(kv.split("=", 1) for kv in m.group(1).split("&"))
pulls = [p for p in data.get("pulls", []) if p.get("base", "main") == query["base"]]
pulls.sort(key=lambda p: p.get("updated") or p.get("merged_at") or "", reverse=True)
page, per = int(query["page"]), int(query["per_page"])
print(json.dumps([{"number": p["number"], "user": {"login": p.get("login")}, "merged_at": p.get("merged_at"),
                   "merge_commit_sha": p.get("sha"), "title": p.get("title", "")} for p in pulls[(page - 1) * per:page * per]]))
