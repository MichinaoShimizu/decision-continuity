---
category: product
checked: 4999eab
---

# 過去の判断を照合する check と、新しい判断を記録する record を足した

## ステータス

Active：decision-log のモードに `check`（変える前に関係する Decision log を照らす）と `record`（人が決めた判断を同じ PR に記録する）がある（`skills/decision-log/references/check-record.md`）。照合は `build_index.py --related` がパスと言葉で当てる。

## 起きたこと

- 2026-10-18 decision-log に `check` と `record` を足し、`build_index.py --related`（パスが重なるか、言葉を含む Decision log を、パスの当たりが多い順に挙げる）と、回し方の `docs/ai-workflow.md`、このリポジトリの `CLAUDE.md` を足した。`allowed-tools` に `git diff` を足した（ブランチ check-record。作成 @MichinaoShimizu）

## 理由

記録あり：レガシーアプリケーションの過去の意思決定を掘り起こして現在に接続し、今後の意思決定の際に照合し、新たな意思決定は記録することで、設計・実装・テストに関わる AI 代替可能性を上げる（@MichinaoShimizu が会話で示した目標、2026-10-18）。

この変更の check で当たった判断：

- DL-2（本文は書き換えず追記で育てる）：record は、同じ流れなら追記で足すので合っている。
- DL-16（指示をぎりぎりまで簡素にした）：モードが 2 つ、参照が 1 つ増える。SKILL.md は約 4.8KB から 5.7KB、参照は 2.6KB 増えた。
- DL-4（確認なしで通すコマンドを読むだけのものに絞る）：`git diff` を足した。`git log` と同じく `--output` で書ける穴は残る（以前、直さないと決めた穴と同じ）。

## 分かっていないこと

- `--related` の言葉での当たりは広い（`check` は `--check` にも当たる）。実際のリポジトリで、当たりすぎて読まれなくならないか（@MichinaoShimizu が使って確かめる）。
- record を、PR を出すたびに AI が自分から回すか。いまは `CLAUDE.md` に書いて促すだけで、フックなどで強制はしていない。
