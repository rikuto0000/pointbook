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
    
    return render_template('login.html', user=get_current_user())

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
        
        # いいねした定点数（存在する定点のみカウント）
        likes_with_setups = supabase.table('likes')\
            .select('setup_id', count='exact')\
            .eq('user_id', user_id)\
            .execute()
        likes_count = likes_with_setups.count if likes_with_setups.count else 0
        
        # ブックマークした定点数（存在する定点のみカウント）
        bookmarks_with_setups = supabase.table('bookmarks')\
            .select('setup_id', count='exact')\
            .eq('user_id', user_id)\
            .execute()
        bookmarks_count = bookmarks_with_setups.count if bookmarks_with_setups.count else 0
        
        # 投稿した定点数（システムユーザー以外）
        posted_count = supabase.table('setups').select('id', count='exact').eq('user_id', user_id).execute()
        posts_count = posted_count.count if posted_count.count else 0
        
        # 最近いいねした定点のIDを取得
        recent_likes_ids = supabase.table('likes')\
            .select('setup_id')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(5)\
            .execute()
        
        # 最近ブックマークした定点のIDを取得
        recent_bookmarks_ids = supabase.table('bookmarks')\
            .select('setup_id')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(5)\
            .execute()
        
        # 投稿した定点を取得
        posted_setups_result = supabase.table('setups')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(10)\
            .execute()
        
        # データを整形
        liked_setups = []
        if recent_likes_ids.data:
            for like in recent_likes_ids.data:
                setup_uuid = like['setup_id']
                try:
                    setup_result = supabase.table('setups').select('*').eq('id', setup_uuid).execute()
                    if setup_result.data:
                        setup = setup_result.data[0]
                        setup['id'] = setup.get('legacy_id', setup['id'])
                        setup['stand_image'] = setup.get('stand_image_url', '')
                        setup['point_image'] = setup.get('point_image_url', '')
                        setup['extra_image'] = setup.get('extra_image_url', '')
                        liked_setups.append(setup)
                except Exception as e:
                    print(f"Error fetching liked setup {setup_uuid}: {str(e)}")
                    continue
        
        bookmarked_setups = []
        if recent_bookmarks_ids.data:
            for bookmark in recent_bookmarks_ids.data:
                setup_uuid = bookmark['setup_id']
                try:
                    setup_result = supabase.table('setups').select('*').eq('id', setup_uuid).execute()
                    if setup_result.data:
                        setup = setup_result.data[0]
                        setup['id'] = setup.get('legacy_id', setup['id'])
                        setup['stand_image'] = setup.get('stand_image_url', '')
                        setup['point_image'] = setup.get('point_image_url', '')
                        setup['extra_image'] = setup.get('extra_image_url', '')
                        bookmarked_setups.append(setup)
                except Exception as e:
                    print(f"Error fetching bookmarked setup {setup_uuid}: {str(e)}")
                    continue
        
        posted_setups = []
        if posted_setups_result.data:
            for setup in posted_setups_result.data:
                setup['id'] = setup.get('legacy_id', setup['id'])
                setup['stand_image'] = setup.get('stand_image_url', '')
                setup['point_image'] = setup.get('point_image_url', '')
                setup['extra_image'] = setup.get('extra_image_url', '')
                posted_setups.append(setup)
        
        return render_template('profile.html',
                             user=user,
                             likes_count=likes_count,
                             bookmarks_count=bookmarks_count,
                             posts_count=posts_count,
                             liked_setups=liked_setups,
                             bookmarked_setups=bookmarked_setups,
                             posted_setups=posted_setups)
                             
    except Exception as e:
        print(f"Profile error: {str(e)}")
        # エラーが発生しても空のプロフィールを表示
        return render_template('profile.html',
                             user=user,
                             likes_count=0,
                             bookmarks_count=0,
                             posts_count=0,
                             liked_setups=[],
                             bookmarked_setups=[],
                             posted_setups=[])

@app.route("/profile/posts")
def profile_posts():
    user = get_current_user()
    
    if not user:
        flash('ログインが必要です', 'warning')
        return redirect(url_for('login'))
    
    try:
        user_id = user['id']
        
        # すべての投稿した定点を取得
        posted_setups_result = supabase.table('setups')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()
        
        posted_setups = []
        if posted_setups_result.data:
            for setup in posted_setups_result.data:
                setup['id'] = setup.get('legacy_id', setup['id'])
                setup['stand_image'] = setup.get('stand_image_url', '')
                setup['point_image'] = setup.get('point_image_url', '')
                setup['extra_image'] = setup.get('extra_image_url', '')
                posted_setups.append(setup)
        
        return render_template('profile_posts.html',
                             user=user,
                             posted_setups=posted_setups,
                             posts_count=len(posted_setups))
                             
    except Exception as e:
        print(f"Profile posts error: {str(e)}")
        flash('エラーが発生しました', 'error')
        return redirect(url_for('profile'))

