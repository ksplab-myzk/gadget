import pygame
import json
import os
import time
from datetime import datetime
from common.utils import safe_save, log, save_cached_uv, load_cached_uv, load_last_uv_update, save_last_uv_update
import requests

CARD_W = 1080
CARD_H = 400

CONFIG_PATH = "airquality/config.json"
OUTPUT_PATH = "output/airquality.png"
TEMP_PATH = "temp/airquality_temp.png"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_aqi(lat, lon, api_key):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()["list"][0]

        return {
            "aqi": data["main"]["aqi"],
            "pm2_5": data["components"]["pm2_5"],
            "pm10": data["components"]["pm10"],
            "o3": data["components"]["o3"],
            "no2": data["components"]["no2"],
            "so2": data["components"]["so2"],
            "co": data["components"]["co"]
        }
    except Exception as e:
        log("weather_summary", f"AQI ERROR: {e}")
        return None


def fetch_hourly_forecast(city, api_key):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=ja"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()["list"]

        # 先頭6?12件を使う（3時間刻み）
        hourly = []
        for item in data[:8]:  # 24時間分
            hourly.append({
                "time": datetime.fromtimestamp(item["dt"]),
                "temp": item["main"]["temp"],
                "pop": item.get("pop", 0.0),
                "icon": item["weather"][0]["icon"]
            })

        return hourly

    except Exception as e:
        log("weather_summary", f"HOURLY ERROR: {e}")
        return None

# def fetch_uv_index(lat, lon, api_key):
#     # 無料プランで使える One Call API 2.5
#     url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid={api_key}"
#     try:
#         r = requests.get(url, timeout=5)
#         r.raise_for_status()
#         data = r.json()

#         # UVが存在しない（夜間など）場合は0にする
#         uvi = data.get("current", {}).get("uvi", 0)

#         return { "uvi": uvi }

#     except Exception as e:
#         log("weather_summary", f"UV ERROR: {e}")
#         # None を返すと描画側が落ちるので必ず辞書を返す
#         return { "uvi": 0 }

def fetch_uv_index(lat, lon, api_key):
    url = "https://api.openuv.io/api/v1/uv"
    headers = {
        "x-access-token": api_key
    }
    params = {
        "lat": lat,
        "lng": lon
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=5)
        r.raise_for_status()
        data = r.json()

        uvi = data.get("result", {}).get("uv", 0)
        return { "uvi": uvi }

    except Exception as e:
        log("weather_summary", f"UV ERROR: {e}")
        return { "uvi": 0 }


def fetch_jma_precip():
    url = "https://www.jma.go.jp/bosai/forecast/data/forecast/140000.json"
    data = requests.get(url).json()

    # 神奈川県の予報（0番目）
    pops = data[0]["timeSeries"][1]["areas"][0]["pops"]  # ["10","20","50","70"]

    # 3時間ごとの降水確率を1時間ごとに展開
    hourly_pop = []
    for pop in pops:
        p = int(pop)
        hourly_pop.extend([p, p, p])  # 3時間分を展開

    return hourly_pop  # 15時間分


def fetch_all_data(config, last_uv_update):
    lat = config["lat"]
    lon = config["lon"]
    city = config["city"]
    api_key = config["api_key"]
    open_uv_api_key = config["open_uv_api_key"]

    now = time.time()

    # 降水確率はJMAから取得
    # jma_pop = fetch_jma_precip()

    # UVは1時間に1回だけ更新
    if now - last_uv_update > config["update_interval_uv"]:
        uv = fetch_uv_index(lat, lon, open_uv_api_key)
        save_cached_uv(uv["uvi"])
        last_uv_update = now
    else:
        uv = load_cached_uv()

    return {
        "aqi": fetch_aqi(lat, lon, api_key),
        "hourly": fetch_hourly_forecast(city, api_key),
        "pop_hourly": fetch_jma_precip(),
        "uv": uv,
        "timestamp": datetime.now()
    }, last_uv_update

