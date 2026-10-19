---
category: product
checked: eff793b
---

# change-history の年表を README.md にまとめ、日付を YYYY-MM-DD にそろえた

## ステータス

Active：`build_history.py` は月ごとの `YYYY-MM.md` と、年表を兼ねた `README.md` だけを書き、以前の `timeline.md` は年の要点を移して消す（`skills/change-history/scripts/build_history.py` の `readme_page`）。一覧の日付は `YYYY-MM-DD`、表の月は `YYYY-MM` で、SKILL.md も年の要点の期間を `2024-03〜2024-06` の形で書くとする。

## 起きたこと

- 2026-10-19 索引の `README.md`（月・件数・主な変更を書いたか）と年表の `timeline.md`（年の要点と、月・件数・主な変更の 1 行目）を、`README.md` 1 つにまとめた。一覧の日付を `05-02` から `2025-05-02` に、表の月を `5 月` から `2025-05` に変えた（ブランチ change-history-branches。作成 @MichinaoShimizu）

## 理由

記録あり：「日付は常にyyyy-mm-dd 統一して」「Timeline.mdの内容をReadmeにして良さそう」（@MichinaoShimizu、会話 2026-10-19）。直前に、2 つのファイルの区別が分かりにくいという問い（「Timeline.mdとReadmeの区別何」）があり、索引の列名を変えた（PR #95）が、年表の表は索引の中身（月と件数、まだ書いていない月）をすべて含んでいた。

## 分かっていないこと

- 月が数百あるリポジトリで、`README.md` 1 つが長くなりすぎないか（年ごとの見出しで足りるか）。
- `timeline.md` へのリンクを外から張っている利用者がいるか。いれば、消さずに `README.md` への案内を残す案もある（@MichinaoShimizu に聞く）。

## 追記 2026-10-19

**分かった**（2026-10-19）：「`timeline.md` へのリンクを外から張っている利用者がいるか。いれば、消さずに `README.md` への案内を残す案もある」

- 2026-10-19 @MichinaoShimizu が「タイムライン消す」と決めた（会話）。案内は残さず、`build_history.py` は年の要点を `README.md` に移して `timeline.md` を消す。リンクが切れることは断片の `BREAKING:` で知らせる
