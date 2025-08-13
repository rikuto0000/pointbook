# 🚀 VALORANT Pointbook リリースチェックリスト

## ✅ リリース前チェック項目

### 1. 環境設定
- [ ] `.env`ファイルが正しく設定されている
- [ ] `SECRET_KEY`が本番用のランダムな値に変更されている
- [ ] Supabase認証情報が正しい
- [ ] Cloudinary認証情報が正しい

### 2. データベース
- [ ] Supabaseプロジェクトが稼働している
- [ ] 必要なテーブル（maps, agents, setups）が存在する
- [ ] サンプルデータが正しく移行されている
- [ ] データベース接続がテストできている

### 3. セキュリティ
- [ ] 本番環境では`FLASK_ENV=production`に設定
- [ ] ファイルアップロード制限（16MB）が有効
- [ ] エラーハンドリングが適切に実装されている
- [ ] 認証情報がハードコードされていない

### 4. パフォーマンス
- [ ] Gunicorn設定ファイル（`gunicorn.conf.py`）が適切
- [ ] ワーカー数がサーバーのCPUコア数に適している
- [ ] Cloudinary画像配信が正常に動作
- [ ] Service Workerによるキャッシュが有効

### 5. 機能テスト
- [ ] マップ選択が正常に動作
- [ ] サイド選択が正常に動作
- [ ] ロール選択が正常に動作
- [ ] エージェント選択が正常に動作
- [ ] 定点一覧表示が正常に動作
- [ ] 定点詳細表示が正常に動作
- [ ] 定点追加機能が正常に動作
- [ ] 定点削除機能が正常に動作

### 6. ナビゲーション
- [ ] 各ページ間の遷移が正常
- [ ] 戻るボタンが正しく動作
- [ ] パンくずナビゲーションが適切
- [ ] エラーページからの復帰が可能

### 7. UI/UX
- [ ] レスポンシブデザインが各デバイスで正常
- [ ] アニメーションが適切に動作
- [ ] ローディング状態の表示が適切
- [ ] エラーメッセージが分かりやすい

### 8. PWA機能
- [ ] マニフェストファイルが正しく配置
- [ ] Service Workerが登録されている
- [ ] オフライン機能が基本的に動作
- [ ] ホーム画面への追加が可能

## 🔧 デプロイ手順

### ステップ1: 環境準備
```bash
# 1. 仮想環境の作成
python3 -m venv venv
source venv/bin/activate

# 2. 依存関係のインストール
pip install -r requirements.txt

# 3. 環境変数の設定
cp .env.example .env
# .envファイルを適切に編集
```

### ステップ2: 本番設定確認
```bash
# SECRET_KEYの生成
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# 設定確認
python -c "
from app import app
print('Flask ENV:', app.config.get('ENV'))
print('Secret Key set:', bool(app.config.get('SECRET_KEY')))
print('Max Content Length:', app.config.get('MAX_CONTENT_LENGTH'))
"
```

### ステップ3: データベース接続テスト
```bash
python -c "
from app import supabase
try:
    result = supabase.table('maps').select('*').limit(1).execute()
    print('✅ Database connection OK')
    print('Maps count:', len(result.data))
except Exception as e:
    print('❌ Database connection failed:', e)
"
```

### ステップ4: 本番デプロイ
```bash
# Gunicornでの起動
gunicorn -c gunicorn.conf.py app:app

# または直接指定
gunicorn --bind 0.0.0.0:5000 --workers 2 app:app
```

## 🧪 テストスクリプト

以下のテストを手動で実行してください：

### 基本動作テスト
1. ブラウザで `http://localhost:5000` にアクセス
2. 各マップをクリックして表示確認
3. 攻撃/防御の選択確認
4. ロール選択の動作確認
5. エージェント選択の動作確認
6. 定点詳細の表示確認

### エラーハンドリングテスト
1. 存在しないURLにアクセス（404エラー）
2. 不正なパラメータでアクセス
3. 大きすぎるファイルのアップロード（413エラー）

### PWAテスト
1. Chrome DevToolsでLighthouseを実行
2. PWAスコアが80%以上であることを確認
3. モバイルデバイスでホーム画面追加をテスト

## 📊 パフォーマンスチェック

### Lighthouseスコア目標
- [ ] Performance: 80+
- [ ] Accessibility: 90+
- [ ] Best Practices: 90+
- [ ] SEO: 80+
- [ ] PWA: 80+

### ロードテスト
```bash
# Apache Benchを使用してロードテスト
ab -n 100 -c 10 http://localhost:5000/

# 目標: 平均応答時間 < 500ms
```

## 🚨 緊急時の対応

### ロールバック手順
1. 前のバージョンのコードにリバート
2. データベースのバックアップから復旧
3. 環境変数の確認

### ログ確認
```bash
# Gunicornログの確認
tail -f gunicorn.log

# アプリケーションエラーログ
grep "ERROR" app.log
```

## 📝 リリースノート テンプレート

```markdown
# VALORANT Pointbook v2.0.0 リリース

## 🎉 新機能
- Supabaseデータベース対応
- モダンUIデザイン（Glassmorphism）
- PWA対応（オフライン機能）
- パフォーマンス向上

## 🔧 改善
- エラーハンドリングの強化
- レスポンシブデザインの最適化
- セキュリティ強化

## 🐛 修正
- ナビゲーション問題の解決
- 画像アップロード安定性の向上

## 💾 データベース移行
- JSON → Supabase PostgreSQL
- 全データの保持（44定点、27エージェント、9マップ）

## 🔄 アップグレード手順
1. 新しいコードをデプロイ
2. 環境変数を更新
3. データベース接続を確認
```

## ✅ 最終確認

リリース前に以下を確認：

- [ ] 全ての機能が正常に動作している
- [ ] エラーが発生していない
- [ ] パフォーマンスが適切
- [ ] セキュリティ設定が正しい
- [ ] ドキュメントが更新されている

---

**🚀 リリース準備完了！**

全てのチェック項目が完了したら、本番環境にデプロイしてください。