def draw_left_bottom_round_rect(surface, color, rect, radius):
    x, y, w, h = rect

    # 上側の直角部分
    pygame.draw.rect(surface, color, (x, y, w, h - radius))

    # 下側中央の直線部分
    pygame.draw.rect(surface, color, (x + radius, y + h - radius, w - radius, radius))

    # 左下の円弧（本物の丸角）
    pygame.draw.circle(surface, color, (x + radius, y + h - radius), radius)

def draw_right_bottom_round_rect(surface, color, rect, radius):
    x, y, w, h = rect

    # 上側の直角部分
    pygame.draw.rect(surface, color, (x, y, w, h - radius))

    # 下側中央の直線部分
    pygame.draw.rect(surface, color, (x, y + h - radius, w - radius, radius))

    # 右下の円弧（本物の丸角）
    pygame.draw.circle(surface, color, (x + w - radius, y + h - radius), radius)

def draw_background(card):
    # 背景グラデーション
    bg = pygame.Surface((1080, CARD_H), pygame.SRCALPHA)
    top = pygame.Color("#2A2E37")
    bottom = pygame.Color("#3A3F4A")

    for y in range(400):
        ratio = y / 400
        r = top.r + (bottom.r - top.r) * ratio
        g = top.g + (bottom.g - top.g) * ratio
        b = top.b + (bottom.b - top.b) * ratio
        pygame.draw.line(bg, (int(r), int(g), int(b)), (0, y), (1080, y))

    bg.set_alpha(120)
    card.blit(bg, (0, 0))

    # 影
    shadow = pygame.Surface((1080, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0,0,0,80), (0,0,1080,CARD_H), border_radius=32)
    shadow.set_alpha(160)
    card.blit(shadow, (6, 6))

    # 外枠
    border = pygame.Surface((1080, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(border, (255,255,255), (0,0,1080,CARD_H), width=6, border_radius=32)
    border.set_alpha(220)
    card.blit(border, (0, 0))

def draw_header(card, timestamp):
    header = pygame.Surface((1080, 60), pygame.SRCALPHA)
    pygame.draw.rect(header, (0,0,0,120), (0,0,1080,60), border_radius=16)

    font = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 40)
    title = font.render("気温・降水確率", True, (255,255,255))
    card.blit(title, (40, 8))

    font = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 24)
    info = timestamp.strftime("%Y年%m月%d日 %H:%M 時点")
    info_txt = font.render(info, True, (255,255,255))
    card.blit(info_txt, (1080 - info_txt.get_width() - 40, 8))

    src = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 16).render("Provided by：OpenWeather・OpenUV・気象庁", True, (255,255,255))
    card.blit(src, (1080 - src.get_width() - 40, 45))

def draw_temp_precip_graph(card, hourly, pop_hourly):
    graph = pygame.Surface((1080, 260), pygame.SRCALPHA)

    # 気温の範囲
    temps = [h["temp"] for h in hourly]
    min_t = min(temps) - 2
    max_t = max(temps) + 2

    # X座標
    step_x = 1080 / len(hourly)

    # 降水確率（棒グラフ）
    for i, h in enumerate(pop_hourly):
        pop = h / 100
        bar_h = int(pop * 190)
        x = int(i * step_x + step_x / 2 - 20)
        pygame.draw.rect(graph, (80,120,255,190), (x, 240 - bar_h, 40, bar_h))

        font_small = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 20)
        pop_v = pop*100
        pop_text = font_small.render(f"{pop_v}%", True, (200,200,200))
        card.blit(pop_text, (x , 80))

    # 折れ線（気温）
    points = []
    for i, h in enumerate(hourly):
        x = int(i * step_x + step_x / 2)
        ratio = (h["temp"] - min_t) / (max_t - min_t)
        y = int(240 - ratio * 200)
        points.append((x, y))

        font_small = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 20)
        temp_text = font_small.render(f"{h['temp']:.1f}°", True, (255,255,255))
        card.blit(temp_text, (x -20, y +20))

    # 折れ線描画
    for i in range(len(points) - 1):
        pygame.draw.line(graph, (255,255,255), points[i], points[i+1], 4)

    # プロット点
    for x, y in points:
        pygame.draw.circle(graph, (255,255,255), (x, y), 8)

    # 時刻ラベル
    font = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 20)
    for i, h in enumerate(hourly):
        t = h["time"].strftime("%H時")
        txt = font.render(t, True, (255,255,255))
        x = int(i * step_x + step_x / 2 - txt.get_width() / 2)
        graph.blit(txt, (x, 250 - 20))

    card.blit(graph, (0, 60))

