# VALORANT Pointbook アプリ仕様書

## プロジェクト概要
VALORANTゲームのラインナップ（定点）を管理・閲覧するためのFlaskベースのプログレッシブウェブアプリ（PWA）。プレイヤーがマップ、サイド、エージェント別にラインナップを検索・閲覧し、ポジショニングとエイムポイントの画像ベースチュートリアルを提供。

## 技術スタック

### バックエンド
- **Flask 3.1.1** - Webアプリケーションフレームワーク
- **Supabase** - PostgreSQLデータベース（JSONファイルから移行済み）
- **Cloudinary** - 画像ホスティングサービス
- **python-dotenv** - 環境変数管理

### フロントエンド
- **Jinja2** - テンプレートエンジン
- **Tailwind CSS** - CSSフレームワーク（CDN版）
- **Rajdhaniフォント** - VALORANTスタイルのフォント

### PWA機能
- **Service Worker** - オフライン対応
- **Web App Manifest** - ホーム画面追加対応

## データベース構造

### 1. maps テーブル
```sql
CREATE TABLE maps (
    id TEXT PRIMARY KEY,           -- "ascent", "icebox" など
    name TEXT NOT NULL,            -- "アセント", "アイスボックス"
    image TEXT,                    -- 画像パス
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 2. agents テーブル
```sql
CREATE TABLE agents (
    id TEXT PRIMARY KEY,           -- "sova", "kayo" など
    name TEXT NOT NULL,            -- "ソーヴァ", "KAY/O"
    role TEXT NOT NULL,            -- "initiator", "controller" など
    image TEXT,                    -- 画像パス
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 3. setups テーブル（メインテーブル）
```sql
CREATE TABLE setups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legacy_id INTEGER,             -- 旧JSONデータとの互換性用
    user_id UUID NOT NULL,         -- ユーザーID
    map TEXT NOT NULL,             -- マップID
    site TEXT NOT NULL,            -- サイト（A/B）
    side TEXT NOT NULL CHECK (side IN ('attack', 'defense')),
    agent TEXT NOT NULL,           -- エージェントID
    title TEXT NOT NULL,           -- ラインナップタイトル
    description TEXT NOT NULL,     -- 説明文
    stand_image_url TEXT,          -- 立ち位置画像URL（Cloudinary）
    point_image_url TEXT,          -- エイムポイント画像URL
    extra_image_url TEXT,          -- 補足画像URL
    video_url TEXT,               -- 動画URL（未使用）
    likes_count INTEGER DEFAULT 0, -- いいね数
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 4. その他のテーブル（実装済み・未使用）
```sql
-- ユーザープロファイル
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- いいね機能
CREATE TABLE likes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    setup_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ブックマーク機能
CREATE TABLE bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    setup_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- コメント機能
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    setup_id UUID NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

## アプリケーション構造

### ディレクトリ構造
```
valorant-pointbook-master/
├── app.py                    # メインFlaskアプリケーション
├── requirements.txt          # Python依存関係
├── migrate_to_supabase.py   # データ移行スクリプト
├── .env                     # 環境変数（Supabaseキー）
├── SPEC.md                  # このファイル（仕様書）
├── CLAUDE.md                # Claude Code用指示書
├── data/                    # 静的データ（移行済み・参考用）
│   ├── agents.json          # エージェント情報
│   ├── maps.json            # マップ情報
│   ├── points.json          # ラインナップデータ（移行済み）
│   └── manifest.json        # PWA設定
├── static/                  # 静的ファイル
│   ├── images/              # ローカル画像
│   │   ├── agents/         # エージェントアイコン
│   │   └── maps/           # マップ画像
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

### URLルーティング

| URL | 機能 | テンプレート | データソース |
|-----|------|------------|------------|
| `/` | マップ選択画面 | `index.html` | `maps`テーブル |
| `/map/<map_id>` | サイド選択（攻撃/防御） | `map.html` | 静的 |
| `/map/<map_id>/side/<side>` | ロール選択 | `role.html` | 静的 |
| `/map/<map_id>/side/<side>/role/<role>` | エージェント選択 | `agent.html` | `agents`テーブル |
| `/map/<map_id>/side/<side>/agent/<agent_id>` | ラインナップ一覧 | `points.html` | `setups`テーブル |
| `/point/<int:point_id>` | ラインナップ詳細 | `point_detail.html` | `setups`テーブル |
| `/add` | 新規ラインナップ追加（GET/POST） | `add.html` | `setups`テーブル |
| `/delete/<int:point_id>` | ラインナップ削除（POST） | - | `setups`テーブル |

### 主要機能

#### 1. 閲覧機能
- **マップ選択**: 9つのマップから選択（Supabaseから動的取得）
- **サイド選択**: 攻撃/防御を選択
- **ロール選択**: controller、duelist、initiator、sentinelから選択
- **エージェント選択**: 選択したロールのエージェント一覧（Supabaseから動的取得）
- **ラインナップ一覧**: 条件に合致するラインナップを表示（Supabaseクエリ）
- **詳細表示**: 3枚の画像（立ち位置、エイムポイント、補足）で定点を説明

#### 2. 管理機能
- **ラインナップ追加**: 画像3枚とメタデータをCloudinaryにアップロード→Supabaseに保存
- **ラインナップ削除**: 既存ラインナップをSupabaseから削除
- **画像管理**: Cloudinaryへの自動アップロード（public_idで整理）

## データ構造

### ラインナップデータ構造（互換性維持）
```json
{
  "id": 1,                              // legacy_id（既存URL互換性用）
  "map": "ascent",                     // マップID
  "side": "attack",                    // 攻撃/防御
  "agent": "sova",                     // エージェントID
  "title": "MIDリコン",                // タイトル
  "description": "１バウンスフルチャージ", // 説明
  "stand_image": "Cloudinary URL",     // 立ち位置画像
  "point_image": "Cloudinary URL",     // エイムポイント画像
  "extra_image": "Cloudinary URL"      // 補足画像
}
```

### Supabase内部データ構造
```json
{
  "id": "uuid",                        // Supabase UUID
  "legacy_id": 1,                      // 旧JSONデータID
  "user_id": "system_user_uuid",       // システムユーザー
  "map": "ascent",
  "site": "A",                         // デフォルト値
  "side": "attack",
  "agent": "sova",
  "title": "MIDリコン",
  "description": "１バウンスフルチャージ",
  "stand_image_url": "Cloudinary URL",
  "point_image_url": "Cloudinary URL",
  "extra_image_url": "Cloudinary URL",
  "likes_count": 0,
  "created_at": "2025-01-13T...",
  "updated_at": "2025-01-13T..."
}
```

## 設定・環境変数

### 必須環境変数（`.env`ファイル）
```bash
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### ハードコード済み設定（app.py内）
```python
# Supabase設定
SUPABASE_URL = "https://dzmtxqldvglsagjvovcr.supabase.co"

# Cloudinary設定（要改善）
cloudinary.config(
    cloud_name="dahgrxpky",
    api_key="664612899882299",
    api_secret="kwMpxye5K46cW0XQewXHXf0-m3I"
)

# システム設定
SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"
```

## デプロイメント

### 開発環境起動
```bash
pip install -r requirements.txt
python app.py  # http://localhost:5000で起動
```

### 本番環境デプロイ
```bash
gunicorn app:app
```

### 依存関係（requirements.txt）
```txt
Flask==3.1.1
Werkzeug==3.1.3
Jinja2==3.1.6
MarkupSafe==3.0.2
itsdangerous==2.2.0
click==8.2.0
blinker==1.9.0
cloudinary==1.36.0
gunicorn==21.2.0
python-dotenv==1.0.0
supabase==2.11.0
```

## PWA機能

### Service Worker機能 (`static/service-worker.js`)
- オフラインキャッシュ機能
- 静的リソース（CSS、JS、画像）のキャッシュ
- ネットワーク障害時のフォールバック

### Web App Manifest (`data/manifest.json`)
```json
{
  "name": "VALORANT Pointbook",
  "short_name": "ValoPointbook",
  "theme_color": "#ff4655",
  "background_color": "#1a1a1a",
  "display": "standalone",
  "start_url": "/",
  "icons": [...]
}
```

## データマイグレーション

### 移行完了データ（2025年1月13日実行済み）
- **マップ**: 9件（ascent, split, haven, bind, breeze, lotus, sunset, icebox, fracture）
- **エージェント**: 27件（全エージェント、最新のtejo、waylayも含む）
- **ラインナップ**: 44件（主にsova、kayoのラインナップ）

### マイグレーションスクリプト (`migrate_to_supabase.py`)
- JSONファイルからSupabaseへの一括移行
- エラーハンドリング付き
- バッチ処理対応（10件ずつ処理）

### 互換性維持
- `legacy_id`フィールドで既存URL（`/point/1`など）の互換性を保持
- 画像URLはCloudinaryで継続利用
- テンプレートでのデータ変換処理を実装

## セキュリティ考慮事項

### 現在の問題点
⚠️ **Cloudinary認証情報**: `app.py`内にハードコード  
⚠️ **SQLインジェクション**: Supabaseクライアント使用により対策済み  
⚠️ **認証機能**: 現在未実装（管理機能は誰でもアクセス可能）

### 推奨改善事項
```python
# 1. Cloudinary認証情報の環境変数化
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# 2. 管理機能の認証追加
@app.before_request
def require_auth():
    if request.endpoint in ['add_point', 'delete_point']:
        # 認証チェック処理
        pass
```

## 今後の拡張可能性

### 実装済みだが未使用の機能
- **ユーザー管理**: `profiles`テーブル（UUIDベース）
- **いいね機能**: `likes`テーブル、`likes_count`フィールド
- **ブックマーク機能**: `bookmarks`テーブル
- **コメント機能**: `comments`テーブル
- **動画サポート**: `video_url`フィールド

### 将来の機能拡張案
1. **認証システム**: Supabase Authを使用したユーザー認証
2. **ソーシャル機能**: いいね・ブックマーク・コメント機能の有効化
3. **検索機能**: タイトル・説明でのフリーテキスト検索
4. **タグ機能**: ラインナップのカテゴリ分類
5. **動画ガイド**: Cloudinaryでの動画アップロード対応
6. **API化**: REST API提供によるモバイルアプリ連携
7. **管理画面**: 管理者用ダッシュボード

### データベース拡張案
```sql
-- タグ機能
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#gray'
);

CREATE TABLE setup_tags (
    setup_id UUID REFERENCES setups(id),
    tag_id UUID REFERENCES tags(id),
    PRIMARY KEY (setup_id, tag_id)
);

-- 評価機能
CREATE TABLE ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    setup_id UUID REFERENCES setups(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 運用・保守

### 定期メンテナンス項目
- Cloudinary使用量の監視
- Supabaseデータベース使用量の監視
- 画像の最適化（サイズ・フォーマット）
- 古いデータのアーカイブ

### モニタリング
- アプリケーションログ（Flask）
- データベースパフォーマンス（Supabase）
- 画像配信パフォーマンス（Cloudinary）

### バックアップ
- Supabaseの自動バックアップ機能を利用
- Cloudinary画像の定期バックアップ推奨