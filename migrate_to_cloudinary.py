import json
import os
import cloudinary
import cloudinary.uploader

# Cloudinary設定
cloudinary.config(
    cloud_name="dahgrxpky",
    api_key="664612899882299",
    api_secret="kwMpxye5K46cW0XQewXHXf0-m3I"
)

# ファイルパス
json_path = "data/points.json"
image_folder = "static/images/points"

# JSON読み込み
with open(json_path, "r", encoding="utf-8") as f:
    points = json.load(f)

for point in points:
    point_id = point["id"]

    def upload_if_local(path, suffix):
        if path.startswith("/static"):  # ローカルパスならアップロード
            filename = f"{point_id}_{suffix}.jpg"
            full_path = os.path.join(image_folder, filename)
            if os.path.exists(full_path):
                result = cloudinary.uploader.upload(full_path, public_id=f"points/{filename}")
                return result["secure_url"]
        return path  # 既にURLならそのまま

    point["stand_image"] = upload_if_local(point["stand_image"], "stand")
    point["point_image"] = upload_if_local(point["point_image"], "point")
    point["extra_image"] = upload_if_local(point["extra_image"], "extra")

# JSON上書き保存
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(points, f, indent=2, ensure_ascii=False)

print("Cloudinaryへの移行完了 ✅")
