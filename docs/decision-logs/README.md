# Decision logs（decision-continuity）

> decision-log が各 Decision log から作り直す索引。手で直さない。過去の観察であり、何も縛らない。

## 設計・構成（architecture）

分割と統合、依存の向き、採用する技術、基盤の移行

- 2026-10-03 [DL-1](0001-record-storage.md) 記録の置き場所が Discussions から records/ を経て、置き場所を持たない汎用ツールになった
- 2026-10-16 [DL-3](0003-kiro-reader.md) Kiro の対応が、薄い入口の方式から、reader を JSON と Markdown の両方で置く形になった
- 2026-10-18 [DL-13](0013-delegation.md) 洗い出しと読むことをサブエージェントに任せ、メインの会話はコマンドをほとんど回さない形になった

## 認証・権限・セキュリティ（security）

認証方式、権限の境界、秘密情報、署名と検証、暗号化

- 2026-10-17 [DL-4](0004-command-permissions.md) 確認なしで通すコマンドが、読むだけのものに絞られていった

## 個人情報（privacy）

個人情報を集めるか、どこに出す・送る・残すか（ログ・送信先・保持期間）、マスキング

- 2026-10-19 [DL-18](0018-change-history-releases-and-names.md) change-history の一覧から人の名前を外し、定型のリリースを主な変更に入れないことにした

## 互換性・外部との約束（compatibility）

公開 API、形式、バージョン、廃止

- 2026-10-16 [DL-8](0008-index-format.md) Decision log の形と索引の作り方が、手書きの表からスクリプト生成の日付順の一覧になった
- 2026-10-16 [DL-9](0009-rename-decision-log.md) スキルの名前が reverse-adr から decision-log になった

## リリース・運用（release）

デプロイの手順、フラグ、環境、監視・アラートと通知先、ログ・トレースの出し方

- 2026-10-17 [DL-11](0011-distribution.md) 入れ方が、ファイルを写すだけから、プラグインと install.sh の 1 行になった
- 2026-10-17 [DL-12](0012-versioning.md) 版の番号を変更の断片から決め、マージでタグとリリースを出す形になった

## 開発の決まり（engineering）

CI の必須チェック、テストの方針、lint・コードの規約、ブランチの運用

- 2026-10-15 [DL-10](0010-evals-ci.md) 評価と CI が、旧キット向けのものから decision-log 向けに作り直された

## プロダクトの方針（product）

仕様の線引き、やらないと決めたこと

- 2026-10-03 [DL-2](0002-append-only.md) 記録の本文は書き換えず、追記で育てる形になった
- 2026-10-16 [DL-5](0005-no-test-evidence.md) CI の結果をテスト証拠に数えたが、約 40 分後にテストの確認自体をやめた
- 2026-10-16 [DL-6](0006-reason-source.md) 理由の確かさを、書かれていた場所で分けるようになった
- 2026-10-16 [DL-7](0007-investigation-method.md) 候補の絞り込みが、タイトルとファイル名から、差分の洗い出しを含む形になった
- 2026-10-17 [DL-15](0015-english.md) 頼まれたら Decision log を英語で書けるようになった
- 2026-10-18 [DL-14](0014-evidence-and-detail.md) 理由の証拠を広く読み、起きたことに値の前後を書く形になった
- 2026-10-18 [DL-16](0016-simplify.md) スキルと Decision log の形を、ぎりぎりまで簡素にした
- 2026-10-18 [DL-17](0017-check-and-record.md) 過去の判断を照合する check と、新しい判断を記録する record を足した
