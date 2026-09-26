import csv
import io
import json
import os
import sys
from datetime import datetime

import pygame
import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from common.utils import log, safe_save


CARD_W = 1080
CARD_H = 480
CONFIG_PATH = os.path.join(PROJECT_ROOT, "power_forecast", "config.json")
FONT_PATH = os.path.join(PROJECT_ROOT, "fonts", "NotoSansJP-Regular.ttf")
REGION_LABELS = {
    "tokyo": "東京エリア",
}
REGION_URLS = {
    "tokyo": "https://www.tepco.co.jp/forecast/html/images/juyo-d1-j.csv",
}
RAMIS_API_URL = "https://www.ramis.nra.go.jp/api/v1"
RAMIS_AUTH = "Basic cHJvZHJhbWlzOmQ0VjlhbitAMTNxQUUpfERTWUIn"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    config["output_path"] = os.path.join(PROJECT_ROOT, config["output_path"])
    config["temp_path"] = os.path.join(PROJECT_ROOT, config["temp_path"])
    return config


def parse_forecast_csv(content):
    text = content.decode("shift_jis", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    header_index = next(
        (index for index, row in enumerate(rows) if row[:2] == ["DATE", "TIME"]),
        None,
    )
    if header_index is None:
        raise ValueError("forecast CSV header was not found")

    forecast = []
    for row in rows[header_index + 1:]:
        if len(row) < 6 or not row[0] or not row[1]:
            if forecast:
                break
            continue
        try:
            demand = int(row[3])
            supply = int(row[5])
        except (ValueError, IndexError):
            continue
        if demand <= 0 or supply <= 0:
            continue
        forecast_time = datetime.strptime(
            f"{row[0]} {row[1]}", "%Y/%m/%d %H:%M"
        )
        reserve_rate = (supply - demand) / demand * 100
        forecast.append({
            "time": forecast_time,
            "demand": demand,
            "supply": supply,
            "reserve_rate": reserve_rate,
        })
    if not forecast:
        raise ValueError("forecast CSV contains no forecast rows")
    return forecast


def fetch_forecast(region):
    if region not in REGION_URLS:
        raise ValueError(f"unsupported power region: {region}")
    response = requests.get(REGION_URLS[region], timeout=10)
    response.raise_for_status()
    return parse_forecast_csv(response.content)


def fetch_ramis_radiation(station_code):
    headers = {
        "Authorization": RAMIS_AUTH,
        "Accept": "application/json",
    }
    response = requests.get(
        f"{RAMIS_API_URL}/map/map-means-data-public",
        params={"data_type": 1},
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()
    stations = response.json().get("data", [])
    station = next(
        (item for item in stations if item.get("obs_station_unique_code") == station_code),
        None,
    )
    if station is None:
        raise ValueError(f"RAMIS station was not found: {station_code}")
    value = station.get("air_dose_rate")
    if value is None or station.get("missing_status") not in (None, "0", 0):
        return None
    return {
        "value": float(value),
        "measured_at": station.get("meas_datetime"),
    }


def choose_current(forecast):
    now = datetime.now()
    upcoming = [item for item in forecast if item["time"] >= now]
    return upcoming[0] if upcoming else forecast[-1]


def format_power(value):
    return f"{value / 1000:.1f}万kW"


def estimate_co2_rate(demand, factor):
    return demand * factor / 1000


def status_for(reserve_rate):
    if reserve_rate >= 8:
        return "安定", (106, 190, 150)
    if reserve_rate >= 5:
        return "やや注意", (238, 186, 82)
    return "厳しい", (224, 105, 92)


def draw_text(surface, font, text, position, color=(240, 244, 248)):
    surface.blit(font.render(text, True, color), position)


def draw_background(card):
    top = pygame.Color("#172637")
    bottom = pygame.Color("#263E4B")
    for y in range(CARD_H):
        ratio = y / CARD_H
        color = tuple(
            int(top[index] + (bottom[index] - top[index]) * ratio)
            for index in range(3)
        )
        pygame.draw.line(card, color, (0, y), (CARD_W, y))
    pygame.draw.rect(
        card, (255, 255, 255, 100), (0, 0, CARD_W, CARD_H), width=4, border_radius=28
    )


def draw_header(card, region, updated_at):
    title_font = pygame.font.Font(FONT_PATH, 42)
    small_font = pygame.font.Font(FONT_PATH, 22)
    draw_text(card, title_font, "でんき予報", (42, 28))
    draw_text(card, small_font, region, (42, 82), (164, 214, 222))
    updated = updated_at.strftime("%Y年%m月%d日 %H:%M 更新")
    text = small_font.render(updated, True, (180, 193, 204))
    card.blit(text, (CARD_W - text.get_width() - 42, 42))


def draw_summary(card, current, peak):
    label_font = pygame.font.Font(FONT_PATH, 22)
    value_font = pygame.font.Font(FONT_PATH, 34)
    status, color = status_for(current["reserve_rate"])
    panels = [
        (42, "現在の予想需要", format_power(current["demand"])),
        (292, "供給力", format_power(current["supply"])),
        (542, "予備率", f"{current['reserve_rate']:.1f}%"),
        (792, "需給状況", status),
    ]
    for x, label, value in panels:
        pygame.draw.rect(card, (7, 16, 25, 150), (x, 126, 220, 92), border_radius=14)
        draw_text(card, label_font, label, (x + 16, 140), (166, 183, 195))
        value_color = color if label == "需給状況" else (242, 247, 250)
        draw_text(card, value_font, value, (x + 16, 169), value_color)

    peak_text = label_font.render(
        f"本日の最大予想: {format_power(peak['demand'])}（{peak['time'].strftime('%H:%M')}）",
        True,
        (210, 220, 228),
    )
    card.blit(peak_text, (42, 238))


def draw_environment(card, current, config, radiation):
    font = pygame.font.Font(FONT_PATH, 20)
    co2_rate = estimate_co2_rate(current["demand"], config["co2_factor_kg_per_kwh"])
    co2_text = f"推定 CO2: {co2_rate:.0f} kg-CO2/時"
    radiation_text = (
        f"空間線量: {radiation['value']:.4f} μSv/h ({config['radiation_station']})"
        if radiation is not None
        else f"空間線量: データなし ({config['radiation_station']})"
    )
    for x, text in ((42, co2_text), (542, radiation_text)):
        pygame.draw.rect(card, (7, 16, 25, 150), (x, 234, 496, 34), border_radius=10)
        draw_text(card, font, text, (x + 16, 240), (202, 216, 222))


def draw_graph(card, forecast):
    graph_x, graph_y, graph_w, graph_h = 42, 278, 996, 138
    pygame.draw.rect(card, (7, 16, 25, 100), (graph_x, graph_y, graph_w, graph_h), border_radius=14)
    maximum = max(item["supply"] for item in forecast) * 1.08
    points = []
    for index, item in enumerate(forecast):
        x = graph_x + 20 + int(index * (graph_w - 40) / max(len(forecast) - 1, 1))
        y = graph_y + graph_h - 20 - int(item["demand"] / maximum * (graph_h - 42))
        points.append((x, y))
    for index in range(len(points) - 1):
        pygame.draw.line(card, (91, 199, 211), points[index], points[index + 1], 4)
    for index, point in enumerate(points):
        pygame.draw.circle(card, (235, 247, 248), point, 5)
        if index in (0, len(points) - 1) or index % 4 == 0:
            label = forecast[index]["time"].strftime("%H時")
            font = pygame.font.Font(FONT_PATH, 18)
            label_surface = font.render(label, True, (175, 193, 204))
            card.blit(label_surface, (point[0] - label_surface.get_width() // 2, graph_y + graph_h - 18))
    font = pygame.font.Font(FONT_PATH, 18)
    draw_text(card, font, "需要予想（1時間ごと）", (graph_x + 18, graph_y + 8), (175, 193, 204))


def draw_card(config, forecast, radiation):
    pygame.init()
    card = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    draw_background(card)
    draw_header(card, REGION_LABELS[config["region"]], datetime.now())
    current = choose_current(forecast)
    peak = max(forecast, key=lambda item: item["demand"])
    draw_summary(card, current, peak)
    draw_environment(card, current, config, radiation)
    draw_graph(card, forecast)
    footer_font = pygame.font.Font(FONT_PATH, 16)
    draw_text(card, footer_font, "Provided by：東京電力パワーグリッド（需給予報 CSV）", (42, 442), (145, 160, 172))
    return card


def main():
    try:
        config = load_config()
        forecast = fetch_forecast(config["region"])
        radiation = fetch_ramis_radiation(config["radiation_station_code"])
        card = draw_card(config, forecast, radiation)
        saved = safe_save(card, config["temp_path"], config["output_path"])
        pygame.quit()
        log("power_forecast", "OK: Updated" if saved else "WARN: Save failed")
        return saved
    except (OSError, KeyError, ValueError, requests.RequestException) as error:
        log("power_forecast", f"ERROR: {error}")
        log("power_forecast", "WARN: Using previous image")
        pygame.quit()
        return False


if __name__ == "__main__":
    main()
