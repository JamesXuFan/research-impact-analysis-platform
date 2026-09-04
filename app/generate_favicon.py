"""One-off script that generated static/favicon.png — not imported by the app
at runtime, kept only so the icon can be regenerated/tweaked later without
redoing this from scratch. Run manually: `python app/generate_favicon.py`.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RED = "#DA291C"
BLACK = "#1A1A1A"

SIZE = 256
OUT = Path(__file__).resolve().parent / "static" / "favicon.png"

img = Image.new("RGB", (SIZE, SIZE), RED)
draw = ImageDraw.Draw(img)

# A thin black frame — echoes the hard-edged, no-border-radius Bauhaus style
# used throughout the app's own CSS (theme.py), not a rounded-icon look.
border = 10
draw.rectangle([0, 0, SIZE - 1, SIZE - 1], outline=BLACK, width=border)

font = ImageFont.truetype(r"C:\Windows\Fonts\ariblk.ttf", 108)
text = "P36"
bbox = draw.textbbox((0, 0), text, font=font)
w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
# Nudge up slightly — cap-height text sits visually low if centred on the
# full bbox including descender space this text doesn't use.
x = (SIZE - w) / 2 - bbox[0]
y = (SIZE - h) / 2 - bbox[1] - 6
draw.text((x, y), text, fill=BLACK, font=font)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
