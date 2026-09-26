import json
import os
import sys
from datetime import datetime, timedelta

import pygame
import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from common.utils import log, safe_save


CARD_W = 1080
CARD_H = 480
CONFIG_PATH = os.path.join(PROJECT_ROOT, "disaster_info", "config.json")
FONT_PATH = os.path.join(PROJECT_ROOT, "fonts", "NotoSansJP-Regular.ttf")
JMA_WARNING_URL = "https://www.jma.go.jp/bosai/warning/data/warning/{area_code}.json"
JMA_QUAKE_URL = "https://www.jma.go.jp/bosai/quake/data/list.json"
RIVER_BASE_URL = "https://www.river.go.jp/kawabou/file/files"
WARNING_NAMES = {
    "2": "暴風", "3": "暴風雪", "4": "大雨", "5": "大雪",
    "6": "風雪", "7": "雷", "8": "強風", "9": "波浪",
    "10": "高潮", "12": "洪水", "13": "高潮",
}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = json.load(file)
    config["output_path"] = os.path.join(PROJECT_ROOT, config["output_path"])
    config["temp_path"] = os.path.join(PROJECT_ROOT, config["temp_path"])
    return config


def get_json(url, params=None):
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_warnings(area_code):
    data = get_json(JMA_WARNING_URL.format(area_code=area_code))
    active = []
    for area_type in data.get("areaTypes", []):
        for area in area_type.get("areas", []):
            for warning in area.get("warnings", []):
                code = str(warning.get("code", ""))
                status = warning.get("status", "")
                if status not in ("解除", "", "発表なし"):
                    active.append(WARNING_NAMES.get(code, "注意報発表"))
    return sorted(set(active))


def fetch_latest_quake():
    items = get_json(JMA_QUAKE_URL)
    if not items:
        return None
    item = items[0]
    return {
        "time": item.get("at", ""),
        "area": item.get("anm", ""),
        "magnitude": item.get("mag", ""),
        "max_intensity": item.get("maxi", ""),
    }


def fetch_tamagawa_level(config):
    station_code = config.get("river_station_code", "")
    if not station_code:
        return None
    now = datetime.now().replace(second=0, microsecond=0)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.river.go.jp/kawabou/pcfull/tm",
        "Accept": "application/json,text/plain,*/*",
    }
    data = None
    for offset in range(0, 13):
        candidate = now.replace(minute=(now.minute // 5) * 5) \
            - timedelta(minutes=offset * 5)
        date_text = candidate.strftime("%Y%m%d")
        time_text = candidate.strftime("%H%M")
        url = f"{RIVER_BASE_URL}/tmlist/swstg/{date_text}/{time_text}/{station_code}.json"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            break
        if response.status_code != 404:
            response.raise_for_status()
    if data is None:
        return None
    observation = data.get("obsValue", {}) if isinstance(data, dict) else {}
    value = observation.get("stg")
    if value in (None, "", "-", "--"):
        return None
    height_from_levee = observation.get("stgHght")
    return {
        "value": float(value),
        "height_from_levee": float(height_from_levee) if height_from_levee is not None else None,
        "time": observation.get("obsTime", ""),
    }


def draw_text(surface, font, text, position, color=(238, 243, 247)):
    surface.blit(font.render(text, True, color), position)


def draw_panel(card, rect, title, lines, accent):
    x, y, width, height = rect
    pygame.draw.rect(card, (8, 20, 31, 210), rect, border_radius=16)
    pygame.draw.rect(card, accent, (x, y, 7, height), border_radius=4)
    title_font = pygame.font.Font(FONT_PATH, 25)
    body_font = pygame.font.Font(FONT_PATH, 22)
    draw_text(card, title_font, title, (x + 22, y + 16), accent)
    for index, line in enumerate(lines):
        draw_text(card, body_font, line, (x + 22, y + 54 + index * 32))


def draw_card(config, warnings, quake, river, errors):
    pygame.init()
    card = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    for y in range(CARD_H):
        ratio = y / CARD_H
        color = (int(21 + 13 * ratio), int(31 + 20 * ratio), int(43 + 23 * ratio))
        pygame.draw.line(card, color, (0, y), (CARD_W, y))
    pygame.draw.rect(card, (255, 255, 255, 110), (0, 0, CARD_W, CARD_H), width=4, border_radius=28)

    title_font = pygame.font.Font(FONT_PATH, 42)
    small_font = pygame.font.Font(FONT_PATH, 19)
    draw_text(card, title_font, "災害情報", (40, 24))
    draw_text(card, small_font, config["area_name"], (42, 78), (168, 211, 220))
    updated = datetime.now().strftime("%Y年%m月%d日 %H:%M 更新")
    updated_surface = small_font.render(updated, True, (180, 194, 204))
    card.blit(updated_surface, (CARD_W - updated_surface.get_width() - 40, 42))

    warning_lines = ["発表なし" if not warnings else "・".join(warnings)]
    draw_panel(card, (40, 116, 490, 112), "気象警報・注意報", warning_lines, (239, 173, 80) if warnings else (100, 198, 170))

    quake_lines = ["情報なし"] if not quake else [
        f"震源: {quake['area']}",
        f"M{quake['magnitude']} / 最大震度 {quake['max_intensity']} / {quake['time'][11:16]}",
    ]
    draw_panel(card, (550, 116, 490, 112), "最新の地震", quake_lines, (236, 119, 108) if quake else (100, 198, 170))

    if not river:
        river_lines = ["データなし"]
    else:
        levee_height = river["height_from_levee"]
        levee_text = "堤防からの高さ 未取得" if levee_height is None else f"堤防からの高さ {levee_height:.1f}m"
        river_lines = [
            f"水位 {river['value']:.2f}m（{levee_text}）",
            f"観測: {river['time']}",
        ]
    river_title = f"{config['river_name']}・{config['river_station_name']}"
    draw_panel(card, (40, 248, 490, 112), river_title, river_lines, (80, 176, 218))

    lightning = "雷注意報は発表なし" if "雷" not in warnings else "雷注意報 発表中"
    draw_panel(card, (550, 248, 490, 112), "雷", [lightning], (239, 173, 80) if "雷" in warnings else (100, 198, 170))

    footer_font = pygame.font.Font(FONT_PATH, 16)
    sources = "気象庁（警報・地震）・国土交通省 川の防災情報（水位）"
    draw_text(card, footer_font, sources, (40, 425), (150, 165, 177))
    if errors:
        draw_text(card, footer_font, "取得失敗: " + " / ".join(errors), (40, 450), (232, 151, 125))
    return card


def main():
    config = load_config()
    warnings, quake, river = [], None, None
    errors = []
    try:
        warnings = fetch_warnings(config["area_code"])
    except (requests.RequestException, ValueError, KeyError) as error:
        errors.append("警報")
        log("disaster_info", f"WARNING ERROR: {error}")
    try:
        quake = fetch_latest_quake()
    except (requests.RequestException, ValueError, KeyError, IndexError) as error:
        errors.append("地震")
        log("disaster_info", f"QUAKE ERROR: {error}")
    try:
        river = fetch_tamagawa_level(config)
    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        errors.append("水位")
        log("disaster_info", f"RIVER ERROR: {error}")

    card = draw_card(config, warnings, quake, river, errors)
    saved = safe_save(card, config["temp_path"], config["output_path"])
    pygame.quit()
    log("disaster_info", "OK: Updated" if saved else "WARN: Save failed")
    return saved


if __name__ == "__main__":
    main()
