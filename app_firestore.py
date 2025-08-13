from flask import Flask, render_template, jsonify, request, redirect, flash, url_for
import json
import os
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# Cloudinaryの初期設定
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dahgrxpky"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "664612899882299"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "kwMpxye5K46cW0XQewXHXf0-m3I")
)

# Firebaseの初期設定
if not firebase_admin._apps:
    # 環境変数からFirebase設定を読み込む
    firebase_config = {
        "type": "service_account",
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    
    # Firebase設定ファイルがある場合はそちらを優先
    if os.path.exists("firebase-key.json"):
        cred = credentials.Certificate("firebase-key.json")
    else:
        cred = credentials.Certificate(firebase_config)
    
    firebase_admin.initialize_app(cred)

# Firestoreクライアントの取得
db = firestore.client()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB制限

# 許可される画像拡張子
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_next_id():
    """次のIDを取得（最大値+1）"""
    try:
        # Firestoreから全ドキュメントを取得してIDの最大値を見つける
        points_ref = db.collection('points')
        docs = points_ref.stream()
        
        max_id = 0
        for doc in docs:
            data = doc.to_dict()
            if data.get('id', 0) > max_id:
                max_id = data['id']
        
        return max_id + 1
    except Exception as e:
        print(f"ID取得エラー: {e}")
        return 1

@app.route("/add", methods=["GET", "POST"])
def add_point():
    if request.method == "POST":
        try:
            # フォームデータの取得
            map_id = request.form.get("map")
            side = request.form.get("side")
            agent = request.form.get("agent")
            title = request.form.get("title")
            description = request.form.get("description")
            
            # バリデーション
            if not all([map_id, side, agent, title, description]):
                flash("すべての項目を入力してください", "error")
                return redirect(url_for('add_point'))
            
            # 画像ファイルの取得と検証
            stand_file = request.files.get("stand_image")
            point_file = request.files.get("point_image")
            extra_file = request.files.get("extra_image")
            
            if not all([stand_file, point_file, extra_file]):
                flash("3枚の画像をすべてアップロードしてください", "error")
                return redirect(url_for('add_point'))
            
            # ファイル形式の検証
            for file in [stand_file, point_file, extra_file]:
                if not allowed_file(file.filename):
                    flash(f"許可されていないファイル形式です: {file.filename}", "error")
                    return redirect(url_for('add_point'))
            
            # 次のIDを取得
            new_id = get_next_id()
            
            # Cloudinaryにアップロード
            try:
                stand_result = cloudinary.uploader.upload(
                    stand_file, 
                    public_id=f"points/{new_id}_stand",
                    overwrite=True
                )
                point_result = cloudinary.uploader.upload(
                    point_file, 
                    public_id=f"points/{new_id}_point",
                    overwrite=True
                )
                extra_result = cloudinary.uploader.upload(
                    extra_file, 
                    public_id=f"points/{new_id}_extra",
                    overwrite=True
                )
            except Exception as e:
                flash(f"画像のアップロードに失敗しました: {str(e)}", "error")
                return redirect(url_for('add_point'))
            
            # Firestoreに保存
            new_point = {
                "id": new_id,
                "map": map_id,
                "side": side,
                "agent": agent,
                "title": title,
                "description": description,
                "stand_image": stand_result["secure_url"],
                "point_image": point_result["secure_url"],
                "extra_image": extra_result["secure_url"],
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP
            }
            
            # Firestoreに追加
            db.collection('points').add(new_point)
            
            flash("定点を登録しました！", "success")
            return redirect(url_for('add_point'))
            
        except Exception as e:
            print(f"エラー: {e}")
            flash(f"エラーが発生しました: {str(e)}", "error")
            return redirect(url_for('add_point'))
    
    return render_template("add.html")

@app.route("/delete/<int:point_id>", methods=["POST"])
def delete_point(point_id):
    try:
        # Firestoreから該当ドキュメントを検索
        points_ref = db.collection('points')
        query = points_ref.where('id', '==', point_id).limit(1)
        docs = query.get()
        
        if docs:
            # ドキュメントを削除
            for doc in docs:
                doc.reference.delete()
            
            # Cloudinaryから画像を削除（オプション）
            try:
                cloudinary.uploader.destroy(f"points/{point_id}_stand")
                cloudinary.uploader.destroy(f"points/{point_id}_point")
                cloudinary.uploader.destroy(f"points/{point_id}_extra")
            except:
                pass  # 画像削除に失敗してもエラーにしない
            
            flash("定点を削除しました", "success")
        else:
            flash("指定された定点が見つかりません", "error")
            
    except Exception as e:
        print(f"削除エラー: {e}")
        flash(f"削除中にエラーが発生しました: {str(e)}", "error")
    
    return redirect(request.referrer or "/")

@app.route("/")
def index():
    with open("data/maps.json", encoding="utf-8") as f:
        maps = json.load(f)
    return render_template("index.html", maps=maps)

@app.route("/map/<map_id>")
def select_side(map_id):
    return render_template("map.html", map_id=map_id)

@app.route("/map/<map_id>/side/<side>")
def select_role(map_id, side):
    return render_template("role.html", map_id=map_id, side=side)

@app.route("/map/<map_id>/side/<side>/role/<role>")
def select_agent_by_role(map_id, side, role):
    with open("data/agents.json", "r", encoding="utf-8") as f:
        all_agents = json.load(f)
    
    agents = [agent for agent in all_agents if agent["role"] == role]
    return render_template("agent.html", map_id=map_id, side=side, role=role, agents=agents)

@app.route("/map/<map_id>/side/<side>/agent/<agent_id>")
def show_points_no_role(map_id, side, agent_id):
    try:
        # Firestoreから条件に合うポイントを取得
        points_ref = db.collection('points')
        query = points_ref.where('map', '==', map_id)\
                         .where('side', '==', side)\
                         .where('agent', '==', agent_id)
        
        docs = query.stream()
        points = []
        for doc in docs:
            point_data = doc.to_dict()
            points.append(point_data)
        
        # ID順にソート
        points.sort(key=lambda x: x.get('id', 0))
        
    except Exception as e:
        print(f"データ取得エラー: {e}")
        points = []
        flash("データの取得に失敗しました", "error")
    
    return render_template("points.html", map_id=map_id, side=side, role=None, agent_id=agent_id, points=points)

@app.route("/point/<int:point_id>")
def point_detail(point_id):
    try:
        # Firestoreから該当ポイントを取得
        points_ref = db.collection('points')
        query = points_ref.where('id', '==', point_id).limit(1)
        docs = query.get()
        
        if docs:
            point = docs[0].to_dict()
        else:
            flash("定点が見つかりません", "error")
            return redirect("/")
            
    except Exception as e:
        print(f"詳細取得エラー: {e}")
        flash("データの取得に失敗しました", "error")
        return redirect("/")
    
    return render_template("point_detail.html", point=point)

# データ移行用の関数（初回のみ実行）
@app.route("/migrate-to-firestore", methods=["GET"])
def migrate_to_firestore():
    """既存のJSONデータをFirestoreに移行"""
    try:
        # JSONファイルを読み込み
        if os.path.exists("data/points.json"):
            with open("data/points.json", "r", encoding="utf-8") as f:
                points = json.load(f)
            
            # Firestoreに一括追加
            batch = db.batch()
            for point in points:
                # タイムスタンプを追加
                point["created_at"] = firestore.SERVER_TIMESTAMP
                point["updated_at"] = firestore.SERVER_TIMESTAMP
                
                # 新しいドキュメントを作成
                doc_ref = db.collection('points').document()
                batch.set(doc_ref, point)
            
            # バッチ実行
            batch.commit()
            
            return f"✅ {len(points)}件のデータをFirestoreに移行しました"
        else:
            return "❌ points.jsonが見つかりません"
            
    except Exception as e:
        return f"❌ 移行エラー: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)