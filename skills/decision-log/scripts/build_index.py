#!/usr/bin/env python3
"""Decision log のフォルダーの索引 README.md を、フォルダーの Decision log 全部から作り直す。

  build_index.py <フォルダー> [--repo NAME] [--lang ja|en]   README.md を書く
  build_index.py <フォルダー> --check         README.md が最新で、各 Decision log の形が崩れていないかを確かめる
                                             （どちらかが駄目なら終了コード 1）
  build_index.py <フォルダー> --related <パス>... [--words 言葉,…]   パスや言葉に関係する Decision log を挙げる（照合）
  build_index.py <フォルダー> --stale         「ステータス」のリンク先が checked のコミットより後に変わった Decision log を挙げる
                                             （あれば終了コード 1。git が要る）

Decision log は日本語でも英語でも読む（references/format.md）。索引の言語は --lang、
なければいまの索引の言語、なければ多いほうの言語（同じなら日本語）。標準ライブラリだけを使う。
"""
import argparse
import pathlib
import re
import subprocess
import sys

# 正しいファイル名。ここから外れる名前も読むが、直すよう知らせる
STRICT_RE = re.compile(r"^\d{4,}(?:-[a-z0-9-]+)?\.md$")
# (category, 見出し, 中身)。references/format.md の表と同じにする（テストで照らす）
CATEGORIES = [
    ("architecture", "設計・構成", "分割と統合、依存の向き、採用する技術、基盤の移行"),
    ("data", "データの意味・持ち方", "スキーマ、値の意味と単位、保存先、保持期間（個人情報は privacy）"),
    ("security", "認証・権限・セキュリティ", "認証方式、権限の境界、秘密情報、署名と検証、暗号化"),
    ("privacy", "個人情報", "個人情報を集めるか、どこに出す・送る・残すか（ログ・送信先・保持期間）、マスキング"),
    ("compatibility", "互換性・外部との約束", "公開 API、形式、バージョン、廃止"),
    ("reliability", "性能・信頼性", "負荷や障害のときの振る舞い。タイムアウト、リトライ、上限、キャッシュ、縮退"),
    ("release", "リリース・運用", "デプロイの手順、フラグ、環境、監視・アラートと通知先、ログ・トレースの出し方"),
    ("engineering", "開発の決まり", "CI の必須チェック、テストの方針、lint・コードの規約、ブランチの運用"),
    ("cost", "コスト", "インスタンスやプランの大きさ、サンプリングの割合、コストのための削減や上限"),
    ("product", "プロダクトの方針", "仕様の線引き、やらないと決めたこと"),
    ("other", "その他", "どれにも当たらないもの。多ければ分類を見直す"),
]
LABELS = {key: label for key, label, _ in CATEGORIES}
# 英語の索引の (見出し, 中身)
CATEGORIES_EN = {
    "architecture": ("Architecture", "Splitting and merging, direction of dependencies, adopted technology, platform migrations"),
    "data": ("Data meaning and storage", "Schemas, meaning and units of values, where data is stored, retention (personal data is privacy)"),
    "security": ("Authentication, permissions and security", "Authentication methods, permission boundaries, secrets, signing and verification, encryption"),
    "privacy": ("Personal data", "Whether personal data is collected, where it is shown, sent or kept (logs, destinations, retention), masking"),
    "compatibility": ("Compatibility and external contracts", "Public APIs, formats, versions, deprecation"),
    "reliability": ("Performance and reliability", "Behavior under load and failure: timeouts, retries, limits, caches, degradation"),
    "release": ("Release and operations", "Deployment steps, flags, environments, monitoring, alerts and who gets them, logging and tracing"),
    "engineering": ("Engineering rules", "Required CI checks, testing policy, lint and code conventions, branch workflow"),
    "cost": ("Cost", "Instance and plan sizes, sampling rates, cuts and limits made for cost"),
    "product": ("Product policy", "Where the spec draws the line, things decided not to do"),
    "other": ("Other", "Anything that fits none of the above; if there are many, revisit the categories"),
}
# 決まった言葉。日本語と英語のどちらの Decision log も読む。old_today は v0.6 までの「いま」の行、
# old_now は v0.5 までの「起きたこと」の行の「現在：」
WORDS = {
    "ja": dict(happened="起きたこと", reason="理由", retire="**終了**", learned="**分かった**",
               reasons=("記録あり", "推測", "不明"), unknown="不明", status="ステータス",
               old_today=r"^\*\*いま\*\*(?:（[0-9a-f]{7,40}）)?：\S", old_now="現在："),
    "en": dict(happened="What happened", reason="Reason", retire="**Retired**", learned="**Answered**",
               reasons=("Documented", "Inferred", "Unknown"), unknown="Unknown", status="Status",
               old_today=r"^\*\*Now\*\*(?: \([0-9a-f]{7,40}\))?: \S", old_now="Now:"),
}
# ステータスの値。日本語でも英語でも同じ語を使う
STATES = ("Active", "Superseded", "Removed")
STATE_RE = re.compile(r"^(?:- )?(?:Active|Superseded|Removed)(?:：|: )\S")
# 0001.md、0001-auth-pkce.md のほか、0001-Short_Title.md・0001-認証の変更.md と、DL- を付けた DL-1.md・DL-0001-x.md も読む
FILE_RE = re.compile(r"^(?:DL-(\d+)|(\d{4,})(?!-\d{2}-\d{2}))(?:[-_].*)?\.md$", re.I)
FRONT_RE = re.compile(r"\A---\n(.*?)\n---[ \t]*\n+", re.S)
APPEND_RE = re.compile(r"^## (?:追記|Addendum) \d{4}-\d{2}-\d{2}.*$", re.M)
# 「起きたこと」の行。v0.5 までは日付の前に C1 などの番号を付けていたので、それも読む
CLAIM_RE = re.compile(r"^- (?:C\d+ )?(\d{4}-\d{2}-\d{2}) .*$", re.M)
# コミットで固定した行・ファイルのリンク：/blob/<ハッシュ>/<パス>#L12 か #L12-L20（GitLab は /-/blob/）
# 本文に出てくるパス：リンクのほか、`src/payment/client.py` のようなコードの書き方
CODE_PATH_RE = re.compile(r"`([\w.-]+(?:/[\w.-]+)+/?)(?::\d+)?`")
BLOB_RE = re.compile(r"/blob/([0-9a-f]{7,40})/([^\s)#?\]]+)(?:#L(\d+)(?:-L(\d+))?)?")
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", re.M)
REF_DEF_RE = re.compile(r"^\[([^\]]+)\]:[ \t]*(\S+)", re.M)


