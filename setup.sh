#!/bin/bash

# VALORANT Pointbook - セットアップスクリプト

echo "🎯 VALORANT Pointbook セットアップを開始します..."

# Python3の確認
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3がインストールされていません"
    exit 1
fi

echo "✅ Python3が見つかりました: $(python3 --version)"

# 仮想環境の作成
if [ ! -d "venv" ]; then
    echo "📦 仮想環境を作成中..."
    python3 -m venv venv
    echo "✅ 仮想環境を作成しました"
else
    echo "✅ 既存の仮想環境を使用します"
fi

# 仮想環境の有効化
echo "🚀 仮想環境を有効化中..."
source venv/bin/activate

# pipのアップグレード
echo "📦 pipをアップグレード中..."
pip install --upgrade pip

# 依存関係のインストール
echo "📦 依存関係をインストール中..."
pip install -r requirements.txt

echo ""
echo "✅ セットアップが完了しました！"
echo ""
echo "🎮 アプリケーションを起動するには："
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "📌 ブラウザで http://localhost:5000 にアクセスしてください"