import calendar
import json
import os
from datetime import datetime, timedelta, timezone

import pygame
import requests

from common.utils import log, safe_save


CARD_W = 1080
CARD_H = 480

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "airquality", "config.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "calendar_sun.png")
TEMP_PATH = os.path.join(BASE_DIR, "airquality", "calendar_sun_temp.png")
FONT_PATH = os.path.join(BASE_DIR, "fonts", "NotoSansJP-Regular.ttf")
ICON_DIR = os.path.join(BASE_DIR, "icons")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def fetch_data(config):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": config["city"],
        "appid": config["api_key"],
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        weather = response.json()
        local_timezone = timezone(timedelta(seconds=weather.get("timezone", 0)))
        local_now = datetime.now(timezone.utc).astimezone(local_timezone)

        return {
            "date": local_now,
            "sunrise": datetime.fromtimestamp(
                weather["sys"]["sunrise"], timezone.utc
            ).astimezone(local_timezone),
            "sunset": datetime.fromtimestamp(
                weather["sys"]["sunset"], timezone.utc
            ).astimezone(local_timezone),
            "city": "川崎市",
        }
    except (KeyError, requests.RequestException, ValueError) as error:
        log("calendar_sun", f"ERROR: {error}")
        return None


def draw_text(surface, font, text, position, color=(255, 255, 255)):
    surface.blit(font.render(text, True, color), position)


def load_sun_icon(filename):
    icon_path = os.path.join(ICON_DIR, filename)
    icon = pygame.image.load(icon_path)
    return pygame.transform.smoothscale(icon, (72, 72))


def draw_calendar(card, current_date, fonts):
    calendar_x = 52
    calendar_y = 112
    cell_w = 88
    cell_h = 48
    header_font, day_font, small_font = fonts
    month_label = current_date.strftime("%Y年%m月")
    draw_text(card, header_font, month_label, (calendar_x, 42))

    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    for column, weekday in enumerate(weekdays):
        color = (255, 190, 190) if weekday == "日" else (190, 220, 255) if weekday == "土" else (225, 230, 238)
        draw_text(card, day_font, weekday, (calendar_x + column * cell_w + 32, calendar_y), color)

    month = calendar.monthcalendar(current_date.year, current_date.month)
    for row, week in enumerate(month):
        for column, day in enumerate(week):
            if day == 0:
                continue
            x = calendar_x + column * cell_w
            y = calendar_y + 42 + row * cell_h
            if day == current_date.day:
                highlight_y = y + 6
                pygame.draw.rect(card, (240, 174, 82), (x + 16, highlight_y, 56, 42), border_radius=10)
                color = (35, 43, 58)
            elif column == 6:
                color = (255, 190, 190)
            elif column == 5:
                color = (190, 220, 255)
            else:
                color = (238, 241, 246)
            label = day_font.render(str(day), True, color)
            card.blit(label, (x + 44 - label.get_width() // 2, y + 3))

def draw_sun_info(card, data, fonts):
    _, day_font, small_font = fonts
    source_font = pygame.font.Font(FONT_PATH, 16)
    panel_x = 720
    panel_y = 34
    panel_w = 310
    panel_h = 406
    pygame.draw.rect(card, (24, 31, 49, 210), (panel_x, panel_y, panel_w, panel_h), border_radius=24)
    pygame.draw.rect(card, (255, 255, 255, 80), (panel_x, panel_y, panel_w, panel_h), width=2, border_radius=24)

    draw_text(card, day_font, data["city"], (panel_x + 28, panel_y + 28))
    draw_text(card, small_font, data["date"].strftime("%Y/%m/%d (%a)"), (panel_x + 28, panel_y + 78), (205, 214, 228))

    sunrise_icon = load_sun_icon("sunrise.png")
    card.blit(sunrise_icon, (panel_x + 32, panel_y + 126))
    draw_text(card, small_font, "日の出", (panel_x + 112, panel_y + 124), (255, 224, 158))
    draw_text(card, day_font, data["sunrise"].strftime("%H:%M"), (panel_x + 112, panel_y + 157))

    sunset_icon = load_sun_icon("sunset.png")
    card.blit(sunset_icon, (panel_x + 32, panel_y + 242))
    draw_text(card, small_font, "日の入り", (panel_x + 112, panel_y + 240), (255, 190, 157))
    draw_text(card, day_font, data["sunset"].strftime("%H:%M"), (panel_x + 112, panel_y + 273))

    draw_text(card, source_font, "Provided by：OpenWeather", (panel_x + 28, panel_y + 364), (155, 165, 182))


def draw_card(data):
    pygame.init()
    card = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    for y in range(CARD_H):
        ratio = y / CARD_H
        color = (int(21 + 12 * ratio), int(29 + 16 * ratio), int(49 + 24 * ratio))
        pygame.draw.line(card, color, (0, y), (CARD_W, y))

    pygame.draw.rect(card, (255, 255, 255, 100), (0, 0, CARD_W, CARD_H), width=4, border_radius=28)
    fonts = (
        pygame.font.Font(FONT_PATH, 42),
        pygame.font.Font(FONT_PATH, 28),
        pygame.font.Font(FONT_PATH, 22),
    )
    draw_calendar(card, data["date"], fonts)
    draw_sun_info(card, data, fonts)
    return card


def main():
    try:
        config = load_config()
        data = fetch_data(config)
    except (OSError, KeyError, json.JSONDecodeError) as error:
        log("calendar_sun", f"ERROR: {error}")
        data = None

    if data is None:
        log("calendar_sun", "WARN: Using previous image")
        return False

    card = draw_card(data)
    saved = safe_save(card, TEMP_PATH, OUTPUT_PATH)
    pygame.quit()
    log("calendar_sun", "OK: Updated" if saved else "WARN: Save failed")
    return saved


if __name__ == "__main__":
    main()