import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 480))
clock = pygame.time.Clock()

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

def draw_weather_card(weather_main):
    alpha_bg = 120      # 背景（強透過）
    alpha_shadow = 160  # 影（中透過）
    alpha_fg = 250      # アイコン・テキスト（弱透過）
    alpha_border = 220  # 外枠（前景より少し濃い）

    # -------------------------
    # 背景レイヤー（強透過）
    # -------------------------
    bg = pygame.Surface((720, 400), pygame.SRCALPHA)
    top_color, bottom_color = COLOR_MAP[weather_main]
    draw_vertical_gradient(bg, top_color, bottom_color)

    mask = pygame.Surface((720, 400), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255,255,255), (0,0,720,400), border_radius=24)
    bg.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)

    bg.set_alpha(alpha_bg)
    screen.blit(bg, (40, 40))

    # -------------------------
    # 影レイヤー（中透過）
    # -------------------------
    shadow = pygame.Surface((720, 400), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0,0,0,80), (0,0,720,400), border_radius=24)
    shadow.set_alpha(alpha_shadow)
    screen.blit(shadow, (44, 44))

    # -------------------------
    # 外枠レイヤー（新規追加）
    # -------------------------
    border = pygame.Surface((720, 400), pygame.SRCALPHA)
    pygame.draw.rect(border, (255,255,255), (0,0,720,400), width=4, border_radius=24)
    border.set_alpha(alpha_border)
    screen.blit(border, (40, 40))

    # -------------------------
    # 前景レイヤー（弱透過）
    # -------------------------
    fg = pygame.Surface((720, 400), pygame.SRCALPHA)

    # アイコン影
    icon = pygame.image.load("icons/clear.png").convert_alpha()
    icon_shadow = pygame.Surface(icon.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(icon_shadow, (0,0,0,80), (0,0,160,160), border_radius=32)
    icon_shadow.set_alpha(alpha_shadow)
    fg.blit(icon_shadow, (84, 124))

    # アイコン本体
    icon.set_alpha(alpha_fg)
    fg.blit(icon, (80, 120))

    # テキスト
    font_big = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 72)
    font_mid = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 48)
    font_small = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 36)

    txt1 = font_big.render("快晴", True, (255,255,255))
    txt2 = font_mid.render("気温 27°C / 体感 29°C", True, (255,255,255))
    txt3 = font_small.render("湿度 68%   風 3.2m/s", True, (255,255,255))

    txt1.set_alpha(alpha_fg)
    txt2.set_alpha(alpha_fg)
    txt3.set_alpha(alpha_fg)

    fg.blit(txt1, (280, 120))
    fg.blit(txt2, (280, 200))
    fg.blit(txt3, (280, 260))

    screen.blit(fg, (40, 40))

weather_main = "Clear"

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((0,0,0))
    draw_weather_card(weather_main)

    pygame.display.update()
    clock.tick(30)
