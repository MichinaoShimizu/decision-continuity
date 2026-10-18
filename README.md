# decision-continuity

意思決定の経緯を途切れさせないための、スキルとサブエージェントの集まり。組み合わせて使う。Claude Code と Kiro で動く。

| 名前 | 種類 | すること |
|---|---|---|
| [decision-log](skills/decision-log/SKILL.md) | スキル | コードのリポジトリの履歴から、何が起きたか・なぜか・何が分かっていないかを Decision log に起こす |
| [decision-log-planner](agents/claude/decision-log-planner.md) | サブエージェント | decision-log の範囲と候補を手元の git で洗い、読み手への分担を返す |
| [decision-log-reader](agents/claude/decision-log-reader.md) | サブエージェント | decision-log の候補を分類ごとに並行に読み、決まった形で返す |

## decision-log の流れ

```mermaid
flowchart TD
    H[("PR・issue・コミット・コード")] --> P["decision-log-planner<br>手元の git で候補を絞り、分担を決める"]
    P --> R["decision-log-reader<br>分類ごとに並行に読む"]
    R --> V["decision-log<br>主張ごとに確かめる<br>履歴（PR・差分）と現在（基準のコミット）"]
    V --> D[("Decision log<br>起きたこと・理由・分かっていないこと")]
    D -- "理由が不明" --> Q["知っていそうな人に聞く"]
    Q -- "分かった（追記）" --> D
```

## 入れ方

どれか 1 つを選ぶ。

### Claude Code のプラグイン

スキルとサブエージェントが両方入る。更新もプラグインで受け取る。

```text
/plugin install decision-continuity --marketplace MichinaoShimizu/decision-continuity
```

Claude Code 2.1.275 より前なら `/plugin marketplace add MichinaoShimizu/decision-continuity` のあと `/plugin install decision-continuity@decision-continuity`。スキルは `decision-continuity:decision-log`、サブエージェントは `decision-continuity:decision-log-planner` と `decision-continuity:decision-log-reader` という名前になる。

### npx skills

[npx skills](https://github.com/vercel-labs/skills) で、Claude Code と Kiro にスキルだけを入れる。

```sh
npx skills add MichinaoShimizu/decision-continuity --skill decision-log -a claude-code -a kiro-cli
```

入るのは `main` の最新。版を決めて入れるなら `MichinaoShimizu/decision-continuity#v0.2.0` のようにタグを付ける。

サブエージェントは入らないので、使うなら下の表の 2 行目を写す。写さなくても、decision-log は洗い出しを自分で回し、読むのは既定のサブエージェントに切り替えて動く（Kiro では、そのぶんコマンドごとに確認が出やすい）。

### 手で写す

| 写すもの | Claude Code | Kiro |
|---|---|---|
| [skills/decision-log/](skills/decision-log/SKILL.md) | `.claude/skills/decision-log/` | `.kiro/skills/decision-log/` |
| [agents/](agents/) の decision-log-planner と decision-log-reader | `claude/` の `.md` を `.claude/agents/` | `kiro/` の `.json` と `.md` を両方 `.kiro/agents/` |

## 使い方

使うときは「認証まわりがなぜこうなったか、履歴から起こして」のように頼む。既定は読むだけ（`audit`）で、書くのは `write` と頼んだときだけ。

### Claude Code で確認を減らす

スキルの `allowed-tools` がサブエージェント（decision-log-planner・decision-log-reader）にも効くかは、公式ドキュメントに書かれていない。サブエージェントのコマンドに毎回確認が出るときは、読むだけのコマンドを `.claude/settings.json` に足す（メインの会話とサブエージェントの両方に効く）。書くコマンド（`git commit`・`git push`・`gh pr create` など）は足さない。

```json
{
  "permissions": {
    "allow": [
      "Bash(git log *)", "Bash(git show *)", "Bash(git grep *)", "Bash(git rev-parse *)",
      "Bash(git remote get-url *)", "Bash(TZ=Asia/Tokyo git log *)",
      "Bash(gh pr view *)", "Bash(gh issue view *)", "Bash(gh release view *)",
      "Bash(glab mr view *)", "Bash(glab issue view *)",
      "Bash(gh api repos/*)"
    ],
    "deny": [
      "Bash(gh api *-X*)", "Bash(gh api *--method*)", "Bash(gh api *-f*)",
      "Bash(gh api *-F*)", "Bash(gh api *--input*)"
    ]
  }
}
```

`gh api repos/*` は、`gh pr view` が使えない環境（GraphQL が止められているなど）で PR を REST API で読むため。書き込みになる指定（`-X`・`-f` など）は `deny` で止める。

Kiro は、`agents/kiro/` の定義に読むだけのコマンドの許可が入っている。この許可はサブエージェントの中でだけ効くので、decision-log は洗い出しを decision-log-planner に、読むのを decision-log-reader に任せ、メインの会話ではコマンドをほとんど回さない。

このリポジトリ自身の経緯は、decision-log で起こして [docs/decision-logs/](docs/decision-logs/README.md) に置いている（組織の記録の置き場所ではない）。

## 限界

- 差分の洗い出しは、決まった言葉と定数・設定ファイルで候補を拾う。言葉の出てこない振る舞いの変更は拾えない。
- 手順書や仕様の文書が中心のリポジトリでは、言葉の洗い出しがほぼ全件に当たり、絞り込みに使えない。コードのリポジトリ向け。
- リポジトリの外の変更（インフラの設定、管理画面のフラグ）は履歴に残らないので見えない。

## 確かめる

- テスト：`python3 -I -m unittest discover -s tests`（Python 3.10 以降。フロントマターの検査には PyYAML が要り、なければその検査だけ飛ばす）
- 実際のエージェントでの評価：スキルごとに `evals/<スキル名>/`（[decision-log](evals/decision-log/cases.md)）

[MIT License](LICENSE)

## 版

変更は [CHANGELOG.md](CHANGELOG.md) にある。PR は `changes/` に変更の断片を足し、リリースの PR が版を決めてまとめる（[docs/release.md](docs/release.md)）。
