"""
認証関連の機能
"""
from flask import session, redirect, url_for, flash, request
from functools import wraps
import secrets
import hashlib
from datetime import datetime, timedelta
import uuid

def generate_user_id():
    """新しいユーザーIDを生成"""
    return str(uuid.uuid4())

def hash_password(password):
    """パスワードをハッシュ化"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', 
                                   password.encode('utf-8'), 
                                   salt.encode('utf-8'), 
                                   100000)
    return f"{salt}${pwd_hash.hex()}"

def verify_password(password, stored_hash):
    """パスワードを検証"""
    try:
        salt, pwd_hash = stored_hash.split('$')
        test_hash = hashlib.pbkdf2_hmac('sha256',
                                        password.encode('utf-8'),
                                        salt.encode('utf-8'),
                                        100000)
        return test_hash.hex() == pwd_hash
    except:
        return False

def login_required(f):
    """ログインが必要なルートのデコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('ログインが必要です', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """現在のログインユーザー情報を取得"""
    if 'user_id' in session:
        return {
            'id': session['user_id'],
            'username': session.get('username', 'ゲスト'),
            'avatar_url': session.get('avatar_url', None)
        }
    return None

def create_session(user_data):
    """ユーザーセッションを作成"""
    session['user_id'] = user_data['id']
    session['username'] = user_data['username']
    session['avatar_url'] = user_data.get('avatar_url')
    session['logged_in_at'] = datetime.now().isoformat()
    session.permanent = True  # Remember me

def clear_session():
    """セッションをクリア"""
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('avatar_url', None)
    session.pop('logged_in_at', None)