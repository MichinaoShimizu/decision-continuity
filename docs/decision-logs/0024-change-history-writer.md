---
category: architecture
checked: 9d3616d
---

# change-history の月ごとの表を、専用のサブエージェントに任せることにした

## ステータス

Active：change-history の SKILL.md の手順 2 は、「まだ」の月を古い順に 12 か月ずつの回に分け、月ごとに `change-history-writer` を 1 回の応答でまとめて呼ぶ（Kiro は 4 つまで）。書き手は月のファイルだけを書いて要約の 1 文を返し、年表の `README.md` にはメインの会話が入れる（`skills/change-history/SKILL.md` の手順 2、`agents/claude/change-history-writer.md`）。

## 起きたこと

- 2026-10-19 それまで「月が多ければ既定のサブエージェントに任せる」としていた月ごとの表を、専用のサブエージェント `change-history-writer` に任せることにした。Kiro 用の `.md`・`.json` も置き、`--list` と `git show` を確認なしで通し、書き込みを `docs/change-history/*.md` に限った（ブランチ change-history-writer。作成 @MichinaoShimizu）

## 理由

記録あり：「Change historyもサブエージェントで並列かしたほうがよい？」という問いに、Kiro で確認が減る、書き方が揃う、大きなリポジトリでメインの会話に結果がたまって止まりにくくなる、と答え、作る案に @MichinaoShimizu が「はい」と答えた（会話 2026-10-19）。並べた書き手が年表の `README.md` を同時に書き換えてぶつからないよう、書き手は月のファイルだけを書き、要約は返すだけにした（Claude の判断）。1 回 12 か月は Claude の案（decision-log の 1 回 20 件に近い大きさ）。

## 分かっていないこと

- Kiro の `toolsSettings.write.allowedPaths` で、書き込みが確認なしに通るか、置き場所を変えたときにどうなるかは、実機で確かめていない（@MichinaoShimizu が確かめる）。
- 1 回 12 か月がちょうどよいか。実際のリポジトリで確かめる。
