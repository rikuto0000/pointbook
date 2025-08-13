# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリでコードを扱う際のガイダンスを提供します。

## 重要な指示
**必ず日本語で応答してください。コードやコマンドは英語のままで構いませんが、説明や会話は全て日本語で行ってください。**

## プロジェクト概要

VALORANT Pointbook - VALORANTゲームのラインナップ（定点）を管理・閲覧するためのFlaskベースのプログレッシブウェブアプリ（PWA）です。プレイヤーがマップ、サイド、エージェント別にラインナップを検索・閲覧でき、ポジショニングとエイムポイントの画像ベースのチュートリアルを提供します。

## 開発コマンド

```bash
# 依存関係のインストール
# 注意：requirements.txtはUTF-16LEエンコーディングのため、必要に応じて変換
pip install -r requirements.txt

# 開発サーバーの起動（http://localhost:5000）
python app.py

# 本番環境デプロイ
gunicorn app:app
```

## ディレクトリ構造

```
valorant-pointbook-master/
├── app.py                    # メインFlaskアプリケーション
├── requirements.txt          # Python依存関係（UTF-16LE）
├── migrate_to_cloudinary.py  # 画像移行スクリプト
├── data/                     # 静的JSONデータ
│   ├── agents.json          # エージェント情報
│   ├── maps.json            # マップ情報
│   ├── points.json          # ラインナップデータ
│   └── manifest.json        # PWA設定
├── static/                  # 静的ファイル
│   ├── images/              # ローカル画像
│   │   ├── agents/         # エージェントアイコン
│   │   ├── maps/           # マップ画像
│   │   └── points/         # ラインナップ画像（移行中）
│   ├── icons/              # PWAアイコン
│   └── service-worker.js   # PWA用Service Worker
└── templates/              # Jinja2テンプレート
    ├── index.html          # マップ選択
    ├── map.html            # サイド選択
    ├── role.html           # ロール選択
    ├── agent.html          # エージェント選択
    ├── points.html         # ラインナップ一覧
    ├── point_detail.html   # ラインナップ詳細
    └── add.html            # 管理者用追加画面
```

## 技術スタック

- **バックエンド**: Flask 3.1.1（Python）
- **データストレージ**: 
  - ローカルJSONファイル（points.json）
  - Cloudinary CDN（画像ホスティング）
- **フロントエンド**: 
  - Jinja2テンプレート
  - Tailwind CSS（CDN版）
  - Rajdhaniフォント（VALORANTスタイル）
- **PWA機能**: Service Worker + Manifest

## 主要機能

### ユーザー向け機能
1. **マップ選択** (`/`): 9つのマップから選択
2. **サイド選択** (`/map/<map_id>`): 攻撃/防御を選択
3. **エージェント選択** (`/map/<map_id>/side/<side>/role/<role>`): ロール別にエージェントを表示
4. **ラインナップ表示** (`/point/<point_id>`): 3枚の画像で定点を説明
   - stand_image: 立ち位置
   - point_image: エイムポイント
   - extra_image: 補足情報

### 管理者機能
- **ラインナップ追加** (`/add`): 新規ラインナップの登録
- **ラインナップ削除** (`/delete/<point_id>`): 既存ラインナップの削除

## データ構造

### points.json
```json
{
  "id": 1,
  "map": "ascent",
  "side": "attack",
  "agent": "sova",
  "title": "MIDリコン",
  "description": "１バウンスフルチャージ",
  "stand_image": "Cloudinary URL",
  "point_image": "Cloudinary URL",
  "extra_image": "Cloudinary URL"
}
```

## セキュリティ注意事項

⚠️ **重要**: 現在、Cloudinary APIの認証情報が`app.py`と`migrate_to_cloudinary.py`にハードコードされています。本番環境では必ず環境変数に移動してください：

```python
# 推奨: 環境変数を使用
import os
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)
```

## PWA対応

- **オフライン対応**: Service Workerによるキャッシュ機能
- **ホーム画面追加**: モバイルでアプリとしてインストール可能
- **テーマカラー**: VALORANTブランドカラー（#ff4655）

## 開発時の注意点

1. **文字エンコーディング**: requirements.txtはUTF-16LEエンコーディング
2. **画像アップロード**: 新規ラインナップはCloudinaryに自動アップロード
3. **レスポンシブデザイン**: モバイルファーストで設計
4. **アニメーション**: CSS keyframesでフェードアップ効果を実装