def field(text, key):
    m = re.search(rf"^{key}:[ \t]*([^#\n]*?)[ \t]*(#.*)?$", text, re.M)
    return m.group(1).strip("'\" ") if m else None


def section(body, heading):
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    return m.group(1) if m else ""


def number(name):
    m = FILE_RE.match(name)
    return int(m.group(1) or m.group(2))


def read_log(path):
    text = path.read_text(encoding="utf-8")
    m = FRONT_RE.match(text)
    front, rest = (m.group(1), text[m.end():]) if m else ("", text)
    title_m = re.match(r"# (.+)\n", rest)
    title = re.sub(r"^\[[^\]]+\]\s*", "", title_m.group(1).strip()) if title_m else path.stem
    parts = APPEND_RE.split(rest)
    body, appends = parts[0], [p.strip() for p in parts[1:]]
    lang = "en" if re.search(r"^## What happened$", body, re.M) else "ja"
    w = WORDS[lang]
    category = field(front, "category") or "other"
    firsts = [note.split("\n", 1)[0] for note in appends]
    retired = any(f.startswith(w["retire"]) for f in firsts)
    learned = any(f.startswith(w["learned"]) for f in firsts)
    checked = field(front, "checked")
    dates = CLAIM_RE.findall(section(body, w["happened"]))
    reason = next((l.strip() for l in section(body, w["reason"]).splitlines() if l.strip()), "")
    problems = []
    if path.name.upper().startswith("DL-"):
        problems.append("ファイル名に DL- を付けない（DL-1 は文中で指すときの書き方）。0001-<名前>.md に変える")
    elif not STRICT_RE.match(path.name):
        problems.append("ファイル名は 0001.md か 0001-<英小文字・数字・ハイフン>.md にする")
    if not front:
        problems.append("フロントマターがない")
    if category not in LABELS:
        problems.append(f"category が分類の一覧にない: {category}")
    if not title_m:
        problems.append("タイトル（# の行）がない")
    if not dates:
        problems.append(f"「## {w['happened']}」に `- YYYY-MM-DD <何が変わったか>` の行がない")
    if checked is not None:
        # checked を持つのは新しい形の Decision log。基準のコミットと「ステータス」の節（前の形なら「いま」の行）を確かめる
        if not re.fullmatch(r"[0-9a-f]{7,40}", checked):
            problems.append("フロントマターの checked が基準のコミットのハッシュ（7〜40 桁）でない")
        first = next((l for l in section(body, w["status"]).splitlines() if l.strip()), "")
        if not STATE_RE.match(first) and not re.search(w["old_today"], rest, re.M):
            problems.append(f"checked があるのに「## {w['status']}」の 1 行目が「{'」「'.join(STATES)}」のどれかで始まっていない")
    if not reason.startswith(w["reasons"]):
        problems.append(f"「## {w['reason']}」の 1 行目が「{'」「'.join(w['reasons'])}」で始まっていない")
    return dict(problems=problems, number=number(path.name), file=path.name, title=title,
                category=category if category in LABELS else "other", retired=retired, lang=lang,
                date=min(dates) if dates else None, checked=checked,
                links=current_links(text, w), text=text,
                status=next((l for l in rest.splitlines() if STATE_RE.match(l) or re.match(w["old_today"], l)), ""),
                paths=sorted({m.group(2) for m in BLOB_RE.finditer(text)} | set(CODE_PATH_RE.findall(text))),
                unknown=reason.startswith(w["unknown"]) and not learned)


