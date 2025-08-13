@echo off
REM VALORANT Pointbook - Windows用セットアップスクリプト

echo 🎯 VALORANT Pointbook セットアップを開始します...

REM Python3の確認
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Pythonがインストールされていません
    echo Pythonをインストールしてください: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Pythonが見つかりました

REM 仮想環境の作成
if not exist "venv" (
    echo 📦 仮想環境を作成中...
    python -m venv venv
    echo ✅ 仮想環境を作成しました
) else (
    echo ✅ 既存の仮想環境を使用します
)

REM 仮想環境の有効化
echo 🚀 仮想環境を有効化中...
call venv\Scripts\activate.bat

REM pipのアップグレード
echo 📦 pipをアップグレード中...
python -m pip install --upgrade pip

REM 依存関係のインストール
echo 📦 依存関係をインストール中...
pip install -r requirements.txt

echo.
echo ✅ セットアップが完了しました！
echo.
echo 🎮 アプリケーションを起動するには：
echo   venv\Scripts\activate.bat
echo   python app.py
echo.
echo 📌 ブラウザで http://localhost:5000 にアクセスしてください
pause