def draw_temp_precip_graph2(card, hourly, pop_hourly):
    graph = pygame.Surface((1080, 260), pygame.SRCALPHA)

    # 気温の範囲
    temps = [h["temp"] for h in hourly]
    min_t = min(temps) - 2
    max_t = max(temps) + 2

    step_x = 1080 / len(hourly)
    font_small = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 20)

    # -----------------------------
    # 1. 降水確率（棒グラフ）
    # -----------------------------
    pop_positions = []  # 後で重なり判定に使う

    for i, pop_val in enumerate(pop_hourly):
        pop = pop_val / 100
        bar_h = int(pop * 190)
        x = int(i * step_x + step_x / 2 - 20)

        # 100%背景（薄いグレー）
        bg_bar = pygame.Surface((40, 190), pygame.SRCALPHA)
        bg_bar.fill((180, 180, 180, 80))  # 薄いグレー＋半透明
        graph.blit(bg_bar, (x, 240 - 190))

        y = 240 - bar_h

        # グラデーションバー
        bar = pygame.Surface((40, bar_h), pygame.SRCALPHA)

        for j in range(bar_h):
            ratio = j / bar_h
            r = 80 * (1 - ratio) + 40 * ratio
            g = 120 * (1 - ratio) + 80 * ratio
            b = 255 * (1 - ratio) + 200 * ratio
            pygame.draw.line(bar, (int(r), int(g), int(b), 200), (0, j), (40, j))
        graph.blit(bar, (x, y))

        # ハイライト
        highlight = pygame.Surface((40, 4), pygame.SRCALPHA)
        highlight.fill((255, 255, 255, 80))
        graph.blit(highlight, (x, y))

        # バッジ位置（固定）
        pop_y = 20

        # バッジ
        badge = pygame.Surface((60, 30), pygame.SRCALPHA)
        pygame.draw.rect(badge, (0, 0, 0, 120), (0, 0, 60, 30), border_radius=8)
        graph.blit(badge, (x - 10, pop_y))

        # テキスト
        pop_text = font_small.render(f"{int(pop*100)}%", True, (255,255,255))
        graph.blit(pop_text, (x , pop_y ))

        pop_positions.append((x, pop_y))

    # -----------------------------
    # 2. 気温折れ線
    # -----------------------------
    temp_positions = []
    points = []

    for i, h in enumerate(hourly):
        x = int(i * step_x + step_x / 2)
        ratio = (h["temp"] - min_t) / (max_t - min_t)
        y = int(240 - ratio * 200)
        points.append((x, y))

        # バッジ位置（折れ線の上に揃える）
        temp_y = y + 5

        # 重なり防止（降水確率と近い場合）
        pop_x, pop_y = pop_positions[i]
        if abs(temp_y - pop_y) < 30:
            temp_y += 5

        # バッジ
        badge = pygame.Surface((70, 30), pygame.SRCALPHA)
        pygame.draw.rect(badge, (0, 0, 0, 120), (0, 0, 70, 30), border_radius=8)
        graph.blit(badge, (x - 35, temp_y + 5))

        # テキスト
        temp_text = font_small.render(f"{h['temp']:.1f}°", True, (255,255,255))
        graph.blit(temp_text, (x - 25, temp_y + 5))

        temp_positions.append((x, temp_y))

    # -----------------------------
    # 3. 折れ線（グラデーション）
    # -----------------------------
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i+1]

        for t in range(4):
            ratio = t / 4
            r = 255 * (1 - ratio) + 120 * ratio
            g = 255 * (1 - ratio) + 180 * ratio
            b = 255 * (1 - ratio) + 255 * ratio
            pygame.draw.line(graph, (int(r), int(g), int(b)), (x1, y1), (x2, y2), 4 - t)

    # プロット点（影付き）
    for x, y in points:
        pygame.draw.circle(graph, (0,0,0,120), (x+2, y+2), 10)
        pygame.draw.circle(graph, (255,255,255), (x, y), 8)

    # -----------------------------
    # 4. 時刻ラベル
    # -----------------------------
    font = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 20)
    for i, h in enumerate(hourly):
        t = h["time"].strftime("%H時")
        txt = font.render(t, True, (255,255,255))
        x = int(i * step_x + step_x / 2 - txt.get_width() / 2)
        graph.blit(txt, (x, 230))

    card.blit(graph, (0, 60))

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_text_color(bg):

    # RGBA → RGB に変換
    if len(bg) == 4:
        bg = bg[:3]

    r, g, b = bg
    luminance = 0.299*r + 0.587*g + 0.114*b
    return (0,0,0) if luminance > 150 else (255,255,255)


