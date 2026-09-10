from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RED = "#DA291C"
BLUE = "#0F4C81"
YELLOW = "#FFC20E"
BLACK = "#1A1A1A"
WHITE = "#FFFFFF"

SIZE = 256
OUT = Path(__file__).resolve().parent / "static" / "favicon.png"

img = Image.new("RGB", (SIZE, SIZE), WHITE)
draw = ImageDraw.Draw(img)

border = 6
draw.rectangle([0, 0, SIZE - 1, SIZE - 1], outline=BLACK, width=border)

font = ImageFont.truetype(r"C:\Windows\Fonts\ariblk.ttf", 108)

letters = [("P", RED), ("3", BLUE), ("6", YELLOW)]
stroke_width = 5

widths = [draw.textbbox((0, 0), ch, font=font, stroke_width=stroke_width)[2] for ch, _ in letters]
total_w = sum(widths)
bbox_full = draw.textbbox((0, 0), "P36", font=font, stroke_width=stroke_width)
h = bbox_full[3] - bbox_full[1]

x = (SIZE - total_w) / 2
y = (SIZE - h) / 2 - bbox_full[1] - 4
for (ch, colour), w in zip(letters, widths):
    draw.text((x, y), ch, fill=colour, font=font, stroke_width=stroke_width, stroke_fill=BLACK)
    x += w

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
