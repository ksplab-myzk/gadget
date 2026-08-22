from PIL import Image, ImageDraw
import os

input_dir = "./icons"
output_dir = "./icons_rounded"
os.makedirs(output_dir, exist_ok=True)

size = (192, 192)
radius = 32

for filename in os.listdir(input_dir):
    if filename.endswith(".png"):
        img = Image.open(os.path.join(input_dir, filename)).convert("RGBA")
        img = img.resize(size, Image.LANCZOS)

        # 角丸マスク
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, size[0], size[1]), radius, fill=255)

        # マスク適用
        rounded = Image.new("RGBA", size)
        rounded.paste(img, (0, 0), mask)

        rounded.save(os.path.join(output_dir, filename), optimize=True)