@app.route("/profile/likes")
def profile_likes():
    user = get_current_user()
    
    if not user:
        flash('ログインが必要です', 'warning')
        return redirect(url_for('login'))
    
    try:
        user_id = user['id']
        
        # すべてのいいねした定点のIDを取得
        likes_ids = supabase.table('likes')\
            .select('setup_id')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()
        
        liked_setups = []
        if likes_ids.data:
            for like in likes_ids.data:
                setup_uuid = like['setup_id']
                try:
                    setup_result = supabase.table('setups').select('*').eq('id', setup_uuid).execute()
                    if setup_result.data:
                        setup = setup_result.data[0]
                        setup['id'] = setup.get('legacy_id', setup['id'])
                        setup['stand_image'] = setup.get('stand_image_url', '')
                        setup['point_image'] = setup.get('point_image_url', '')
                        setup['extra_image'] = setup.get('extra_image_url', '')
                        liked_setups.append(setup)
                except Exception:
                    continue
        
        return render_template('profile_likes.html',
                             user=user,
                             liked_setups=liked_setups,
                             likes_count=len(liked_setups))
                             
    except Exception as e:
        print(f"Profile likes error: {str(e)}")
        flash('エラーが発生しました', 'error')
        return redirect(url_for('profile'))

@app.route("/profile/bookmarks")
def profile_bookmarks():
    user = get_current_user()
    
    if not user:
        flash('ログインが必要です', 'warning')
        return redirect(url_for('login'))
    
    try:
        user_id = user['id']
        
        # すべてのブックマークした定点のIDを取得
        bookmarks_ids = supabase.table('bookmarks')\
            .select('setup_id')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()
        
        bookmarked_setups = []
        if bookmarks_ids.data:
            for bookmark in bookmarks_ids.data:
                setup_uuid = bookmark['setup_id']
                try:
                    setup_result = supabase.table('setups').select('*').eq('id', setup_uuid).execute()
                    if setup_result.data:
                        setup = setup_result.data[0]
                        setup['id'] = setup.get('legacy_id', setup['id'])
                        setup['stand_image'] = setup.get('stand_image_url', '')
                        setup['point_image'] = setup.get('point_image_url', '')
                        setup['extra_image'] = setup.get('extra_image_url', '')
                        bookmarked_setups.append(setup)
                except Exception:
                    continue
        
        return render_template('profile_bookmarks.html',
                             user=user,
                             bookmarked_setups=bookmarked_setups,
                             bookmarks_count=len(bookmarked_setups))
                             
    except Exception as e:
        print(f"Profile bookmarks error: {str(e)}")
        flash('エラーが発生しました', 'error')
        return redirect(url_for('profile'))

# いいね機能
@app.route("/api/like/<int:legacy_id>", methods=["POST"])
def toggle_like(legacy_id):
    if 'user_id' not in session:
        return jsonify({"error": "ログインが必要です"}), 401
    
    user_id = session['user_id']
    
    try:
        # legacy_idから実際のUUID（setup.id）を取得
        setup_result = supabase.table('setups').select('id').eq('legacy_id', legacy_id).execute()
        if not setup_result.data:
            return jsonify({"error": "定点が見つかりません"}), 404
            
        setup_uuid = setup_result.data[0]['id']
        
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
        setup_result = supabase.table('setups').select('id').eq('legacy_id', legacy_id).execute()
        if not setup_result.data:
            return jsonify({"error": "定点が見つかりません"}), 404
            
        setup_uuid = setup_result.data[0]['id']
        
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
        # 現在のユーザーを取得
        user = get_current_user()
        if not user:
            flash('ログインが必要です', 'warning')
            return redirect(url_for('login'))
        
        map_id = request.form["map"]
        side = request.form["side"]
        site = request.form["site"]
        agent = request.form["agent"]
        title = request.form["title"]
        description = request.form["description"]
        skill_type = request.form.get("skill_type", "")

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

            # Supabaseに新しいデータを挿入（現在のユーザーIDを使用）
            new_setup = {
                "legacy_id": new_legacy_id,
                "user_id": user['id'],
                "map": map_id,
                "site": site,
                "side": side,
                "agent": agent,
                "title": title,
                "description": description,
                "stand_image_url": stand_url,
                "point_image_url": point_url,
                "extra_image_url": extra_url,
                "likes_count": 0
            }
            
            # skill_typeカラムが存在する場合のみ追加
            if skill_type:
                new_setup["skill_type"] = skill_type

            result = supabase.table('setups').insert(new_setup).execute()
            
            # 総定点数を取得
            total_count = supabase.table('setups').select('id', count='exact').execute()
            total_points = total_count.count if total_count.count else 0
            
            return render_template('success.html', 
                                 total_points=total_points,
                                 user_points=1,
                                 user=user)

        except Exception as e:
            return f"エラーが発生しました: {str(e)}", 500
    
    # GET リクエストの場合もログインチェック
    user = get_current_user()
    if not user:
        flash('ログインが必要です', 'warning')
        return redirect(url_for('login'))
    
    return render_template("add.html", user=user)


