# 変更の断片

利用者に見える変更をする PR は、`CHANGELOG.md` を直さず、ここにファイルを足す。同時に開いている PR どうしがぶつからない。リリースの PR（`sh tools/release.sh`）が `sh tools/changelog.sh` で全部の断片を `CHANGELOG.md` にまとめ、断片を消す。

## 形

変更の種類ごとに 1 ファイル：`changes/<短い名前>.<節>.md`

- `<短い名前>`：英小文字・数字・`-`。英小文字か数字で始める。ブランチ名など（`reader-kiro`・`index-format`）。ファイルを分けるだけで、CHANGELOG には出ない
- `<節>`：`added`・`changed`・`deprecated`・`removed`・`fixed`・`security` のどれか。`### Added`・`### Changed` などになる
- 中身：「- 」で始まる項目を 1 つ以上。リリースノートにそのまま出る文で書く。項目の続きの行と、入れ子の項目は空白 2 つで字下げする。空の行は消える。見出しや項目の外の文は書かない
- スキルやサブエージェントの名前・入れ方・Decision log の形や置き場所など、使っている人の手元を壊す変更は、項目を `BREAKING:` で始める。0.x の間は minor、1.0 からは major が上がる

種類の違う変更をする PR は、節ごとにファイルを分ける（例：`reader-kiro.added.md` と `reader-kiro.fixed.md`）。

```markdown
- decision-log: 索引の見出しの直下に、分類の中身を書く
  - 古い索引は、次に `write` したときに作り直される
```

## ツールがすること

- `sh tools/changelog.sh --check`：ここのファイルを全部確かめ、おかしいものを名指しする。CI が回す
- `sh tools/next-version.sh`：ここの断片と `CHANGELOG.md` の `## Unreleased` を合わせて、次の版を決める（決まりは [docs/release.md](../docs/release.md)）
- `sh tools/changelog.sh`：断片を `## Unreleased` にまとめる。すでにある項目が先、断片はファイル名の順にその後ろ。節は Added・Changed・Deprecated・Removed・Fixed・Security の順。何度動かしても同じ結果になる
- `sh tools/changelog.sh --release vX.Y.Z`：同じようにまとめ、節の名前を `## vX.Y.Z - <今日（UTC）>` にする。`tools/release.sh` が使う

内部だけの変更、テスト、文書だけの変更、評価（`evals/`）や Decision log（`docs/decision-logs/`）の更新には断片は要らない。