def current_links(text, w):
    """ステータスの行（本文と追記）、前の形の「いま」の行、「起きたこと」の行の「現在：」より後にあるリンクを、
    (URL, ハッシュ, パス, 行, 行) で返す。参照の定義（[c12]: <URL>）も引く。"""
    defs = {k.lower(): v for k, v in REF_DEF_RE.findall(text)}
    tails = [l for l in text.splitlines() if STATE_RE.match(l) or re.match(w["old_today"], l)]
    tails += [l.rsplit(w["old_now"], 1)[1] for l in (m.group(0) for m in CLAIM_RE.finditer(text)) if w["old_now"] in l]
    found = set()
    for tail in tails:
        urls = re.findall(r"\]\((\S+?)\)", tail) + [defs.get(k.lower(), "") for k in re.findall(r"\]\[([^\]]+)\]", tail)]
        for url in urls:
            m = BLOB_RE.search(url)
            if m:
                found.add((url,) + m.groups())
    return sorted(found)


def related(logs, paths, words):
    """パス（どちらかがもう一方を含む）か言葉（大文字と小文字を区別しない）で、関係する Decision log を挙げる。"""
    norm = lambda x: x.strip("/").lower()
    def touches(a, b):
        a, b = norm(a), norm(b)
        return a == b or a.startswith(b + "/") or b.startswith(a + "/")
    found = []
    for log in logs:
        on_path = sorted({t for t in paths for q in log["paths"] if touches(t, q)})
        on_word = [f"「{x}」" for x in words if x.lower() in log["text"].lower()]
        if on_path or on_word:
            found.append(((-len(on_path), -len(on_word), order(log)), log, on_path + on_word))
    # パスに当たったものを先に、当たりの多い順に
    return [(log, hits) for _, log, hits in sorted(found, key=lambda x: x[0])]