@app.route("/delete/<int:point_id>", methods=["POST"])
def delete_point(point_id):
    # ログインチェック
    user = get_current_user()
    if not user:
        flash('ログインが必要です', 'warning')
        return redirect(url_for('login'))
    
    try:
        # 削除対象の定点を取得して投稿者確認
        setup_result = supabase.table('setups').select('user_id').eq('legacy_id', point_id).execute()
        
        if not setup_result.data:
            flash('指定された定点が見つかりません', 'error')
            return redirect(request.referrer or "/")
        
        # 投稿者本人または管理者のみ削除可能
        if setup_result.data[0]['user_id'] != user['id']:
            flash('この定点を削除する権限がありません', 'error')
            return redirect(request.referrer or "/")
        
        # 削除対象の詳細情報を取得（削除前に）
        map_id = setup_result.data[0].get('map')
        side = setup_result.data[0].get('side')
        agent = setup_result.data[0].get('agent')
        
        # 削除実行
        result = supabase.table('setups').delete().eq('legacy_id', point_id).execute()
        
        # 削除成功メッセージに行き先を含める
        if map_id and side and agent:
            flash(f'定点を削除しました。{agent}の定点一覧に移動します。', 'success')
        else:
            flash('定点を削除しました', 'success')
        
        # 削除後の適切な導線を提供
        referrer = request.referrer
        if referrer and '/point/' in referrer:
            # 定点詳細ページから削除された場合、そのエージェントの定点一覧に戻る
            if map_id and side and agent:
                return redirect(f"/map/{map_id}/side/{side}/agent/{agent}")
            else:
                return redirect("/")
        elif referrer and '/profile' in referrer:
            # プロフィール画面から削除された場合、プロフィールに戻る
            return redirect("/profile")
        else:
            # その他の場合はホームに戻る
            return redirect("/")
        
    except Exception as e:
        flash(f'削除中にエラーが発生しました: {str(e)}', 'error')
        return redirect(request.referrer or "/")



@app.route("/")
def index():
    try:
        user = get_current_user()
        
        # マップ情報を取得
        maps_result = supabase.table('maps').select('*').execute()
        maps = maps_result.data if maps_result.data else []
        
        # 各マップの定点数を計算
        for map_data in maps:
            count_result = supabase.table('setups')\
                .select('id', count='exact')\
                .eq('map', map_data['id'])\
                .execute()
            map_data['total_setups'] = count_result.count if count_result.count else 0
        
        # 統計情報を取得
        total_points_result = supabase.table('setups').select('id', count='exact').execute()
        total_points = total_points_result.count if total_points_result.count else 0
        
        total_users_result = supabase.table('profiles').select('id', count='exact').execute()
        total_users = total_users_result.count if total_users_result.count else 0
        
        return render_template("index.html", 
                             maps=maps,
                             user=user,
                             total_points=total_points,
                             total_users=total_users)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 500