def draw_aqi_card(card, aqi_data):
    aqi = aqi_data["aqi"]
    pm25 = aqi_data["pm2_5"]
    pm10 = aqi_data["pm10"]

    colors = {
        1: "#80E2E2",
        2: "#7BB923",
        3: "#FFC000",
        4: "#FF5000",
        5: "#AA00B0"
    }

    bg = pygame.Surface((540, 130), pygame.SRCALPHA)
    # pygame.draw.rect(bg, pygame.Color(colors[aqi]), (0,0,540,180), border_radius=0)
    draw_left_bottom_round_rect(card, (colors[aqi]),  (6,320,534,74), 25)

    bg.set_alpha(180)
    card.blit(bg, (0, 320))

    font_big = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 28)
    font_small = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 24)

    text_color = get_text_color(hex_to_rgb(colors[aqi]))
    txt = font_big.render(f"空気質指数：{aqi}", True, text_color)
 
    card.blit(txt, (40, 320))

    pm_txt = font_small.render(f"PM2.5:{pm25:.1f} / PM10:{pm10:.1f}", True, text_color)
    card.blit(pm_txt, (40, 355))


def draw_uv_card(card, uv_data):
    uv = uv_data["uvi"]

    if uv <= 2: color = "#54B3B8"
    elif uv <= 5: color = "#FFEB3B"
    elif uv <= 7: color = "#FF9800"
    elif uv <= 10: color = "#F44336"
    else: color = "#D86ECC"

    bg = pygame.Surface((540, 130), pygame.SRCALPHA)
    # pygame.draw.rect(bg, pygame.Color(color), (0,0,540,180), border_radius=0)
    draw_right_bottom_round_rect(card, color,  (540,320,534,74), 25)

    bg.set_alpha(180)
    card.blit(bg, (540, 320))

    font_big = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 28)
    font_small = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 24)

    text_color = get_text_color(hex_to_rgb(color))

    txt = font_big.render(f"紫外線指数(UV)：{uv:.1f}", True, text_color)
    card.blit(txt, (580, 320))

    cat = (
        "弱い" if uv <= 2 else
        "中程度" if uv <= 5 else
        "強い" if uv <= 7 else
        "非常に強い" if uv <= 10 else
        "危険"
    )

    cat_txt = font_small.render(cat, True, text_color)
    card.blit(cat_txt, (580, 355))

def generate_weather_summary(data):
    pygame.init()
    card = pygame.Surface((1080, CARD_H), pygame.SRCALPHA)

    draw_background(card)
    draw_header(card, data["timestamp"])
    draw_temp_precip_graph2(card, data["hourly"], data["pop_hourly"])
    draw_aqi_card(card, data["aqi"])
    draw_uv_card(card, data["uv"])

    return card


def main():

    config = load_config()

    # 前回 UV をいつ取得したか読み込む
    last_uv_update = load_last_uv_update()

    # UV の最終更新時刻（初回は 0 にして必ず更新させる）
    # last_uv_update = 0

    data, last_uv_update  = fetch_all_data(config, last_uv_update )
    if data is None:
        log("airquality", "WARN: Using previous image")
        return False

    # UV の最終更新時刻を保存
    save_last_uv_update(last_uv_update)

    card = generate_weather_summary(data)

    ok = safe_save(card, "temp/weather_summary_temp.png", "output/weather_summary.png")

    if ok:
        log("weather_summary", "OK: Updated")
    else:
        log("weather_summary", "WARN: Using previous output")

    return ok

if __name__ == "__main__":
    main()
