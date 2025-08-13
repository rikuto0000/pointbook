#!/usr/bin/env python3
"""
JSON データをSupabaseに移行するスクリプト
"""

import json
import os
from supabase import create_client, Client
from typing import Dict, List, Any

# Supabase設定
SUPABASE_URL = "https://dzmtxqldvglsagjvovcr.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")  # 環境変数から読み込み

def load_json_data(filepath: str) -> List[Dict[str, Any]]:
    """JSONファイルを読み込む"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return []

def migrate_maps(supabase: Client) -> bool:
    """mapsデータを移行"""
    print("Migrating maps data...")
    maps_data = load_json_data('data/maps.json')
    
    if not maps_data:
        print("No maps data found")
        return False
    
    try:
        # 既存データを削除
        supabase.table('maps').delete().neq('id', '').execute()
        
        # 新しいデータを挿入
        result = supabase.table('maps').insert(maps_data).execute()
        print(f"Migrated {len(maps_data)} maps successfully")
        return True
    except Exception as e:
        print(f"Error migrating maps: {e}")
        return False

def migrate_agents(supabase: Client) -> bool:
    """agentsデータを移行"""
    print("Migrating agents data...")
    agents_data = load_json_data('data/agents.json')
    
    if not agents_data:
        print("No agents data found")
        return False
    
    try:
        # 既存データを削除
        supabase.table('agents').delete().neq('id', '').execute()
        
        # 新しいデータを挿入
        result = supabase.table('agents').insert(agents_data).execute()
        print(f"Migrated {len(agents_data)} agents successfully")
        return True
    except Exception as e:
        print(f"Error migrating agents: {e}")
        return False

def migrate_points(supabase: Client) -> bool:
    """pointsデータをsetupsテーブルに移行"""
    print("Migrating points data to setups table...")
    points_data = load_json_data('data/points.json')
    
    if not points_data:
        print("No points data found")
        return False
    
    # データを変換
    setups_data = []
    for point in points_data:
        setup = {
            'legacy_id': point['id'],
            'map': point['map'],
            'side': point['side'],
            'agent': point['agent'],
            'title': point['title'],
            'description': point['description'],
            'stand_image_url': point['stand_image'],
            'point_image_url': point['point_image'],
            'extra_image_url': point['extra_image'],
            'user_id': '00000000-0000-0000-0000-000000000000',  # システムユーザー
            'site': 'A',  # デフォルト値（必要に応じて後で更新）
            'likes_count': 0
        }
        setups_data.append(setup)
    
    try:
        # 既存のlegacy_idを持つデータを削除
        supabase.table('setups').delete().not_.is_('legacy_id', 'null').execute()
        
        # 新しいデータを挿入
        # バッチサイズを小さくして分割挿入
        batch_size = 10
        for i in range(0, len(setups_data), batch_size):
            batch = setups_data[i:i+batch_size]
            result = supabase.table('setups').insert(batch).execute()
        
        print(f"Migrated {len(setups_data)} points to setups successfully")
        return True
    except Exception as e:
        print(f"Error migrating points: {e}")
        return False

def main():
    """メイン実行関数"""
    if not SUPABASE_KEY:
        print("Error: SUPABASE_ANON_KEY environment variable not set")
        print("Please set your Supabase anon key:")
        print("export SUPABASE_ANON_KEY='your_key_here'")
        return
    
    # Supabaseクライアントを初期化
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("Starting migration to Supabase...")
    print(f"Target URL: {SUPABASE_URL}")
    
    # 順次移行実行
    success_count = 0
    
    if migrate_maps(supabase):
        success_count += 1
    
    if migrate_agents(supabase):
        success_count += 1
    
    if migrate_points(supabase):
        success_count += 1
    
    print(f"\nMigration completed: {success_count}/3 successful")
    
    if success_count == 3:
        print("✅ All data migrated successfully!")
    else:
        print("⚠️  Some migrations failed. Please check the errors above.")

if __name__ == "__main__":
    main()