@app.route("/api/agent/<agent_id>/points")
def get_agent_points_count(agent_id):
    try:
        # クエリパラメータを取得
        map_filter = request.args.get('map', '')
        side_filter = request.args.get('side', '')
        
        # ベースクエリ
        query = supabase.table('setups').select('id', count='exact').eq('agent', agent_id)
        
        # フィルタを適用
        if map_filter:
            query = query.eq('map', map_filter)
        if side_filter:
            query = query.eq('side', side_filter)
            
        result = query.execute()
        count = result.count if result.count else 0
        
        return jsonify({"count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/agent/<agent_id>")
def show_agent_points(agent_id):
    try:
        user = get_current_user()
        
        # エージェント情報を取得
        agent_result = supabase.table('agents').select('*').eq('id', agent_id).execute()
        if not agent_result.data:
            return "エージェントが見つかりません", 404
        agent = agent_result.data[0]
        
        # そのエージェントの全定点を取得
        points_result = supabase.table('setups')\
            .select('*')\
            .eq('agent', agent_id)\
            .order('created_at', desc=True)\
            .execute()
        
        points = []
        if points_result.data:
            for point in points_result.data:
                point['id'] = point.get('legacy_id', point['id'])
                point['stand_image'] = point.get('stand_image_url', '')
                point['point_image'] = point.get('point_image_url', '')
                point['extra_image'] = point.get('extra_image_url', '')
                points.append(point)
        
        # マップ情報を取得（フィルタリング用）
        maps_result = supabase.table('maps').select('*').execute()
        maps = maps_result.data if maps_result.data else []
        
        return render_template("agent_points.html", 
                             agent=agent,
                             points=points,
                             maps=maps,
                             user=user)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 500

@app.route("/map/<map_id>")
def select_agent_for_map(map_id):
    try:
        user = get_current_user()
        
        # マップ情報を取得
        map_result = supabase.table('maps').select('*').eq('id', map_id).execute()
        if not map_result.data:
            return "マップが見つかりません", 404
        map_info = map_result.data[0]
        
        # エージェント情報を取得（ロール別にグループ化）
        agents_result = supabase.table('agents').select('*').execute()
        all_agents = agents_result.data if agents_result.data else []
        
        # ロール別にエージェントを分類し、このマップでの定点数を計算
        agents_by_role = {
            'controller': [],
            'initiator': [],
            'sentinel': [],
            'duelist': []
        }
        
        for agent in all_agents:
            role = agent.get('role', 'duelist')
            if role in agents_by_role:
                # 各エージェントのこのマップでの定点数を計算
                count_result = supabase.table('setups')\
                    .select('id', count='exact')\
                    .eq('agent', agent['id'])\
                    .eq('map', map_id)\
                    .execute()
                agent['map_setups'] = count_result.count if count_result.count else 0
                agents_by_role[role].append(agent)
        
        return render_template("map_agents.html", 
                             map_info=map_info,
                             agents_by_role=agents_by_role,
                             user=user)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 500

@app.route("/map/<map_id>/side/<side>")
def select_role(map_id, side):
    user = get_current_user()
    return render_template("role.html", map_id=map_id, side=side, user=user)


@app.route("/map/<map_id>/side/<side>/role/<role>")
def select_agent_by_role(map_id, side, role):
    try:
        user = get_current_user()
        result = supabase.table('agents').select('*').eq('role', role).execute()
        agents = result.data
        
        # 各エージェントの定点数を取得
        for agent in agents:
            count_result = supabase.table('setups')\
                .select('id', count='exact')\
                .eq('map', map_id)\
                .eq('side', side)\
                .eq('agent', agent['id'])\
                .execute()
            agent['setup_count'] = count_result.count if count_result.count else 0
        
        return render_template("agent.html", map_id=map_id, side=side, role=role, agents=agents, user=user)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 500

@app.route("/map/<map_id>/agent/<agent_id>")
def show_map_agent_points(map_id, agent_id):
    try:
        user = get_current_user()
        
        # マップ情報を取得
        map_result = supabase.table('maps').select('*').eq('id', map_id).execute()
        if not map_result.data:
            return "マップが見つかりません", 404
        map_info = map_result.data[0]
        
        # エージェント情報を取得
        agent_result = supabase.table('agents').select('*').eq('id', agent_id).execute()
        if not agent_result.data:
            return "エージェントが見つかりません", 404
        agent = agent_result.data[0]
        
        # そのマップ＋エージェントの全定点を取得
        points_result = supabase.table('setups')\
            .select('*')\
            .eq('map', map_id)\
            .eq('agent', agent_id)\
            .order('created_at', desc=True)\
            .execute()
        
        points = []
        if points_result.data:
            for point in points_result.data:
                point['id'] = point.get('legacy_id', point['id'])
                point['stand_image'] = point.get('stand_image_url', '')
                point['point_image'] = point.get('point_image_url', '')
                point['extra_image'] = point.get('extra_image_url', '')
                points.append(point)
        
        return render_template("map_agent_points.html", 
                             map_info=map_info,
                             agent=agent,
                             points=points,
                             user=user)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 500

@app.route("/map/<map_id>/side/<side>/agent/<agent_id>")
def show_points_no_role(map_id, side, agent_id):
    try:
        user = get_current_user()
        result = supabase.table('setups').select('*').eq('map', map_id).eq('side', side).eq('agent', agent_id).execute()
        points = result.data
        
        # legacy形式との互換性のためデータを変換
        for point in points:
            if 'legacy_id' in point and point['legacy_id']:
                point['id'] = point['legacy_id']
            point['stand_image'] = point.get('stand_image_url', '')
            point['point_image'] = point.get('point_image_url', '')
            point['extra_image'] = point.get('extra_image_url', '')
        
        return render_template("points.html", map_id=map_id, side=side, role=None, agent_id=agent_id, points=points, user=user)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 500

@app.route("/point/<int:point_id>")
def point_detail(point_id):
    try:
        result = supabase.table('setups').select('*').eq('legacy_id', point_id).execute()
        
        if not result.data:
            return "定点が見つかりません", 404
            
        point = result.data[0]
        
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
            setup_uuid_result = supabase.table('setups').select('id').eq('legacy_id', point_id).execute()
            setup_uuid = setup_uuid_result.data[0]['id'] if setup_uuid_result.data else None
            
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
