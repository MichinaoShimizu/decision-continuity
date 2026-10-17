# 版とリリース

kiroku と同じ仕組みで版を付ける。PR は変更の断片を足すだけで、版の番号はリリースの PR で中身から決まり、その PR をマージするとタグとリリースが出る。

## 変更の記録

利用者に見える変更をする PR は、`CHANGELOG.md` ではなく `changes/<短い名前>.<節>.md` に書く（形は [changes/README.md](../changes/README.md)）。`sh tools/changelog.sh --check` で確かめられ、CI も回す。`CHANGELOG.md` の `## Unreleased` に直接書いた項目も数えられ、残る。

## 版の番号

まだ出していない変更（`changes/` の断片と `## Unreleased`）から、Semantic Versioning で決める。`sh tools/next-version.sh` が次の版を出す。

| まだ出していない変更 | 上げるところ |
|---|---|
| `BREAKING:` で始まる項目がある（スキルやサブエージェントの名前、入れ方、Decision log の形や置き場所など、使っている人の手元を壊す変更） | 1.0 からは major、0.x の間は minor |
| Added の変更がある（`*.added.md`・`### Added`） | minor |
| それ以外（Changed・Fixed・Removed など） | patch |

Claude Code のプラグインは `.claude-plugin/plugin.json` の `version` で更新を見分ける。この値はリリースの PR だけが変え、`CHANGELOG.md` のいちばん上の版と同じでなければテストが落ちる。

## リリースの PR

変更のない作業ツリーで：

```sh
sh tools/release.sh
```

`tools/release.sh` は push もタグ付けもしない。次のことをする。

1. 作業ツリーに変更があれば止まる（コミットするか、別のブランチに置く。素の `git stash` は使わない）
2. `origin/main` を取ってきて `next-version.sh` で版を決め、`origin/main` から `claude/release-vX.Y.Z` を作る
3. `sh tools/changelog.sh --release vX.Y.Z` で、断片と `## Unreleased` を `## vX.Y.Z - <今日（UTC）>` にまとめ、まとめた断片を消す
4. `.claude-plugin/plugin.json` の `version` を `X.Y.Z` にする
5. テストと `sh tools/release-notes.sh vX.Y.Z` を回し、`Release vX.Y.Z` をコミットして、次の手順（push と PR）を出す。`DC_RELEASE_TRAILER` を指定すると、その値をコミットの最後の行に足す（エージェントが作るときの `Co-Authored-By:` など）

テストが落ちたら、リリースのブランチの上で、コミットしていない状態で止まる。そこで直してコミットし、出てきた次の手順を手で続ける。節を手で作るなら `sh tools/changelog.sh --release vX.Y.Z` を動かす（何度動かしても同じ。PR を作ったあとに main に入った断片は、もう一度動かすと同じ節に足される）。

PR を main にマージすると、`.github/workflows/tag.yml` がいちばん上の節の版でタグを打ち、その節をリリースノートにして GitHub のリリースを作る。手でタグを打つ必要はない。うまくいかなかったときは Actions → Tag → Run workflow でやり直せる。

いちばん上の節の番号が中身と合わないとき、`plugin.json` の版と合わないとき、リリースの PR に断片が残っているとき（その版に入らない）は、CI と Tag が止まる。
