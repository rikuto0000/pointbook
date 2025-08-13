#!/usr/bin/env python3
"""
簡易テストサーバー - Flaskなしで基本的な動作確認
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import json

class TestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # points.jsonを読み込んでテスト
            try:
                with open('data/points.json', 'r', encoding='utf-8') as f:
                    points = json.load(f)
                    point_count = len(points)
            except:
                point_count = 0
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>VALORANT Pointbook テストサーバー</title>
                <meta charset="UTF-8">
                <style>
                    body {{ 
                        background: #0f1923; 
                        color: white; 
                        font-family: sans-serif;
                        padding: 20px;
                    }}
                    .info {{ 
                        background: #1c1c1c; 
                        padding: 20px; 
                        border-radius: 10px;
                        margin: 10px 0;
                    }}
                    .status {{ color: #00ff00; }}
                    .error {{ color: #ff4655; }}
                </style>
            </head>
            <body>
                <h1>🎯 VALORANT Pointbook - テストサーバー</h1>
                
                <div class="info">
                    <h2>📊 現在の状態</h2>
                    <p>登録済み定点数: <span class="status">{point_count}件</span></p>
                </div>
                
                <div class="info">
                    <h2>🔍 ファイル構造チェック</h2>
                    <ul>
                        <li>data/points.json: {'✅ 存在' if os.path.exists('data/points.json') else '❌ 不明'}</li>
                        <li>data/maps.json: {'✅ 存在' if os.path.exists('data/maps.json') else '❌ 不明'}</li>
                        <li>data/agents.json: {'✅ 存在' if os.path.exists('data/agents.json') else '❌ 不明'}</li>
                    </ul>
                </div>
                
                <div class="info">
                    <h2>⚠️ 注意</h2>
                    <p class="error">これは簡易テストサーバーです。</p>
                    <p>Flaskが必要です。以下のコマンドでインストールしてください：</p>
                    <pre style="background: black; padding: 10px;">
pip install flask cloudinary
または
pip install -r requirements.txt
                    </pre>
                </div>
                
                <div class="info">
                    <h2>📝 最新の定点データ（最大5件）</h2>
                    <ul>
            """
            
            try:
                with open('data/points.json', 'r', encoding='utf-8') as f:
                    points = json.load(f)
                    for point in points[-5:]:
                        html += f"<li>{point.get('title', 'タイトルなし')} - {point.get('map', '?')} / {point.get('agent', '?')}</li>"
            except:
                html += "<li class='error'>データ読み込みエラー</li>"
            
            html += """
                    </ul>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
        else:
            super().do_GET()

if __name__ == '__main__':
    os.chdir('/mnt/c/Users/rikut/Documents/div/valorant-pointbook-master')
    port = 8000
    server = HTTPServer(('localhost', port), TestHandler)
    print(f"🚀 テストサーバー起動中: http://localhost:{port}")
    print("Ctrl+C で終了")
    server.serve_forever()