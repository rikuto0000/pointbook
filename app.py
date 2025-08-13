from flask import Flask, render_template, jsonify, request, redirect, session, flash, url_for
import os
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import timedelta
from auth import *

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
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # セッション有効期限30日

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

# 認証関連ルート
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        try:
            # ユーザーを検索
            result = supabase.table('profiles').select('*').eq('username', username).single().execute()
            
            if result.data and verify_password(password, result.data['password_hash']):
                # ログイン成功
                create_session(result.data)
                flash('ログインしました', 'success')
                return redirect(url_for('index'))
            else:
                flash('ユーザー名またはパスワードが正しくありません', 'error')
        except Exception as e:
            flash('ユーザー名またはパスワードが正しくありません', 'error')
    
    return render_template('login.html')

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]
    email = request.form.get("email", "")
    
    try:
        # ユーザー名の重複チェック
        existing = supabase.table('profiles').select('id').eq('username', username).execute()
        if existing.data:
            flash('このユーザー名は既に使用されています', 'error')
            return redirect(url_for('login'))
        
        # 新しいユーザーを作成
        user_id = generate_user_id()
        new_user = {
            "id": user_id,
            "username": username,
            "password_hash": hash_password(password),
            "email": email if email else None,
            "avatar_url": f"https://ui-avatars.com/api/?name={username}&background=ff4655&color=fff"
        }
        
        result = supabase.table('profiles').insert(new_user).execute()
        
        # 自動ログイン
        create_session(result.data[0])
        flash('アカウントを作成しました', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash('登録中にエラーが発生しました', 'error')
        return redirect(url_for('login'))

@app.route("/logout")
def logout():
    try:
        clear_session()
        # 追加的にセッションを完全にクリア
        session.clear()
        flash('ログアウトしました', 'success')
    except Exception as e:
        print(f"Logout error: {str(e)}")
        session.clear()  # エラーが発生してもセッションをクリア
        flash('ログアウトしました', 'success')
    
    return redirect(url_for('index'))

# プロフィール画面
@app.route("/profile")
def profile():
    user = get_current_user()
    
    if not user:
        flash('ログインが必要です', 'warning')
        return redirect(url_for('login'))
    
    try:
        # ユーザーの統計情報を取得
        user_id = user['id']
        
        # いいねした定点数
        liked_count = supabase.table('likes').select('id', count='exact').eq('user_id', user_id).execute()
        likes_count = liked_count.count if liked_count.count else 0
        
        # ブックマークした定点数
        bookmarked_count = supabase.table('bookmarks').select('id', count='exact').eq('user_id', user_id).execute()
        bookmarks_count = bookmarked_count.count if bookmarked_count.count else 0
        
        # 投稿した定点数（システムユーザー以外）
        posted_count = supabase.table('setups').select('id', count='exact').eq('user_id', user_id).execute()
        posts_count = posted_count.count if posted_count.count else 0
        
        # 最近いいねした定点（JOINでsetupデータも取得）
        recent_likes = supabase.table('likes')\
            .select('*, setups!inner(*)')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(5)\
            .execute()
        
        # 最近ブックマークした定点（JOINでsetupデータも取得）
        recent_bookmarks = supabase.table('bookmarks')\
            .select('*, setups!inner(*)')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(5)\
            .execute()
        
        # データを整形
        liked_setups = []
        if recent_likes.data:
            for like in recent_likes.data:
                setup = like['setups']
                setup['id'] = setup.get('legacy_id', setup['id'])
                setup['stand_image'] = setup.get('stand_image_url', '')
                setup['point_image'] = setup.get('point_image_url', '')
                setup['extra_image'] = setup.get('extra_image_url', '')
                liked_setups.append(setup)
        
        bookmarked_setups = []
        if recent_bookmarks.data:
            for bookmark in recent_bookmarks.data:
                setup = bookmark['setups']
                setup['id'] = setup.get('legacy_id', setup['id'])
                setup['stand_image'] = setup.get('stand_image_url', '')
                setup['point_image'] = setup.get('point_image_url', '')
                setup['extra_image'] = setup.get('extra_image_url', '')
                bookmarked_setups.append(setup)
        
        return render_template('profile.html',
                             user=user,
                             likes_count=likes_count,
                             bookmarks_count=bookmarks_count,
                             posts_count=posts_count,
                             liked_setups=liked_setups,
                             bookmarked_setups=bookmarked_setups)
                             
    except Exception as e:
        print(f"Profile error: {str(e)}")
        # エラーが発生しても空のプロフィールを表示
        return render_template('profile.html',
                             user=user,
                             likes_count=0,
                             bookmarks_count=0,
                             posts_count=0,
                             liked_setups=[],
                             bookmarked_setups=[])

# いいね機能
@app.route("/api/like/<int:legacy_id>", methods=["POST"])
def toggle_like(legacy_id):
    if 'user_id' not in session:
        return jsonify({"error": "ログインが必要です"}), 401
    
    user_id = session['user_id']
    
    try:
        # legacy_idから実際のUUID（setup.id）を取得
        setup_result = supabase.table('setups').select('id').eq('legacy_id', legacy_id).single().execute()
        if not setup_result.data:
            return jsonify({"error": "定点が見つかりません"}), 404
            
        setup_uuid = setup_result.data['id']
        
        # 既存のいいねをチェック（UUID使用）
        existing = supabase.table('likes').select('id').eq('user_id', user_id).eq('setup_id', setup_uuid).execute()
        
        if existing.data:
            # いいねを削除
            supabase.table('likes').delete().eq('user_id', user_id).eq('setup_id', setup_uuid).execute()
            # RPC関数を正しいUUIDで呼び出し
            supabase.rpc('decrement_likes', {'setup_id': setup_uuid}).execute()
            return jsonify({"liked": False})
        else:
            # いいねを追加
            supabase.table('likes').insert({
                "user_id": user_id,
                "setup_id": setup_uuid
            }).execute()
            # RPC関数を正しいUUIDで呼び出し
            supabase.rpc('increment_likes', {'setup_id': setup_uuid}).execute()
            return jsonify({"liked": True})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ブックマーク機能
@app.route("/api/bookmark/<int:legacy_id>", methods=["POST"])
def toggle_bookmark(legacy_id):
    if 'user_id' not in session:
        return jsonify({"error": "ログインが必要です"}), 401
    
    user_id = session['user_id']
    
    try:
        # legacy_idから実際のUUID（setup.id）を取得
        setup_result = supabase.table('setups').select('id').eq('legacy_id', legacy_id).single().execute()
        if not setup_result.data:
            return jsonify({"error": "定点が見つかりません"}), 404
            
        setup_uuid = setup_result.data['id']
        
        # 既存のブックマークをチェック（UUID使用）
        existing = supabase.table('bookmarks').select('id').eq('user_id', user_id).eq('setup_id', setup_uuid).execute()
        
        if existing.data:
            # ブックマークを削除
            supabase.table('bookmarks').delete().eq('user_id', user_id).eq('setup_id', setup_uuid).execute()
            return jsonify({"bookmarked": False})
        else:
            # ブックマークを追加
            supabase.table('bookmarks').insert({
                "user_id": user_id,
                "setup_id": setup_uuid
            }).execute()
            return jsonify({"bookmarked": True})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        user = get_current_user()
        return render_template("index.html", maps=maps, user=user)
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
        
        # ユーザー情報を取得
        user = get_current_user()
        
        # ログインユーザーのいいね・ブックマーク状態を確認
        is_liked = False
        is_bookmarked = False
        
        if user:
            # legacy_idから実際のUUID（setup.id）を取得
            setup_uuid_result = supabase.table('setups').select('id').eq('legacy_id', point_id).single().execute()
            setup_uuid = setup_uuid_result.data['id'] if setup_uuid_result.data else None
            
            if setup_uuid:
                # いいね状態（UUIDで検索）
                like_check = supabase.table('likes').select('id').eq('user_id', user['id']).eq('setup_id', setup_uuid).execute()
                is_liked = bool(like_check.data)
                
                # ブックマーク状態（UUIDで検索）
                bookmark_check = supabase.table('bookmarks').select('id').eq('user_id', user['id']).eq('setup_id', setup_uuid).execute()
                is_bookmarked = bool(bookmark_check.data)
            else:
                is_liked = False
                is_bookmarked = False
        
        return render_template("point_detail.html", 
                             point=point, 
                             user=user,
                             is_liked=is_liked,
                             is_bookmarked=is_bookmarked)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 500



if __name__ == "__main__":
    app.run(debug=True)
