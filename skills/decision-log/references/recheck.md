# 確かめ直す（decision-log の `recheck`）

頼まれたときだけ回す。コードが変わるたびに回すものではない。

1. `python3 .claude/skills/decision-log/scripts/build_index.py <置き場所> --stale`（Kiro なら `.kiro/skills/…`）で、「現在」のリンク先が `checked` のコミットより後に変わったものを挙げる。行の範囲付きのリンクは、その範囲に当たる変更だけを数える。「確かめられない」は浅いクローンなど、コミットが手元にないとき。
2. 挙がった C 行を `HEAD` で確かめる（`git show HEAD:<パス>`、`git log --first-parent --format='%h %ad %s' --date=short-local <checked>..HEAD -- <パス>`）。ファイルが変わっても中身が同じなら、何も足さない。
3. 状態が変わった Decision log にだけ追記を足し、フロントマターの `checked` を `HEAD` の短いハッシュに直す。変わらなかったものは `checked` だけ直す。

   ```markdown
   ## 追記 2026-01-20（書いた人）

   **いま**（def5678）：上限は 7。理由は分かっていない。

   - C1 は置き換え済みになった：[PR #160][pr160] で 5 から 7 になった（322 日後）

   [pr160]: <PR #160 の URL>
   ```

4. 索引を作り直し、`--check` と `--stale` が通ることを確かめる（[save.md](save.md)）。

`audit` では書かず、手順 1〜2 の結果と追記の下書きを返す。
