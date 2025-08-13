# 🚀 Render デプロイガイド

VALORANT PointbookをRenderにデプロイするための完全ガイドです。

## 🎯 Renderとは

- **無料プラン有り** - 月750時間まで無料
- **自動デプロイ** - GitHubと連携して自動デプロイ
- **HTTPS対応** - SSL証明書自動取得
- **スケーラブル** - 負荷に応じて自動スケール

## 📋 事前準備

### 1. GitHubリポジトリの準備
```bash
# GitHubにプッシュ
git add .
git commit -m "Render deployment ready"
git push origin main
```

### 2. 必要な環境変数
以下の値を準備してください：
- `SUPABASE_ANON_KEY`: Supabaseの匿名キー
- `CLOUDINARY_CLOUD_NAME`: Cloudinaryのクラウド名
- `CLOUDINARY_API_KEY`: CloudinaryのAPIキー
- `CLOUDINARY_API_SECRET`: CloudinaryのAPIシークレット

## 🚀 Renderデプロイ手順

### ステップ1: Renderアカウント作成
1. [Render](https://render.com) にアクセス
2. "Get Started for Free" でアカウント作成
3. GitHubアカウントで認証

### ステップ2: 新しいWebサービス作成
1. Renderダッシュボードで "New" → "Web Service"
2. GitHubリポジトリを選択
3. 以下の設定を入力：

```
Name: valorant-pointbook
Environment: Python
Build Command: pip install -r requirements.txt
Start Command: gunicorn -c gunicorn.conf.py app:app
```

### ステップ3: 環境変数の設定
"Environment" タブで以下を設定：

```
PYTHON_VERSION=3.11.0
FLASK_ENV=production
SUPABASE_ANON_KEY=[あなたのSupabaseキー]
CLOUDINARY_CLOUD_NAME=[あなたのCloudinaryクラウド名]
CLOUDINARY_API_KEY=[あなたのCloudinaryAPIキー]
CLOUDINARY_API_SECRET=[あなたのCloudinaryAPIシークレット]
SECRET_KEY=[ランダムな秘密鍵]
```

### ステップ4: デプロイ実行
1. "Create Web Service" をクリック
2. 自動的にビルドとデプロイが開始
3. 完了までに約2-3分待機

## 🎛️ render.yamlを使用した自動設定（推奨）

リポジトリに`render.yaml`が含まれているので、以下の手順で簡単デプロイ：

1. Renderダッシュボードで "New" → "Blueprint"
2. GitHubリポジトリを選択
3. 環境変数だけ設定してデプロイ実行

## 🔧 カスタマイズ設定

### 無料プランの制限
- **メモリ**: 512MB
- **CPU**: 0.1 CPU
- **スリープ**: 15分非アクティブでスリープ
- **帯域幅**: 100GB/月

### 有料プランへのアップグレード
月$7のStarterプランで：
- メモリ: 1GB
- CPU: 0.5 CPU
- スリープなし
- 帯域幅: 400GB/月

## 🌐 カスタムドメイン設定

### サブドメイン（無料）
- `your-app-name.onrender.com` が自動割り当て

### カスタムドメイン（有料プランのみ）
1. "Settings" → "Custom Domains"
2. ドメインを追加
3. DNS設定でCNAMEを追加

## 📊 モニタリング

### メトリクス確認
- CPU/メモリ使用率
- レスポンス時間
- エラー率

### ログ確認
```bash
# Renderダッシュボードの "Logs" タブで確認
# またはCLIを使用
render logs -s [service-id]
```

## 🚨 トラブルシューティング

### よくある問題

**Q: ビルドが失敗する**
```
解決方法:
- requirements.txtの文字エンコーディングを確認
- Python バージョンを3.11.0に固定
- ログでエラー詳細を確認
```

**Q: アプリケーションが起動しない**
```
解決方法:
- 環境変数が正しく設定されているか確認
- Supabase接続をテスト
- gunicorn設定を確認
```

**Q: 画像アップロードエラー**
```
解決方法:
- Cloudinary認証情報を再確認
- ファイルサイズ制限（16MB）を確認
```

### ローカルテスト
デプロイ前にローカルで本番環境をテスト：

```bash
# 本番と同じ環境変数を設定
export FLASK_ENV=production
export SECRET_KEY=test-key

# Gunicornで起動テスト
gunicorn -c gunicorn.conf.py app:app

# ローカルでアクセステスト
curl http://localhost:5000
```

## 🔄 継続的デプロイ

### 自動デプロイ設定
GitHubのmainブランチにpushすると自動デプロイ：

```bash
# コードを更新
git add .
git commit -m "Feature: add new functionality"
git push origin main

# Renderが自動的にデプロイ実行
```

### デプロイフック
特定の条件でデプロイを実行：

```bash
# Webhookを設定して外部からデプロイをトリガー
curl -X POST https://api.render.com/deploy/[your-hook-id]
```

## 📈 パフォーマンス最適化

### Renderでの推奨設定

1. **静的ファイル配信**
```python
# app.py で静的ファイル配信を最適化
app.static_folder = 'static'
app.static_url_path = '/static'
```

2. **キャッシュ設定**
```python
# レスポンスヘッダーでキャッシュを設定
@app.after_request
def after_request(response):
    if request.endpoint == 'static':
        response.headers['Cache-Control'] = 'public, max-age=3600'
    return response
```

## 🔐 セキュリティ設定

### HTTPS強制
Renderは自動的にHTTPS化されますが、追加設定：

```python
# app.py でHTTPS強制
from flask_talisman import Talisman
Talisman(app, force_https=True)
```

### セキュリティヘッダー
```python
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

## ✅ デプロイ後チェックリスト

- [ ] アプリケーションが正常に起動している
- [ ] 全てのページが正しく表示される
- [ ] データベース接続が正常
- [ ] 画像アップロード機能が動作
- [ ] PWA機能が有効
- [ ] エラーページが適切に表示される
- [ ] レスポンス時間が適切（< 1秒）

## 🎉 デプロイ完了！

Renderでのデプロイが完了しました。以下のURLでアクセス可能：

```
https://your-app-name.onrender.com
```

### 次のステップ
1. カスタムドメインの設定（オプション）
2. モニタリング設定
3. バックアップ戦略の検討
4. パフォーマンス監視

---

**トラブルがあれば [Render Docs](https://render.com/docs) を参照してください。**