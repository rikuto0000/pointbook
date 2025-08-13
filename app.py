from flask import Flask, render_template, jsonify, request, redirect
import os
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
from supabase import create_client, Client
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Cloudinaryの初期設定
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'dahgrxpky'),
    api_key=os.getenv('CLOUDINARY_API_KEY', '664612899882299'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', 'kwMpxye5K46cW0XQewXHXf0-m3I')
)

# Supabase設定
SUPABASE_URL = "https://dzmtxqldvglsagjvovcr.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR6bXR4cWxkdmdsc2FnanZvdmNyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ2MzcyNDksImV4cCI6MjA3MDIxMzI0OX0.L1Ndf7rdPNQDmZyFr873Ik1s9HbtAYpZrIHYeHUpkSI")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"
app = Flask(__name__)

# Flask設定
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# エラーハンドラー
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message="ページが見つかりません"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_code=500, 
                         error_message="サーバーエラーが発生しました"), 500

@app.errorhandler(413)
def too_large(error):
    return render_template('error.html', 
                         error_code=413, 
                         error_message="ファイルサイズが大きすぎます"), 413


@app.route("/add", methods=["GET", "POST"])
def add_point():
    if request.method == "POST":
        map_id = request.form["map"]
        side = request.form["side"]
        agent = request.form["agent"]
        title = request.form["title"]
        description = request.form["description"]

        # 画像3枚取得
        stand_file = request.files["stand_image"]
        point_file = request.files["point_image"]
        extra_file = request.files["extra_image"]

        try:
            # 次のlegacy_idを取得
            result = supabase.table('setups').select('legacy_id').not_.is_('legacy_id', 'null').order('legacy_id', desc=True).limit(1).execute()
            if result.data:
                new_legacy_id = result.data[0]['legacy_id'] + 1
            else:
                new_legacy_id = 1

            # Cloudinaryにアップロード
            stand_result = cloudinary.uploader.upload(stand_file, public_id=f"points/{new_legacy_id}_stand")
            point_result = cloudinary.uploader.upload(point_file, public_id=f"points/{new_legacy_id}_point")
            extra_result = cloudinary.uploader.upload(extra_file, public_id=f"points/{new_legacy_id}_extra")

            # URLを取得
            stand_url = stand_result["secure_url"]
            point_url = point_result["secure_url"]
            extra_url = extra_result["secure_url"]

            # Supabaseに新しいデータを挿入
            new_setup = {
                "legacy_id": new_legacy_id,
                "user_id": SYSTEM_USER_ID,
                "map": map_id,
                "site": "A",  # デフォルト値
                "side": side,
                "agent": agent,
                "title": title,
                "description": description,
                "stand_image_url": stand_url,
                "point_image_url": point_url,
                "extra_image_url": extra_url,
                "likes_count": 0
            }

            result = supabase.table('setups').insert(new_setup).execute()
            
            # 総定点数を取得
            total_count = supabase.table('setups').select('id', count='exact').execute()
            total_points = total_count.count if total_count.count else 0
            
            return render_template('success.html', 
                                 total_points=total_points,
                                 user_points=1)

        except Exception as e:
            return f"エラーが発生しました: {str(e)}", 500

    return render_template("add.html")


@app.route("/delete/<int:point_id>", methods=["POST"])
def delete_point(point_id):
    try:
        # legacy_idで削除
        result = supabase.table('setups').delete().eq('legacy_id', point_id).execute()
        return redirect(request.referrer or "/")
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 500



@app.route("/")
def index():
    try:
        result = supabase.table('maps').select('*').execute()
        maps = result.data
        return render_template("index.html", maps=maps)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 500

@app.route("/map/<map_id>")
def select_side(map_id):
    return render_template("map.html", map_id=map_id)

@app.route("/map/<map_id>/side/<side>")
def select_role(map_id, side):
    return render_template("role.html", map_id=map_id, side=side)


@app.route("/map/<map_id>/side/<side>/role/<role>")
def select_agent_by_role(map_id, side, role):
    try:
        result = supabase.table('agents').select('*').eq('role', role).execute()
        agents = result.data
        return render_template("agent.html", map_id=map_id, side=side, role=role, agents=agents)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 500

@app.route("/map/<map_id>/side/<side>/agent/<agent_id>")
def show_points_no_role(map_id, side, agent_id):
    try:
        result = supabase.table('setups').select('*').eq('map', map_id).eq('side', side).eq('agent', agent_id).execute()
        points = result.data
        
        # legacy形式との互換性のためデータを変換
        for point in points:
            if 'legacy_id' in point and point['legacy_id']:
                point['id'] = point['legacy_id']
            point['stand_image'] = point.get('stand_image_url', '')
            point['point_image'] = point.get('point_image_url', '')
            point['extra_image'] = point.get('extra_image_url', '')
        
        return render_template("points.html", map_id=map_id, side=side, role=None, agent_id=agent_id, points=points)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 500

@app.route("/point/<int:point_id>")
def point_detail(point_id):
    try:
        result = supabase.table('setups').select('*').eq('legacy_id', point_id).single().execute()
        point = result.data
        
        if not point:
            return "定点が見つかりません", 404
        
        # legacy形式との互換性のためデータを変換
        point['id'] = point.get('legacy_id', point_id)
        point['stand_image'] = point.get('stand_image_url', '')
        point['point_image'] = point.get('point_image_url', '')
        point['extra_image'] = point.get('extra_image_url', '')
        
        return render_template("point_detail.html", point=point)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 500



if __name__ == "__main__":
    app.run(debug=True)