def git_text(folder, *args):
    """git を回して標準出力を返す。失敗したら None。"""
    result = subprocess.run(["git", "-C", str(folder), *args], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    return result.stdout if result.returncode == 0 else None


def hunks(folder, old, new, path):
    out = git_text(folder, "diff", "-U0", old, new, "--", f":(top){path}")
    if out is None:
        return None
    return [(int(a), int(b or 1), int(c), int(d or 1)) for a, b, c, d in HUNK_RE.findall(out)]


def map_range(changes, lo, hi):
    """old の行の範囲を、diff の塊（hunk）を使って new の行の範囲に写す。範囲に当たる塊は new の側に広げる。"""
    def move(n, end):
        offset = 0
        for a, b, c, d in changes:
            if (b and a + b - 1 < n) or (not b and a < n):
                offset += d - b
            elif b and a <= n <= a + b - 1:
                return max(c, c + d - 1) if end else c
        return n + offset
    return move(lo, False), max(move(lo, False), move(hi, True))


def changed_lines(folder, base, path, first, last):
    """base から HEAD までに path が変わったか。行の範囲があれば、その範囲に当たる変更だけを数える。
    確かめられなければ None。"""
    changes = hunks(folder, base, "HEAD", path)
    if changes is None:
        return None
    if not first:
        return bool(changes) or git_text(folder, "diff", "--quiet", base, "HEAD", "--", f":(top){path}") is None
    lo, hi = first
    for start, count, _, _ in changes:
        if count == 0 and lo <= start < hi:  # 範囲の中に行が足された
            return True
        if count and start <= hi and start + count - 1 >= lo:
            return True
    return False


def stale_links(folder, logs):
    """「現在」のリンク先が、確かめたコミット（checked、なければリンクのハッシュ）より後に変わったもの。"""
    found = []
    origin = (git_text(folder, "remote", "get-url", "origin") or "").strip()
    m = re.search(r"[/:]([^/:]+/[^/]+?)(?:\.git)?/?$", origin)
    repo = m.group(1).lower() if m else None
    for log in logs:
        if log["retired"]:
            continue
        for url, sha, path, first, last in log["links"]:
            if repo and f"/{repo}/" not in url.lower():
                continue  # ほかのリポジトリへのリンクは、このリポジトリの git では確かめられない
            base = log["checked"] or sha
            where = path + (f"#L{first}" + (f"-L{last}" if last else "") if first else "")
            lines = (int(first), int(last or first)) if first else None
            if lines and base != sha:
                # 行の範囲はリンクのコミットで書かれている。確かめたコミットの行に写してから比べる
                moved = hunks(folder, sha, base, path)
                lines = map_range(moved, *lines) if moved is not None else None
                if lines is None:
                    found.append(f"{log['file']}: 確かめられない：{where}（{sha[:7]} か {base[:7]} がない。浅いクローンなら git fetch --unshallow）")
                    continue
            changed = changed_lines(folder, base, path, lines, None)
            if changed is None:
                found.append(f"{log['file']}: 確かめられない：{where}（{base[:7]} がない。浅いクローンなら git fetch --unshallow）")
            elif changed:
                found.append(f"{log['file']}: 要再確認：{where}（{base[:7]} より後に変わった）")
    return list(dict.fromkeys(found))


def line(log, lang="ja"):
    date = log["date"] or ("no date" if lang == "en" else "日付なし")
    mark = (" · reason unknown" if lang == "en" else "・理由不明") if log["unknown"] else ""
    return f"- {date} [DL-{log['number']}]({log['file']}) {log['title']}{mark}"


def order(log):
    return (log["date"] or "9999-99-99", log["number"])


def read_logs(folder):
    return [read_log(p) for p in sorted(folder.glob("*.md")) if FILE_RE.match(p.name)]


def unindexed(folder):
    """番号を読めず、索引に入らない Markdown（README.md を除く）。"""
    return sorted(p.name for p in folder.glob("*.md") if p.name != "README.md" and not FILE_RE.match(p.name))


def build(logs, repo, lang="ja"):
    en = lang == "en"
    out = [f"# Decision logs ({repo})" if en else f"# Decision logs（{repo}）", "",
           "> Rebuilt by decision-log from each Decision log; don't edit it by hand. These are past observations and bind nothing."
           if en else "> decision-log が各 Decision log から作り直す索引。手で直さない。過去の観察であり、何も縛らない。"]
    for key, label, about in CATEGORIES:
        if en:
            label, about = CATEGORIES_EN[key]
        group = sorted((l for l in logs if l["category"] == key and not l["retired"]), key=order)
        if group:
            out += ["", f"## {label} ({key})" if en else f"## {label}（{key}）", "", about, ""] + [line(l, lang) for l in group]
    retired = sorted((l for l in logs if l["retired"]), key=order)
    if retired:
        out += ["", "## Retired" if en else "## 取り下げ", ""] + [line(l, lang) for l in retired]
    return "\n".join(out) + "\n"


def index_lang(folder, logs):
    """索引の言語。いまの索引の言語を保ち、なければ多いほうの言語（同じなら日本語）。"""
    index = folder / "README.md"
    if index.exists():
        title = index.read_text(encoding="utf-8").split("\n", 1)[0]
        if title.startswith("# Decision logs ("):
            return "en"
        if title.startswith("# Decision logs（"):
            return "ja"
    english = sum(l["lang"] == "en" for l in logs)
    return "en" if english > len(logs) - english else "ja"


def duplicates(logs):
    """同じ番号を持つファイル。ほかのブランチと同じ番号でマージされたときに起きる。"""
    seen = {}
    for log in logs:
        seen.setdefault(log["number"], []).append(log["file"])
    return [files for _, files in sorted(seen.items()) if len(files) > 1]


def repo_name(folder):
    """見出しに出すリポジトリ名。いまの索引にあればそれを使い、--repo の有無で索引が変わらないようにする。"""
    index = folder / "README.md"
    if index.exists():
        m = re.match(r"# Decision logs(?:（(.+)）| \((.+)\))\n", index.read_text(encoding="utf-8"))
        if m:
            return m.group(1) or m.group(2)
    url = (git_text(folder, "remote", "get-url", "origin") or "").strip()
    if url:
        return re.sub(r"\.git$", "", url.rstrip("/").split("/")[-1].split(":")[-1])
    top = (git_text(folder, "rev-parse", "--show-toplevel") or "").strip()
    return pathlib.Path(top).name if top else folder.resolve().parent.name


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder", type=pathlib.Path)
    p.add_argument("--repo", help="見出しに出すリポジトリ名（既定はいまの索引の名前、なければ git の origin から）")
    p.add_argument("--lang", choices=("ja", "en"), help="索引の言語（既定はいまの索引の言語、なければ多いほうの言語）")
    p.add_argument("--check", action="store_true", help="書かずに、README.md が最新かを確かめる")
    p.add_argument("--related", nargs="+", metavar="PATH", help="書かずに、このパスに関係する Decision log を挙げる")
    p.add_argument("--words", default="", help="--related と一緒に、この言葉（, で区切る）を含む Decision log も挙げる")
    p.add_argument("--stale", action="store_true", help="書かずに、「ステータス」のリンク先が checked より後に変わった Decision log を挙げる")
    args = p.parse_args()
    if not args.folder.is_dir():
        print(f"{args.folder} がない", file=sys.stderr)
        return 2
    logs = read_logs(args.folder)
    if args.related:
        words = [x.strip() for x in args.words.split(",") if x.strip()]
        found = related(logs, args.related, words)
        for log, hits in found:
            mark = "（取り下げ）" if log["retired"] else ""
            print(f"DL-{log['number']} {log['file']}{mark}：{log['title']}（当たり：{'、'.join(hits)}）")
            if log["status"]:
                print(f"  {log['status']}")
        print(f"関係する Decision log {len(found)} 件" if found else "関係する Decision log はない")
        return 0
    if args.stale:
        found = stale_links(args.folder, logs)
        for f in found:
            print(f)
        print(f"要再確認 {sum('要再確認' in f for f in found)} 件、確かめられない {sum('確かめられない' in f for f in found)} 件"
              "（確かめ直しを頼まれたら、変わったものに追記し checked を進める）" if found else "checked より後に変わった「ステータス」はない")
        return 1 if found else 0
    text = build(logs, args.repo or repo_name(args.folder), args.lang or index_lang(args.folder, logs))
    target = args.folder / "README.md"
    problems = [f"{l['file']}: {p}" for l in logs for p in l["problems"]]
    problems += [f"{name}: ファイル名の先頭に 4 桁の番号がない（0001.md か 0001-<名前>.md）。索引に入らない"
                 for name in unindexed(args.folder)]
    problems += [f"{', '.join(files)}: 番号が重なっている。あとから入れた側のファイルの番号を、いちばん大きい番号の次に振り直す"
                 for files in duplicates(logs)]
    for p in problems:
        print(p)
    if args.check:
        current = target.read_text(encoding="utf-8") if target.exists() else ""
        stale = current != text
        if stale:
            print(f"{target} が古い。build_index.py {args.folder} で作り直す")
        if stale or problems:
            return 1
        print(f"{target} は最新で、{len(logs)} 件の Decision log に形の崩れはない")
        return 0
    target.write_text(text, encoding="utf-8")
    print(f"{target} を作り直した（{len(logs)} 件、形の崩れ {len(problems)} 件）")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
