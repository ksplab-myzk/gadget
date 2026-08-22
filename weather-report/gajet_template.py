import pygame
import json
import os
from datetime import datetime
from common.utils import safe_save, log
import requests


CARD_W = 1080
CARD_H = 480

CONFIG_PATH = "generators/airquality/config.json"
OUTPUT_PATH = "output/airquality.png"
TEMP_PATH = "temp/airquality_temp.png"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_data():
    """
    ここにデータ取得処理を書く
    API / RSS / ローカルファイルなど
    """
    try:
        # 仮データ（ここをAPIに置き換える）
        return {
            "title": "空気質",
            "value": "AQI 42（良好）",
            "timestamp": datetime.now()
        }
    except Exception as e:
        log("airquality", f"ERROR: {e}")
        return None

def draw_card(data):
    pygame.init()
    card = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)

    # 背景
    bg = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(bg, (60, 100, 140), (0,0,CARD_W,CARD_H), border_radius=32)
    bg.set_alpha(120)
    card.blit(bg, (0,0))

    # 外枠
    border = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(border, (255,255,255), (0,0,CARD_W,CARD_H), width=6, border_radius=32)
    border.set_alpha(220)
    card.blit(border, (0,0))

    # テキスト
    font_big = pygame.font.Font("generators/airquality/assets/fonts/NotoSansJP-Regular.otf", 72)
    font_small = pygame.font.Font("generators/airquality/assets/fonts/NotoSansJP-Regular.otf", 48)

    txt1 = font_big.render(data["title"], True, (255,255,255))
    txt2 = font_small.render(str(data["value"]), True, (255,255,255))

    card.blit(txt1, (60, 120))
    card.blit(txt2, (60, 220))

    # 時刻
    info = data["timestamp"].strftime("%Y年%m月%d日 %H:%M 時点")
    txt_info = font_small.render(info, True, (255,255,255))
    card.blit(txt_info, (CARD_W - txt_info.get_width() - 40, CARD_H - 80))

    return card

def main():
    data = fetch_data()
    if data is None:
        log("airquality", "WARN: Using previous image")
        return False

    card = draw_card(data)

    # temp → output（フェイルセーフ）
    safe_save(card, TEMP_PATH, OUTPUT_PATH)

    log("airquality", "OK: Updated")
    return True

if __name__ == "__main__":
    main()
