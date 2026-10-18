# 保存と索引（decision-log の `write`）

## 保存

ファイルを作るか末尾に追記し、索引を作り直し、`--check` が通るまで直す。ブランチを切ってコミットし、PR（MR）を出す。出せなければコミットまでにして、そう伝える。書いたら番号・ファイル・PR のリンクを伝え、「マージで保存される」と伝える。書けないときは貼れる形で返し、「まだ保存していません」と書く。

## 索引

索引の `README.md` は手で書かない。リポジトリのルートで、スクリプトを相対パスで 1 つずつ呼ぶ（Kiro なら `.kiro/skills/…`）。

```sh
python3 .claude/skills/decision-log/scripts/build_index.py <置き場所>           # 索引を作り直す
python3 .claude/skills/decision-log/scripts/build_index.py <置き場所> --check   # 索引が最新で、形の崩れがなければ終了コード 0
python3 .claude/skills/decision-log/scripts/build_index.py <置き場所> --stale   # 「現在」が checked より後に変わったものを挙げる（recheck.md）
```

索引は分類ごとに、いちばん古い日付の順に並ぶ。理由が「不明」のままのものに `・理由不明`、「終了」の追記があるものは「取り下げ」に入る。

ほかのブランチと `README.md` が衝突したら、既定のブランチを取り込み、番号が重なっていれば自分の側のファイルの番号を振り直してから、スクリプトで作り直す。
