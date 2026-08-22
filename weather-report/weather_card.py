import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 480))
clock = pygame.time.Clock()

# -----------------------------
# 天気ごとの色設定
# -----------------------------
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
# 影＋角丸＋透過カード
# -----------------------------
def draw_card(surface, x, y, w, h, radius=24, top_color="#FFFFFF", bottom_color="#FFFFFF", alpha=200):
    # カード用サーフェス
    card = pygame.Surface((w, h), pygame.SRCALPHA)

    # グラデーション背景
    draw_vertical_gradient(card, top_color, bottom_color)

    # 角丸マスク
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255,255,255), (0,0,w,h), border_radius=radius)

    # マスク適用
    card.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)

    # 透過度設定（ここが重要）
    card.set_alpha(alpha)

    # 影（透過度は影にも適用される）
    shadow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0,0,0,80), (0,0,w,h), border_radius=radius)
    shadow.set_alpha(alpha)
    surface.blit(shadow, (x+4, y+4))

    # カード本体
    surface.blit(card, (x, y))

# -----------------------------
# アイコン影
# -----------------------------
def draw_icon_with_shadow(surface, icon, x, y, alpha=255):
    shadow = pygame.Surface(icon.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0,0,0,80), (0,0,icon.get_width(), icon.get_height()), border_radius=32)
    shadow.set_alpha(alpha)
    surface.blit(shadow, (x+4, y+4))

    icon.set_alpha(alpha)
    surface.blit(icon, (x, y))

# -----------------------------
# メインループ
# -----------------------------
weather_main = "Clear"
alpha_value = 150   # ← 透過度（0→255）

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((0,0,0))

    # カード描画（透過）
    top_color, bottom_color = COLOR_MAP[weather_main]
    draw_card(screen, 40, 40, 720, 400, radius=24,
              top_color=top_color, bottom_color=bottom_color,
              alpha=alpha_value)

    # アイコン
    icon = pygame.image.load("icons/clear.png").convert_alpha()
    draw_icon_with_shadow(screen, icon, 80, 120, alpha=alpha_value)

    # テキスト（透過）
    # font_big = pygame.font.SysFont(None, 72)
    # font_mid = pygame.font.SysFont(None, 48)
    # font_small = pygame.font.SysFont(None, 36)
    font_big = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 72)
    font_mid = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 48)
    font_small = pygame.font.Font("fonts/NotoSansJP-Regular.ttf", 36)

    text_color = (255,255,255)

    txt1 = font_big.render("快晴", True, text_color)
    txt1.set_alpha(alpha_value)
    screen.blit(txt1, (280, 120))

    txt2 = font_mid.render("気温 27°C / 体感 29°C", True, text_color)
    txt2.set_alpha(alpha_value)
    screen.blit(txt2, (280, 200))

    txt3 = font_small.render("湿度 68%   風 3.2m/s", True, text_color)
    txt3.set_alpha(alpha_value)
    screen.blit(txt3, (280, 260))

    pygame.display.update()
    clock.tick(30)
