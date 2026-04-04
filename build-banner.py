#!/usr/bin/env python3
"""Build Gullicksen banner — eagle as watermark background, text on top."""
from PIL import Image, ImageDraw, ImageFont
import os

DIR = '/Users/warden/Desktop/gullicksen-realty'

W, H = 1300, 500

# Colors
NAVY = (0, 35, 90)
GOLD = (197, 164, 78)
GOLD_LIGHT = (220, 195, 110)
WHITE = (255, 255, 255)

img = Image.new('RGBA', (W, H), NAVY)
draw = ImageDraw.Draw(img)

# --- Crosshatch pattern across full banner ---
for offset in range(-H, W + H, 20):
    draw.line([(offset, 0), (offset - H, H)], fill=(255, 255, 255, 12), width=1)
for offset in range(-H, W + H, 20):
    draw.line([(offset, 0), (offset + H, H)], fill=(255, 255, 255, 12), width=1)

# --- Eagle as large faded watermark background ---
eagle = Image.open(os.path.join(DIR, 'eagle.png')).convert('RGBA')
eagle_h = 480
eagle_w = int(eagle.width * eagle_h / eagle.height)
eagle_resized = eagle.resize((eagle_w, eagle_h), Image.LANCZOS)

# Faint gold tint at low opacity
eagle_tinted = Image.new('RGBA', eagle_resized.size)
eagle_px = eagle_resized.load()
eagle_t = eagle_tinted.load()
for y in range(eagle_resized.height):
    for x in range(eagle_resized.width):
        r, g, b, a = eagle_px[x, y]
        if a > 20:
            brightness = (r + g + b) / 3
            cr = int(brightness * 0.4)
            cg = int(brightness * 0.35)
            cb = int(brightness * 0.12)
            alpha = int(a * 0.12)  # Very faint
            eagle_t[x, y] = (cr, cg, cb, alpha)
        else:
            eagle_t[x, y] = (0, 0, 0, 0)

# Center eagle
eagle_x = W // 2 - eagle_w // 2
eagle_y = 10
img.paste(eagle_tinted, (eagle_x, eagle_y), eagle_tinted)

# --- Fonts ---
font_bold = ImageFont.truetype("/System/Library/Fonts/Georgia Bold.ttf", 46)
font_amp = ImageFont.truetype("/System/Library/Fonts/Georgia Bold Italic.ttf", 42)
font_circle = ImageFont.truetype("/System/Library/Fonts/Georgia Bold.ttf", 19)
font_subtitle = ImageFont.truetype("/System/Library/Fonts/Georgia Bold.ttf", 20)
font_tagline = ImageFont.truetype("/System/Library/Fonts/Georgia.ttf", 13)
font_info = ImageFont.truetype("/System/Library/Fonts/Georgia.ttf", 14)

star_font = ImageFont.truetype("/System/Library/Fonts/Georgia Bold.ttf", 18)

draw = ImageDraw.Draw(img)

# --- Company name at top ---
name_y = 20
name = "GULLICKSEN"
amp = "&"
co = "CO"

name_bbox = draw.textbbox((0, 0), name, font=font_bold)
name_w = name_bbox[2] - name_bbox[0]
amp_bbox = draw.textbbox((0, 0), amp, font=font_amp)
amp_w = amp_bbox[2] - amp_bbox[0]

total_w = name_w + 12 + amp_w + 16 + (22 * 2) + 8
start_x = W // 2 - total_w // 2

draw.text((start_x, name_y), name, fill=WHITE, font=font_bold)
x = start_x + name_w + 12
draw.text((x, name_y + 3), amp, fill=GOLD, font=font_amp)
x += amp_w + 16

cr = 22
cx_c = x + cr
cy_c = name_y + 26
draw.ellipse([cx_c - cr, cy_c - cr, cx_c + cr, cy_c + cr], outline=GOLD, width=2)
co_bbox = draw.textbbox((0, 0), co, font=font_circle)
co_w2 = co_bbox[2] - co_bbox[0]
co_h2 = co_bbox[3] - co_bbox[1]
draw.text((cx_c - co_w2 // 2, cy_c - co_h2 // 2 - 2), co, fill=GOLD, font=font_circle)

# --- Subtitle: SEMPER FI REALTY ---
subtitle = "SEMPER FI REALTY"
sub_bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
sub_w = sub_bbox[2] - sub_bbox[0]
draw.text((W // 2 - sub_w // 2, name_y + 70), subtitle, fill=GOLD, font=font_subtitle)

# --- Stars row (5) ---
stars_text = "★   ★   ★   ★   ★"
stars_bbox = draw.textbbox((0, 0), stars_text, font=star_font)
stars_w = stars_bbox[2] - stars_bbox[0]
draw.text((W // 2 - stars_w // 2, name_y + 105), stars_text, fill=GOLD, font=star_font)

# --- Tagline ---
tagline = "Serving Those Who Served. And Everyone In Between."
tagline_bbox = draw.textbbox((0, 0), tagline, font=font_tagline)
tagline_w = tagline_bbox[2] - tagline_bbox[0]
draw.text((W // 2 - tagline_w // 2, name_y + 140), tagline, fill=WHITE, font=font_tagline)

# --- Bottom info bar ---
BAR_H = 60
BAR_Y = H - BAR_H

bar = Image.new('RGBA', (W, BAR_H), (0, 20, 55, 255))
bar_draw = ImageDraw.Draw(bar)
bar_draw.line([(0, 0), (W, 0)], fill=GOLD, width=2)
bar_draw.line([(0, BAR_H - 1), (W, BAR_H - 1)], fill=GOLD, width=1)
img.paste(bar, (0, BAR_Y), bar)

bar_cx = W // 2
bar_cy = BAR_Y + BAR_H // 2

website = "www.gullicksen-realty.com"
phone = "(xxx) xxx-xxxx"
info_line = f"{website}  •  {phone}"
info_bbox = draw.textbbox((0, 0), info_line, font=font_info)
info_w = info_bbox[2] - info_bbox[0]
draw.text((bar_cx - info_w // 2, bar_cy - 14), info_line, fill=WHITE, font=font_info)

bar_stars = "★   ★   ★"
bar_stars_bbox = draw.textbbox((0, 0), bar_stars, font=star_font)
bar_stars_w = bar_stars_bbox[2] - bar_stars_bbox[0]
draw.text((bar_cx - bar_stars_w // 2, bar_cy + 2), bar_stars, fill=GOLD, font=star_font)

buying = "BUYING - SELLING - RENTING - INVESTING"
buying_bbox = draw.textbbox((0, 0), buying, font=font_info)
buying_w = buying_bbox[2] - buying_bbox[0]
draw.text((bar_cx - buying_w // 2, bar_cy + 24), buying, fill=GOLD_LIGHT, font=font_info)

# Save
out = os.path.join(DIR, 'gullicksen-banner-dual-eagle.png')
img.save(out, 'PNG')
print(f'Saved: {out}')
