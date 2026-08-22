import os
import pygame
import json
from datetime import datetime

# ----------------------------------------
# ログ出力（ガジェット名ごとに logs/xxx.log に書く）
# ----------------------------------------
def log(gadget_name, message):
    log_path = f"logs/{gadget_name}.log"

    # ディレクトリが無ければ作る
    os.makedirs("logs", exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print(f"[LOG ERROR] {e}")


# ----------------------------------------
# フェイルセーフ保存
# temp → output に安全に保存する
# ----------------------------------------
def safe_save(surface, temp_path, output_path):
    """
    1. temp_path にまず保存
    2. temp が正常なら output に上書き
    3. 失敗したら output を維持（フェイルセーフ）
    """

    # ディレクトリが無ければ作る
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        # まず temp に保存
        pygame.image.save(surface, temp_path)

        # temp が正常に保存されたかチェック
        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            # output に上書き
            pygame.image.save(surface, output_path)
            return True
        else:
            print("[SAFE_SAVE] Temp file invalid, keeping previous output.")
            return False

    except Exception as e:
        print(f"[SAFE_SAVE ERROR] {e}")
        return False

def save_cached_uv(uvi, path="temp/uv.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = { "uvi": uvi }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)

def load_cached_uv(path="temp/uv.json"):
    if not os.path.exists(path):
        return { "uvi": 0 }

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return { "uvi": data.get("uvi", 0) }
    except:
        return { "uvi": 0 }

def save_last_uv_update(ts, path="temp/last_uv_update.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"ts": ts}, f)

def load_last_uv_update(path="temp/last_uv_update.json"):
    if not os.path.exists(path):
        return 0  # 初回は必ず更新させる

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("ts", 0)
    except:
        return 0