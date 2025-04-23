# Dajare Garden 🌸🤖🎌

GitHub Pages + Gemini で「ダジャレ採点バトル」を楽しむスターターキットです。

## 概要
* ユーザは 5 分ごとに 1 回、フォーム（GitHub Issue Form）からダジャレを投稿
* GitHub Actions が Gemini API を使って 100 点満点で採点し、`data/YYYY-MM-DD.json` に保存
* Gemini 自身も 5 分ごとに 1 本ダジャレを自動生成して参戦
* `docs/index.html` で当日ランキングを自動表示
* 人間 vs Gemini の得点勝負！

## 必要な準備
1. **このリポジトリを `Use this template` で作成**  
2. `Settings → Secrets and variables → Actions` に以下を追加  
   | Name | 用途 |
   |------|------|
   | `GEMINI_API_KEY` | Vertex AI で発行した **Gemini 1.5 Pro** などの API キー |
3. GitHub Pages を **main /docs** ディレクトリとして公開  
4. `docs/index.html` 内の `{{OWNER}}` `{{REPO}}` をあなたのリポジトリ名に置換  
5. これで 5 分毎に自動でランキングが更新されます！

## 仕組み
```
            +--------------+
            |  User Form   |  (GitHub Issue)
            +--------------+
                     ↓ (event: issues)
+----------+    +----------------+      +------------------+
| GitHub   |--> | evaluate_pun   | ---> |  data/DATE.json   |
| Actions  |    |  (Gemini score)|      +------------------+
+----------+             ↑
                     schedule (*/5)
                     |
                 +-----------+
                 | gemini_post|
                 +-----------+
```

## ライセンス
MIT
