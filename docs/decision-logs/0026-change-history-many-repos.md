---
category: architecture
checked: a5033e3
---

# change-history で、一覧にした複数のリポジトリの年表を中央のリポジトリにまとめられるようにした

## ステータス

Active：`build_many.py` は `repos.txt` の各リポジトリを `.cache/change-history/<owner>/<repo>/` に bare のクローン（`--filter=blob:none`）として取り、`build_history.py --repo` で `docs/change-history/<owner>/<repo>/` に年表を書き、`docs/change-history/README.md` に年ごとのリポジトリ別の要点と月 × リポジトリの件数の表を書く（`skills/change-history/scripts/build_many.py` の `overview`）。単位はリポジトリで、いまのリポジトリを対象にする使い方はそのまま残す。書き手は `build_history.py --show` で変えたファイルを見る（`agents/claude/change-history-writer.md`）。

## 起きたこと

- 2026-10-20 `build_many.py` と手順（`skills/change-history/references/many-repos.md`）を足し、`build_history.py` に `--repo`・`--show` を足した。書き手は `git show --stat` の代わりに `--show` を使い、Kiro の書き手は `docs/change-history/*/*/*.md` にも書ける。README に使い方を書いた（ブランチ change-history-many。作成 @MichinaoShimizu）

## 理由

記録あり：「いまみたいに作業リポジトリのみを対象にする以外に、リスト化された複数リポジトリを対象にし、中央管理する使い方も良いと思うがどうか」に、年表は中央に向き、decision-log は照合（`--related`・`--stale`）がコードの隣にあることを前提にするので各リポジトリに残す、と答えた。単位をアプリケーション（複数のリポジトリやモノレポのパスをまとめる）にする案も挙げたが、@MichinaoShimizu が「リポジトリ単位でいいや」と決め、「実際他のリポジトリにインストールする際の可搬性は意識した上、リードミーも更新して。作業リポジトリを対象にする使い方も維持して」と求めた（会話 2026-10-20）。

ほかの案：アプリケーション単位は取らなかった（上のとおり）。月 × リポジトリの行を全部並べる全体の表は取らなかった（リポジトリと年が増えると読めない。Claude の判断）。書き手に `cd`・`git -C` を許す案は取らなかった（確認なしで通すコマンドの決まりに合わない）ので、`build_history.py` が `--repo` で別のクローンを読み、`--show` で変えたファイルを出す（Claude の判断）。`--show` は author の名前とメールを出さない（DL-18）。

## 分かっていないこと

- 中央のリポジトリで decision-log をまとめる使い方が要るか（いまは各リポジトリに置く前提）。
- 対象が数十のリポジトリになったとき、書き手の回（リポジトリごとに 12 か月ずつ）の進め方で足りるか。実際の規模で確かめる。
- Kiro の `allowedPaths` の `docs/change-history/*/*/*.md` が、確認なしで通るかは実機で確かめていない（@MichinaoShimizu が確かめる）。
