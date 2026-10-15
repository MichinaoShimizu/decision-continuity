## 決定の記録

このリポジトリの名前（決定の記録の `repos` で使う）：`<repo-name>`

決定の記録は、`.claude/skills/decision-record/STORE` に書いたリポジトリの GitHub Discussions にある。このリポジトリには ADR や索引のファイルを置かない。

- 設計、データの意味、保存先、公開 API・互換性、認証・権限、個人情報・セキュリティ、監視・ログ、プロダクトの方針に触れる変更をする前に、`.claude/skills/adr-guard/SKILL.md` で関係する決定を確かめる。見た目だけの変更やふつうの修正では要らない。
- 決定を変えたいとき、新しく決めたいときは、`.claude/skills/decision-record/SKILL.md` の「書く」で提案中の DR を作る。有効にするのは人。
- 過去の変更の理由を知りたいときは、`.claude/skills/reverse-adr/SKILL.md` で Decision log を起こす。
- 記録を読めなかったときは、「関係する決定はない」とせず、読めなかったと書く。
