import pygame
import requests
import json
import sys
import os
from datetime import datetime

# -----------------------------
# 設定
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "weather.png")
API_KEY = "9374cbd85e6aa5d3605d3e659ba39a28"
CITY = "Kawasaki,jp"

FONT_PATH = os.path.join(BASE_DIR, "fonts", "NotoSansJP-Regular.ttf")
ICON_DIR = os.path.join(BASE_DIR, "icons")   # ← 240pxアイコン推奨

CARD_W = 1080
CARD_H = 400

COLOR_MAP = {
    "Clear": ("#3FA9F5", "#6FC8FF"),
    "Clouds": ("#9EA7B8", "#C3C8D0"),
    "Rain": ("#4B6C8B", "#6A8AA5"),
    "Drizzle": ("#6C8FA8", "#8AAAC0"),
    "Thunderstorm": ("#3B3F5C", "#4C506F"),
    "Snow": ("#E3E7ED", "#FFFFFF"),
    "Fog": ("#C9D1D9", "#E2E6EA"),
    "Mist": ("#D5DCE2", "#E8EDF0"),
    "Haze": ("#E0D8C8", "#F0E8D8"),
}

# -----------------------------
# グラデーション描画
# -----------------------------
def draw_vertical_gradient(surface, top_color, bottom_color):
    top = pygame.Color(top_color)
    bottom = pygame.Color(bottom_color)
    height = surface.get_height()
    for y in range(height):
        ratio = y / height
        r = top.r + (bottom.r - top.r) * ratio
        g = top.g + (bottom.g - top.g) * ratio
        b = top.b + (bottom.b - top.b) * ratio
        pygame.draw.line(surface, (int(r), int(g), int(b)), (0, y), (surface.get_width(), y))

# -----------------------------
# 天気取得（フェイルセーフ）
# -----------------------------
def fetch_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=ja"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[ERROR] Weather API failed: {e}")
        return None

# -----------------------------
# 天気カード画像生成
# -----------------------------
def generate_weather_image():
    pygame.init()

    card = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)

    # API取得
    data = fetch_weather()
    if data is None:
        print("[WARN] Using previous image due to API failure.")
        return False

    # 天気情報抽出
    weather_main = data["weather"][0]["main"]
    desc = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    feels = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    wind = data["wind"]["speed"]

    # --- 追加：情報時点（UNIX秒 → 日本時間） ---
    dt_unix = data.get("dt", None)
    if dt_unix:
        dt_jst = datetime.fromtimestamp(dt_unix)
        dt_text = dt_jst.strftime("%Y年%m月%d日 %H:%M 時点")
    else:
        dt_text = "時刻情報なし"

    # -------------------------
    # 背景レイヤー（強透過）
    # -------------------------
    top_color, bottom_color = COLOR_MAP.get(weather_main, ("#888888", "#AAAAAA"))
    bg = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    draw_vertical_gradient(bg, top_color, bottom_color)

    mask = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255,255,255), (0,0,CARD_W,CARD_H), border_radius=32)
    bg.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
    bg.set_alpha(120)
    card.blit(bg, (0, 0))

    # -------------------------
    # 影レイヤー（中透過）
    # -------------------------
    shadow = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0,0,0,80), (0,0,CARD_W,CARD_H), border_radius=32)
    shadow.set_alpha(160)
    card.blit(shadow, (6, 6))

    # -------------------------
    # 外枠レイヤー
    # -------------------------
    border = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(border, (255,255,255), (0,0,CARD_W,CARD_H), width=6, border_radius=32)
    border.set_alpha(220)
    card.blit(border, (0, 0))

    # -------------------------
    # 前景レイヤー（弱透過）
    # -------------------------
    fg = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)

    # アイコン
    icon_file = f"{ICON_DIR}/{weather_main.lower()}.png"
    if os.path.exists(icon_file):
        icon = pygame.image.load(icon_file)
        icon.set_alpha(250)
        fg.blit(icon, (60, 80))

    # テキスト
    font_big = pygame.font.Font(FONT_PATH, 96)
    font_mid = pygame.font.Font(FONT_PATH, 64)
    font_small = pygame.font.Font(FONT_PATH, 48)

    txt1 = font_big.render(desc, True, (255,255,255))
    txt2 = font_mid.render(f"気温 {temp:.1f}°C / 体感 {feels:.1f}°C", True, (255,255,255))
    txt3 = font_small.render(f"湿度 {humidity}%   風 {wind}m/s", True, (255,255,255))

    txt1.set_alpha(250)
    txt2.set_alpha(250)
    txt3.set_alpha(250)

    fg.blit(txt1, (300, 30))
    fg.blit(txt2, (300, 150))
    fg.blit(txt3, (300, 240))

    # --- 追加：情報時点と出典 ---
    font_info = pygame.font.Font(FONT_PATH, 32)
    font_src  = pygame.font.Font(FONT_PATH, 24)

    info_txt = font_info.render(dt_text, True, (255,255,255))
    src_txt  = font_src.render("Provided by：OpenWeather", True, (255,255,255))

    info_txt.set_alpha(250)
    src_txt.set_alpha(250)

    # 右下に配置
    fg.blit(info_txt, (CARD_W - info_txt.get_width() - 40, CARD_H - 90))
    fg.blit(src_txt,  (CARD_W - src_txt.get_width()  - 40, CARD_H - 50))

    card.blit(fg, (0, 0))

    # 保存
    pygame.image.save(card, OUTPUT_PATH)
    print(f"[OK] Weather image updated: {OUTPUT_PATH}")
    return True

# -----------------------------
# メイン処理
# -----------------------------
if __name__ == "__main__":
    success = generate_weather_image()
    if not success:
        print("[FAILSAFE] Keeping previous weather.png")
