import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

import pygame
import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from common.utils import log, safe_save


CARD_W = 1080
CARD_H = 480
CONFIG_PATH = os.path.join(PROJECT_ROOT, "space_weather", "config.json")
FONT_PATH = os.path.join(PROJECT_ROOT, "fonts", "NotoSansJP-Regular.ttf")
ICON_DIR = os.path.join(PROJECT_ROOT, "icons")
FLARE_IMAGES = {
    "few": "furea_low.png",
    "normal": "furea_norm.png",
    "many": "furea_high.png",
}
FLARE_URL = "https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json"
CLASS_RANK = {"A": 0, "B": 1, "C": 2, "M": 3, "X": 4}
LEVELS = {
    "few": {"label": "少ない", "color": (112, 190, 151)},
    "normal": {"label": "普通", "color": (237, 183, 86)},
    "many": {"label": "多い", "color": (229, 119, 108)},
}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    window_hours = config.get("window_hours")
    few_max_count = config.get("few_max_count")
    many_min_count = config.get("many_min_count")
    minimum_flare_class = config.get("minimum_flare_class")
    descriptions = config.get("descriptions")
    if not isinstance(window_hours, int) or window_hours <= 0:
        raise ValueError("window_hours must be a positive integer")
    if not isinstance(few_max_count, int) or few_max_count < 0:
        raise ValueError("few_max_count must be a non-negative integer")
    if not isinstance(many_min_count, int) or many_min_count <= few_max_count:
        raise ValueError("many_min_count must be greater than few_max_count")
    if minimum_flare_class not in CLASS_RANK:
        raise ValueError("minimum_flare_class must be A, B, C, M, or X")
    if not isinstance(descriptions, dict) or any(
        not isinstance(descriptions.get(level), str)
        or not descriptions[level].strip()
        for level in LEVELS
    ):
        raise ValueError("descriptions must define non-empty few, normal, and many text")
    if not isinstance(config.get("explanation"), str) or not config["explanation"].strip():
        raise ValueError("explanation must be a non-empty string")

    for path_key in ("output_path", "temp_path"):
        path = config.get(path_key)
        if not isinstance(path, str) or not path.strip():
            raise ValueError(f"{path_key} must be a non-empty path")
        config[path_key] = os.path.join(PROJECT_ROOT, path)
    return config


