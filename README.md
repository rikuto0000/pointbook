# 🎯 VALORANT Pointbook

VALORANTの定点（ラインナップ）を管理・共有するためのWebアプリケーション
Supabase対応版 - モダンなUIでリッチな体験を提供

## ✨ 特徴

- 📱 **PWA対応** - スマートフォンでアプリのようにインストール可能
- 🎨 **モダンUI** - Glassmorphismとパーティクルアニメーション
- 🚀 **高パフォーマンス** - Supabaseによる高速データベース
- 🔒 **セキュリティ** - 本番環境に適したセキュリティ設定
- 📊 **スケーラブル** - Gunicornによる本番デプロイメント対応

## 🚀 デプロイ手順

### クイック デプロイ（Render - 推奨）

**最も簡単な方法：**

1. **GitHubにpush**
```bash
git add .
git commit -m "Deploy to Render"
git push origin main
```

2. **[Render](https://render.com) で New > Blueprint**
3. **GitHubリポジトリを選択**
4. **環境変数を設定**：
   - `SUPABASE_ANON_KEY`
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY` 
   - `CLOUDINARY_API_SECRET`

5. **デプロイ実行** - 約2-3分で完了

📖 詳細手順: [RENDER_DEPLOY.md](RENDER_DEPLOY.md)

### 手動デプロイ（VPS/サーバー）

`.env`ファイルを作成：
```bash
# Supabase設定
SUPABASE_ANON_KEY=your_supabase_anon_key

# Cloudinary設定
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Flask設定
FLASK_ENV=production
SECRET_KEY=your-secure-random-secret-key-here
```

依存関係とデプロイ：
```bash
# Python仮想環境の作成
python3 -m venv venv
source venv/bin/activate

# パッケージのインストール
pip install -r requirements.txt

# Gunicornでの起動
gunicorn -c gunicorn.conf.py app:app
```

## 🔧 開発環境

### クイックスタート

```bash
# 仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# 開発サーバーの起動
python app.py
```

ブラウザで `http://localhost:5000` にアクセス

## 📦 技術スタック

### バックエンド
- **Flask 3.1.1** - Webフレームワーク
- **Supabase** - PostgreSQLデータベース
- **Cloudinary** - 画像CDN
- **Gunicorn** - WSGIサーバー

### フロントエンド
- **Tailwind CSS** - ユーティリティファーストCSS
- **Font Awesome** - アイコン
- **Custom CSS** - Glassmorphismとアニメーション
- **Service Worker** - PWA機能

### データベース構造

```sql
-- Maps テーブル
maps (id, name, display_name, image_url)

-- Agents テーブル  
agents (id, name, display_name, role, image_url)

-- Setups テーブル
setups (
  id, legacy_id, user_id, map, site, side, agent,
  title, description, stand_image_url, point_image_url, 
  extra_image_url, likes_count, created_at, updated_at
)
```

## 🎮 使用方法

### ユーザー向け機能
1. **マップ選択** - 9つのマップから選択
2. **サイド選択** - 攻撃/防御を選択
3. **ロール選択** - コントローラー/イニシエーター/センチネル/デュエリスト
4. **エージェント選択** - ロール別にフィルタされたエージェント
5. **定点閲覧** - 立ち位置、エイムポイント、着弾位置の3枚画像

### 管理者機能
- **定点追加** (`/add`) - 新しい定点の登録
- **定点削除** - 既存定点の削除
- 画像は自動的にCloudinaryにアップロード

## 🔒 セキュリティ

### 本番環境での注意点

1. **SECRET_KEY** を必ず変更
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

2. **データベース認証情報** を環境変数で管理

3. **HTTPS** での運用を推奨

4. **ファイルアップロード制限** - 16MB制限済み

## 🚨 トラブルシューティング

### よくある問題

**Q: requirements.txtのエンコーディングエラー**
A: UTF-16LEエンコーディングの可能性があります。UTF-8で再保存してください。

**Q: Supabaseへの接続エラー**
A: `.env`ファイルの`SUPABASE_ANON_KEY`を確認してください。

**Q: 画像アップロードエラー**
A: Cloudinary認証情報と16MB制限を確認してください。

**Q: ナビゲーションが正しく動作しない**
A: ブラウザのキャッシュをクリアしてください。

### ログの確認

```bash
# Gunicornログの確認
gunicorn -c gunicorn.conf.py app:app --log-level debug

# アプリケーションログ
tail -f /var/log/app.log
```

## 📈 パフォーマンス

### 最適化済み設定

- **Gunicorn**: 2ワーカープロセス
- **Cloudinary**: 画像CDNによる高速配信
- **Service Worker**: オフライン対応とキャッシュ
- **CSS/JS**: 軽量化とフォールバック

### モニタリング

- エラーハンドリング完備（404、500、413）
- 包括的なJavaScriptエラーキャッチ
- パフォーマンス監視対応

## 🔄 アップデート履歴

### v2.0.0 (最新)
- ✅ Supabaseデータベース移行
- ✅ モダンUI実装
- ✅ PWA対応
- ✅ 本番環境対応
- ✅ 包括的エラーハンドリング

### v1.0.0 
- 基本機能実装（JSON ベース）

## 📞 サポート

問題が発生した場合は、以下を確認してください：

1. 環境変数設定（`.env`）
2. Python 3.8+のバージョン
3. 仮想環境の有効化
4. 依存関係のインストール

## 📄 ライセンス

このプロジェクトは教育目的で作成されています。