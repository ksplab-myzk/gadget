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
LIGHT_OUTPUT_PATH = os.path.join(BASE_DIR, "output", "calendar_sun_light.png")
LIGHT_TEMP_PATH = os.path.join(BASE_DIR, "airquality", "calendar_sun_light_temp.png")
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


def draw_calendar(card, current_date, fonts, light_mode=False):
    calendar_x = 52
    calendar_y = 112
    cell_w = 88
    cell_h = 48
    header_font, day_font, small_font = fonts
    month_label = current_date.strftime("%Y年%m月")
    text_color = (43, 56, 70) if light_mode else (255, 255, 255)
    weekday_color = (83, 96, 110) if light_mode else (225, 230, 238)
    sunday_color = (193, 76, 80) if light_mode else (255, 190, 190)
    saturday_color = (57, 115, 177) if light_mode else (190, 220, 255)
    draw_text(card, header_font, month_label, (calendar_x, 42), text_color)

    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    for column, weekday in enumerate(weekdays):
        color = sunday_color if weekday == "日" else saturday_color if weekday == "土" else weekday_color
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
                color = sunday_color
            elif column == 5:
                color = saturday_color
            else:
                color = text_color if light_mode else (238, 241, 246)
            label = day_font.render(str(day), True, color)
            card.blit(label, (x + 44 - label.get_width() // 2, y + 3))

def draw_sun_info(card, data, fonts, light_mode=False):
    _, day_font, small_font = fonts
    source_font = pygame.font.Font(FONT_PATH, 16)
    panel_x = 720
    panel_y = 34
    panel_w = 310
    panel_h = 406
    panel_color = (255, 255, 255, 225) if light_mode else (54, 68, 91, 210)
    panel_border = (190, 204, 216, 255) if light_mode else (255, 255, 255, 255)
    text_color = (43, 56, 70) if light_mode else (255, 255, 255)
    secondary_color = (88, 102, 116) if light_mode else (205, 214, 228)
    source_color = (104, 116, 128) if light_mode else (155, 165, 182)
    sunrise_label_color = (146, 91, 24) if light_mode else (255, 224, 158)
    sunset_label_color = (166, 78, 48) if light_mode else (255, 190, 157)
    pygame.draw.rect(card, panel_color, (panel_x, panel_y, panel_w, panel_h), border_radius=24)
    pygame.draw.rect(card, panel_border, (panel_x, panel_y, panel_w, panel_h), width=2, border_radius=24)

    draw_text(card, day_font, data["city"], (panel_x + 28, panel_y + 28), text_color)
    draw_text(card, small_font, data["date"].strftime("%Y/%m/%d (%a)"), (panel_x + 28, panel_y + 78), secondary_color)

    sunrise_icon = load_sun_icon("sunrise.png")
    card.blit(sunrise_icon, (panel_x + 32, panel_y + 126))
    draw_text(card, small_font, "日の出", (panel_x + 112, panel_y + 124), sunrise_label_color)
    draw_text(card, day_font, data["sunrise"].strftime("%H:%M"), (panel_x + 112, panel_y + 157), text_color)

    sunset_icon = load_sun_icon("sunset.png")
    card.blit(sunset_icon, (panel_x + 32, panel_y + 242))
    draw_text(card, small_font, "日の入り", (panel_x + 112, panel_y + 240), sunset_label_color)
    draw_text(card, day_font, data["sunset"].strftime("%H:%M"), (panel_x + 112, panel_y + 273), text_color)

    draw_text(card, source_font, "Provided by：OpenWeather", (panel_x + 28, panel_y + 364), source_color)


def draw_card(data, light_mode=False):
    pygame.init()
    card = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    for y in range(CARD_H):
        ratio = y / CARD_H
        if light_mode:
            color = (int(246 - 8 * ratio), int(249 - 7 * ratio), int(252 - 6 * ratio))
        else:
            color = (int(49 + 14 * ratio), int(62 + 18 * ratio), int(87 + 26 * ratio))
        pygame.draw.line(card, color, (0, y), (CARD_W, y))

    border_color = (190, 204, 216, 255) if light_mode else (255, 255, 255, 255)
    pygame.draw.rect(card, border_color, (0, 0, CARD_W, CARD_H), width=4, border_radius=28)
    fonts = (
        pygame.font.Font(FONT_PATH, 42),
        pygame.font.Font(FONT_PATH, 28),
        pygame.font.Font(FONT_PATH, 22),
    )
    draw_calendar(card, data["date"], fonts, light_mode=light_mode)
    draw_sun_info(card, data, fonts, light_mode=light_mode)
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
    light_card = draw_card(data, light_mode=True)
    dark_saved = safe_save(card, TEMP_PATH, OUTPUT_PATH)
    light_saved = safe_save(light_card, LIGHT_TEMP_PATH, LIGHT_OUTPUT_PATH)
    saved = dark_saved and light_saved
    pygame.quit()
    log(
        "calendar_sun",
        "OK: Updated dark and light images"
        if saved
        else "WARN: One or more image saves failed; previous outputs were retained",
    )
    return saved


if __name__ == "__main__":
    main()