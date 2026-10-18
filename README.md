# decision-continuity

コードのリポジトリの履歴から、いつ・何が変わったか（change-history）と、なぜか・何が分かっていないか（decision-log）を起こす。Claude Code と Kiro で動く。

## Claude Code

シェルで実行する。次に起動したときから効く。

```sh
# 導入
claude plugin install decision-continuity --marketplace MichinaoShimizu/decision-continuity

# 更新
claude plugin update decision-continuity@decision-continuity

# 削除
claude plugin uninstall decision-continuity@decision-continuity
```

## Kiro

リポジトリのルートで実行する。導入と更新は同じ。終わったら会話を開き直す。

```sh
# 導入・更新
d=$(mktemp -d) && git clone --depth 1 https://github.com/MichinaoShimizu/decision-continuity "$d" && sh "$d/tools/install.sh" kiro

# 削除
rm -rf .kiro/skills/decision-log .kiro/skills/change-history .kiro/agents/decision-log-planner.* .kiro/agents/decision-log-reader.*
```

## 使い方

```text
decision-log で audit して。範囲は src/payment/。
洗い出しは decision-log-planner、読むのは decision-log-reader に、1 回でまとめて並列に任せて。
```

既定は読むだけ。ファイルに書くのは `write` と頼んだときだけ。

```text
change-history で、いつどんな変更をしてきたかを docs/change-history/ に月ごとにまとめて。
```

## その他

[確認を減らす（Claude Code）](docs/claude-code-permissions.md)／[変更](CHANGELOG.md)／[リリース](docs/release.md)／[このリポジトリの経緯](docs/decision-logs/README.md)／[MIT License](LICENSE)