def get_json(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError("GOES flare response must be a JSON array")
    return data


def _parse_utc(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def count_flares(events, window_hours, minimum_flare_class, now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    cutoff = now.astimezone(timezone.utc) - timedelta(hours=window_hours)
    minimum_rank = CLASS_RANK[minimum_flare_class]
    count = 0

    for event in events:
        if not isinstance(event, dict):
            continue
        event_time = _parse_utc(event.get("max_time") or event.get("time_tag"))
        match = re.match(r"^\s*(A|B|C|M|X)\s*\d", str(event.get("max_class", "")).upper())
        if event_time is None or match is None:
            continue
        if cutoff <= event_time <= now.astimezone(timezone.utc):
            if CLASS_RANK[match.group(1)] >= minimum_rank:
                count += 1
    return count


def classify_count(count, config):
    if count <= config["few_max_count"]:
        return "few"
    if count >= config["many_min_count"]:
        return "many"
    return "normal"


def _wrap_text(text, font, max_width):
    lines = []
    line = ""
    for character in text:
        if character == "\n":
            lines.append(line)
            line = ""
            continue
        candidate = line + character
        if line and font.size(candidate)[0] > max_width:
            lines.append(line)
            line = character
        else:
            line = candidate
    if line or not lines:
        lines.append(line)
    return lines


def draw_card(config, level, updated_at):
    pygame.init()
    card = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    top = pygame.Color("#493238")
    bottom = pygame.Color("#5C3C42")
    for y in range(CARD_H):
        ratio = y / CARD_H
        color = tuple(
            int(top[index] + (bottom[index] - top[index]) * ratio)
            for index in range(3)
        )
        pygame.draw.line(card, color, (0, y), (CARD_W, y))

    white = (255, 255, 255)
    pygame.draw.rect(card, (*white, 255), (0, 0, CARD_W, CARD_H), width=4, border_radius=28)
    title_font = pygame.font.Font(FONT_PATH, 42)
    body_font = pygame.font.Font(FONT_PATH, 20)
    detail_font = pygame.font.Font(FONT_PATH, 22)
    state = LEVELS[level]
    title = title_font.render("宇宙天気：今日の太陽活動状況", True, white)
    card.blit(title, (42, 28))

    updated = detail_font.render(
        f"{updated_at.astimezone().strftime('%Y年%m月%d日 %H:%M')} 更新",
        True,
        (225, 233, 239),
    )
    card.blit(updated, (CARD_W - updated.get_width() - 42, 44))

    inner_frame = pygame.Rect(42, 112, 996, 326)
    pygame.draw.rect(card, (48, 34, 37), inner_frame, border_radius=18)
    pygame.draw.rect(card, (128, 128, 128), inner_frame, width=2, border_radius=18)
    flare_image = pygame.image.load(os.path.join(ICON_DIR, FLARE_IMAGES[level]))
    image_width, image_height = flare_image.get_size()
    scale = min(84 / image_width, 84 / image_height)
    image_size = (int(image_width * scale), int(image_height * scale))
    flare_image = pygame.transform.smoothscale(flare_image, image_size)
    card.blit(flare_image, (70, 122 + (84 - image_size[1]) // 2))

    state_font = pygame.font.Font(FONT_PATH, 48)
    state_surface = state_font.render(state["label"], True, state["color"])
    card.blit(state_surface, (172, 132))

    heading = pygame.font.Font(FONT_PATH, 23).render("生活への影響", True, white)
    card.blit(heading, (70, 226))
    text_y = 258
    for line in config["descriptions"][level].splitlines():
        for wrapped in _wrap_text(line, body_font, 920):
            text = body_font.render(wrapped, True, (238, 243, 247))
            card.blit(text, (93, text_y))
            text_y += 22

    explanation_heading = pygame.font.Font(FONT_PATH, 20).render("宇宙天気とは", True, white)
    explanation_heading_y = text_y + 26
    card.blit(explanation_heading, (70, explanation_heading_y))
    explanation_font = pygame.font.Font(FONT_PATH, 15)
    explanation_y = explanation_heading_y + 25
    for line in config["explanation"].splitlines():
        for wrapped in _wrap_text(line, explanation_font, 920):
            text = explanation_font.render(wrapped, True, (238, 243, 247))
            card.blit(text, (93, explanation_y))
            explanation_y += 17

    source_font = pygame.font.Font(FONT_PATH, 16)
    source = source_font.render("Data: NOAA SWPC GOES X-ray flare observations", True, (210, 221, 229))
    card.blit(source, (70, 444))
    return card


def main(debug_level=None):
    try:
        config = load_config()
        events = get_json(FLARE_URL)
        now = datetime.now(timezone.utc)
        count = count_flares(
            events,
            config["window_hours"],
            config["minimum_flare_class"],
            now,
        )
        level = debug_level or classify_count(count, config)
        card = draw_card(config, level, now)
        saved = safe_save(card, config["temp_path"], config["output_path"])
        pygame.quit()
        status = "OK: Updated" if saved else "WARN: Save failed"
        if debug_level:
            status = f"DEBUG ({debug_level}): {status}"
        log("space_weather", status)
        return saved
    except (OSError, KeyError, ValueError, requests.RequestException) as error:
        pygame.quit()
        log("space_weather", f"ERROR: {error}")
        log("space_weather", "WARN: Keeping previous image")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the space weather forecast card.")
    parser.add_argument(
        "--debug-level",
        choices=LEVELS,
        help="force the displayed activity level (few, normal, or many)",
    )
    args = parser.parse_args()
    main(debug_level=args.debug_level)
