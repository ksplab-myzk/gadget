import json
import os
import re
import sys

import pygame

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from common.utils import log, safe_save


CARD_W = 1080
CARD_H = 480
CONFIG_PATH = os.path.join(PROJECT_ROOT, "notice_board", "config.json")
FONT_PATH = os.path.join(PROJECT_ROOT, "fonts", "NotoSansJP-Regular.ttf")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    if not isinstance(config, dict):
        raise ValueError("config.json must contain a JSON object")
    if not isinstance(config.get("title"), str) or not config["title"].strip():
        raise ValueError("config.json must contain a non-empty title")
    if not isinstance(config.get("content"), str) or not config["content"].strip():
        raise ValueError("config.json must contain non-empty Markdown content")
    if not isinstance(config.get("posted_at", ""), str):
        raise ValueError("posted_at must be a string")

    for path_key in ("output_path", "temp_path"):
        path = config.get(path_key)
        if not isinstance(path, str) or not path.strip():
            raise ValueError(f"config.json must contain a non-empty {path_key}")
        config[path_key] = os.path.join(PROJECT_ROOT, path)
    return config


def _plain_markdown(text):
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"(`{1,3})(.*?)\1", r"\2", text)
    text = re.sub(r"(\*\*|__|~~|\*|_)(.*?)\1", r"\2", text)
    return text


def _wrap_text(text, font, max_width):
    if not text:
        return [""]

    wrapped = []
    line = ""
    for character in text:
        candidate = line + character
        if line and font.size(candidate)[0] > max_width:
            wrapped.append(line.rstrip())
            line = character.lstrip()
        else:
            line = candidate
    if line:
        wrapped.append(line.rstrip())
    return wrapped


def _markdown_lines(content):
    body_font = pygame.font.Font(FONT_PATH, 22)
    heading_fonts = {
        1: pygame.font.Font(FONT_PATH, 29),
        2: pygame.font.Font(FONT_PATH, 25),
        3: pygame.font.Font(FONT_PATH, 22),
    }
    rendered_lines = []

    for source_line in content.splitlines():
        if not source_line.strip():
            rendered_lines.append((None, "", 10))
            continue

        heading = re.match(r"^\s{0,3}(#{1,3})\s+(.+?)\s*#*\s*$", source_line)
        if heading:
            level = len(heading.group(1))
            rendered_lines.extend(
                (heading_fonts[level], line, 5)
                for line in _wrap_text(_plain_markdown(heading.group(2)), heading_fonts[level], 920)
            )
            continue

        list_item = re.match(r"^\s*[-+*]\s+(.+)$", source_line)
        numbered_item = re.match(r"^\s*(\d+)\.\s+(.+)$", source_line)
        quote = re.match(r"^\s*>\s?(.*)$", source_line)
        if list_item:
            text = "• " + _plain_markdown(list_item.group(1))
            indent = 24
        elif numbered_item:
            text = numbered_item.group(1) + ". " + _plain_markdown(numbered_item.group(2))
            indent = 24
        elif quote:
            text = "│ " + _plain_markdown(quote.group(1))
            indent = 24
        else:
            text = _plain_markdown(source_line.strip())
            indent = 0

        rendered_lines.extend(
            (body_font, line, 2)
            for line in _wrap_text(text, body_font, 920 - indent)
        )

    return rendered_lines


def draw_card(config):
    pygame.init()
    card = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)

    pygame.draw.rect(card, (73, 48, 35), (0, 0, CARD_W, CARD_H), border_radius=24)
    pygame.draw.rect(card, (127, 82, 52), (15, 15, CARD_W - 30, CARD_H - 30), border_radius=18)
    pygame.draw.rect(card, (178, 125, 76), (24, 24, CARD_W - 48, CARD_H - 48), border_radius=14)

    for x in (42, CARD_W - 42):
        for y in (42, CARD_H - 42):
            pygame.draw.circle(card, (82, 55, 39), (x, y), 7)
            pygame.draw.circle(card, (218, 173, 119), (x - 2, y - 2), 2)

    paper_rect = pygame.Rect(42, 34, CARD_W - 84, CARD_H - 68)
    pygame.draw.rect(card, (71, 49, 36), paper_rect.move(3, 5), border_radius=12)
    pygame.draw.rect(card, (250, 246, 229), paper_rect, border_radius=12)

    label_font = pygame.font.Font(FONT_PATH, 22)
    title_font = pygame.font.Font(FONT_PATH, 34)
    meta_font = pygame.font.Font(FONT_PATH, 18)
    label_rect = pygame.Rect(66, 52, 152, 38)
    pygame.draw.rect(card, (35, 70, 112), label_rect, border_radius=8)
    label_surface = label_font.render("お知らせ", True, (255, 250, 238))
    card.blit(label_surface, label_surface.get_rect(center=label_rect.center))

    title = config["title"].strip()
    title_lines = _wrap_text(title, title_font, 780)
    title_y = 101
    for line in title_lines[:2]:
        card.blit(title_font.render(line, True, (58, 53, 45)), (68, title_y))
        title_y += title_font.get_linesize() + 2

    posted_at = config.get("posted_at", "").strip()
    if posted_at:
        posted_surface = meta_font.render(posted_at, True, (112, 104, 91))
        card.blit(posted_surface, (CARD_W - 68 - posted_surface.get_width(), 62))

    divider_y = max(173, title_y + 4)
    pygame.draw.line(card, (220, 210, 187), (68, divider_y), (CARD_W - 68, divider_y), 2)

    content_top = divider_y + 15
    content_bottom = CARD_H - 62
    previous_clip = card.get_clip()
    card.set_clip(pygame.Rect(68, content_top, CARD_W - 136, content_bottom - content_top))
    y = content_top
    content_lines = _markdown_lines(config["content"])
    for index, (font, line, gap) in enumerate(content_lines):
        if font is None:
            y += gap
            continue
        line_height = max(font.get_linesize(), 24)
        if y + line_height > content_bottom:
            if index < len(content_lines):
                omission = meta_font.render("…", True, (112, 104, 91))
                card.blit(omission, (CARD_W - 92, content_bottom - omission.get_height()))
            break
        card.blit(font.render(line, True, (67, 62, 53)), (76, y))
        y += line_height + gap
    card.set_clip(previous_clip)
    return card


def main():
    try:
        config = load_config()
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as error:
        log("notice_board", f"ERROR: Invalid configuration: {error}")
        return False

    try:
        card = draw_card(config)
        saved = safe_save(card, config["temp_path"], config["output_path"])
    finally:
        pygame.quit()

    log("notice_board", "OK: Updated" if saved else "WARN: Save failed")
    return saved


if __name__ == "__main__":
    main()
