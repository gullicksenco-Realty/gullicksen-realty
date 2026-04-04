#!/usr/bin/env python3
"""Build Gullicksen banner — reference-accurate version matching Mike's provided banner."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math, random

DIR = '/Users/warden/Desktop/gullicksen-realty'
W, H = 1300, 500

# --- Colors ---
PARCHMENT = (235, 220, 190)
PARCHMENT_DARK = (210, 195, 160)
RED_BORDER = (160, 45, 35)
RED_DARK = (120, 30, 25)
GOLD = (197, 164, 78)
GOLD_BRIGHT = (220, 195, 110)
NAVY_SHIELD = (25, 35, 70)
NAVY_LIGHT = (35, 50, 90)
WHITE = (255, 255, 255)
BLACK = (30, 25, 20)

img = Image.new('RGBA', (W, H))

# === 1. AGED PAPER BACKGROUND ===
draw = ImageDraw.Draw(img)
for y in range(H):
    for x in range(W):
        # Base parchment with subtle variation
        noise = random.randint(-12, 12)
        r = PARCHMENT[0] + noise
        g = PARCHMENT[1] + noise - 2
        b = PARCHMENT[2] + noise - 5
        # Darken edges (vignette)
        dx = (x - W/2) / (W/2)
        dy = (y - H/2) / (H/2)
        dist = math.sqrt(dx*dx + dy*dy)
        factor = max(0.82, 1.0 - dist * 0.2)
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        img.putpixel((x, y), (r, g, b, 255))

draw = ImageDraw.Draw(img)

# === 2. RED BORDER ===
BORDER = 22
# Outer red border
for i in range(BORDER):
    alpha_factor = 1.0
    r = int(RED_BORDER[0] + (i % 3) * 5)
    g = int(RED_BORDER[1] + (i % 2) * 3)
    b = int(RED_BORDER[2] + (i % 2) * 2)
    draw.rectangle([i, i, W-1-i, H-1-i], outline=(r, g, b, 255))

# Inner gold line
INNER_OFF = BORDER + 4
draw.rectangle([INNER_OFF, INNER_OFF, W-1-INNER_OFF, H-1-INNER_OFF], outline=GOLD, width=2)

# === 3. DECORATIVE CORNERS ===
CORNER_SIZE = 55
for cx, cy in [(BORDER, BORDER), (W-BORDER, BORDER), (BORDER, H-BORDER), (W-BORDER, H-BORDER)]:
    # Ornate corner flourish - concentric arcs
    for r_size in [CORNER_SIZE, CORNER_SIZE-8, CORNER_SIZE-14]:
        bbox = [cx - r_size, cy - r_size, cx + r_size, cy + r_size]
        draw.arc(bbox, 0, 360, fill=GOLD, width=2)
    # Diamond accent
    d = 10
    draw.polygon([(cx, cy-d), (cx+d, cy), (cx, cy+d), (cx-d, cy)], fill=GOLD)


# Corner line accents extending from corners
accent_len = 80
# Top-left
draw.line([(BORDER, BORDER+CORNER_SIZE), (BORDER, BORDER+CORNER_SIZE+accent_len)], fill=GOLD, width=1)
draw.line([(BORDER+CORNER_SIZE, BORDER), (BORDER+CORNER_SIZE+accent_len, BORDER)], fill=GOLD, width=1)
# Top-right
draw.line([(W-BORDER, BORDER+CORNER_SIZE), (W-BORDER, BORDER+CORNER_SIZE+accent_len)], fill=GOLD, width=1)
draw.line([(W-BORDER-CORNER_SIZE, BORDER), (W-BORDER-CORNER_SIZE-accent_len, BORDER)], fill=GOLD, width=1)
# Bottom-left
draw.line([(BORDER, H-BORDER-CORNER_SIZE), (BORDER, H-BORDER-CORNER_SIZE-accent_len)], fill=GOLD, width=1)
draw.line([(BORDER+CORNER_SIZE, H-BORDER), (BORDER+CORNER_SIZE+accent_len, H-BORDER)], fill=GOLD, width=1)
# Bottom-right
draw.line([(W-BORDER, H-BORDER-CORNER_SIZE), (W-BORDER, H-BORDER-CORNER_SIZE-accent_len)], fill=GOLD, width=1)
draw.line([(W-BORDER-CORNER_SIZE, H-BORDER), (W-BORDER-CORNER_SIZE-accent_len, H-BORDER)], fill=GOLD, width=1)

# === 4. NAVY SHIELD (organic shape, centered) ===
SHIELD_W = 380
SHIELD_H = 340
scx, scy = W // 2, H // 2 + 10

# Shield outline points (organic rounded shape like reference)
shield_pts = []
steps = 200
for i in range(steps + 1):
    t = i / steps
    # Parametric shield shape
    angle = t * 2 * math.pi
    # Base ellipse
    rx, ry = SHIELD_W / 2, SHIELD_H / 2
    x = rx * math.cos(angle)
    y = ry * math.sin(angle)
    # Flattish top, pointed bottom
    if y < 0:  # Top half
        y = y * 0.6  # Flatten top
    else:  # Bottom half
        y = y * 1.15  # Elongate bottom
        # Sharpen toward point at bottom
        squeeze = 1.0 - (y / ry) * 0.3
        x = x * max(0.3, squeeze)
    shield_pts.append((scx + x, scy + y))

# Draw shield shadow
shadow_pts = [(p[0]+4, p[1]+4) for p in shield_pts]
draw.polygon(shadow_pts, fill=(0, 0, 0, 60))

# Draw shield fill (navy gradient effect via layered polygons)
for depth in range(10, 0, -1):
    factor = 1.0 - depth * 0.015
    scaled = []
    for px, py in shield_pts:
        dx, dy = px - scx, py - scy
        scaled.append((scx + dx * factor, scy + dy * factor))
    shade = max(0, NAVY_SHIELD[0] + depth * 2)
    shade2 = max(0, NAVY_SHIELD[1] + depth * 3)
    shade3 = max(0, NAVY_SHIELD[2] + depth * 5)
    draw.polygon(scaled, fill=(shade, shade2, shade3, 255))

# Shield border (gold)
draw.polygon(shield_pts, outline=GOLD, width=3)

# Inner shield border
inner_pts = []
for px, py in shield_pts:
    dx, dy = px - scx, py - scy
    inner_pts.append((scx + dx * 0.94, scy + dy * 0.94))
draw.polygon(inner_pts, outline=GOLD, width=1)

# === 5. EAGLE (centered in shield) ===
eagle = Image.open(os.path.join(DIR, 'eagle.png')).convert('RGBA')

# Size eagle to fit in shield
eagle_h = 260
eagle_w = int(eagle.width * eagle_h / eagle.height)
eagle_resized = eagle.resize((eagle_w, eagle_h), Image.LANCZOS)

# Tint eagle golden
eagle_tinted = Image.new('RGBA', eagle_resized.size)
px_in = eagle_resized.load()
px_out = eagle_tinted.load()
for y in range(eagle_resized.height):
    for x in range(eagle_resized.width):
        r, g, b, a = px_in[x, y]
        if a > 30:
            brightness = (r + g + b) / 3 / 255.0
            # Rich golden tint
            gold_r = int(180 + brightness * 60)
            gold_g = int(145 + brightness * 55)
            gold_b = int(40 + brightness * 50)
            px_out[x, y] = (gold_r, gold_g, gold_b, a)
        else:
            px_out[x, y] = (0, 0, 0, 0)

# Center eagle in shield
eagle_x = scx - eagle_w // 2
eagle_y = scy - eagle_h // 2 + 5
img.paste(eagle_tinted, (eagle_x, eagle_y), eagle_tinted)

# === 6. TEXT ===
# Fonts
font_bold = ImageFont.truetype("/System/Library/Fonts/Georgia Bold.ttf", 44)
font_amp = ImageFont.truetype("/System/Library/Fonts/Georgia Bold Italic.ttf", 38)
font_co = ImageFont.truetype("/System/Library/Fonts/Georgia Bold.ttf", 20)
font_subtitle = ImageFont.truetype("/System/Library/Fonts/Georgia Bold.ttf", 18)
font_real_estate = ImageFont.truetype("/System/Library/Fonts/Georgia.ttf", 14)

# "GULLICKSEN & CO." above shield
text_y_top = scy - SHIELD_H // 2 - 55

name = "GULLICKSEN"
amp = "&"
co = "CO."

name_bbox = draw.textbbox((0, 0), name, font=font_bold)
name_w = name_bbox[2] - name_bbox[0]
amp_bbox = draw.textbbox((0, 0), amp, font=font_amp)
amp_w = amp_bbox[2] - amp_bbox[0]
co_bbox = draw.textbbox((0, 0), co, font=font_co)
co_w = co_bbox[2] - co_bbox[0]

total_w = name_w + 14 + amp_w + 10 + co_w
start_x = W // 2 - total_w // 2

# Text shadow
draw.text((start_x + 2, text_y_top + 2), name, fill=(0, 0, 0, 100), font=font_bold)
draw.text((start_x, text_y_top), name, fill=NAVY_SHIELD, font=font_bold)

x = start_x + name_w + 14
draw.text((x + 2, text_y_top + 3), amp, fill=(0, 0, 0, 80), font=font_amp)
draw.text((x, text_y_top + 1), amp, fill=GOLD, font=font_amp)

x += amp_w + 10
draw.text((x, text_y_top + 18), co, fill=NAVY_SHIELD, font=font_co)

# "SEMPER FI REALTY" below shield
sub_y = scy + SHIELD_H // 2 + 15
subtitle = "SEMPER FI REALTY"
sub_bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
sub_w = sub_bbox[2] - sub_bbox[0]
# Underline
line_y = sub_y + 8
line_half = sub_w // 2 + 30
draw.line([(W//2 - line_half, line_y), (W//2 + line_half, line_y)], fill=GOLD, width=1)

draw.text((W // 2 - sub_w // 2, sub_y), subtitle, fill=NAVY_SHIELD, font=font_subtitle)

# "Real Estate" smaller text
re = "Real Estate"
re_bbox = draw.textbbox((0, 0), re, font=font_real_estate)
re_w = re_bbox[2] - re_bbox[0]
re_y = sub_y + 30
draw.text((W // 2 - re_w // 2, re_y), re, fill=(100, 85, 65), font=font_real_estate)

# "Serving Those Who Served..." tagline at bottom
font_tagline = ImageFont.truetype("/System/Library/Fonts/Georgia Bold Italic.ttf", 16)
tagline = "Serving Those Who Served. And Everyone In Between."
tl_bbox = draw.textbbox((0, 0), tagline, font=font_tagline)
tl_w = tl_bbox[2] - tl_bbox[0]
tl_y = H - 60
draw.text((W // 2 - tl_w // 2, tl_y), tagline, fill=(80, 65, 45), font=font_tagline)

# === 7. TEXTURE OVERLAY (paper grain) ===
texture = Image.new('RGBA', (W, H))
tex_draw = ImageDraw.Draw(texture)
for _ in range(3000):
    tx, ty = random.randint(0, W-1), random.randint(0, H-1)
    tex_draw.point((tx, ty), fill=(0, 0, 0, random.randint(5, 15)))
img = Image.alpha_composite(img, texture)

# === SAVE ===
out = os.path.join(DIR, 'gullicksen-banner-dual-eagle.png')
img.save(out, 'PNG')
print(f'Saved: {out} ({img.size[0]}x{img.size[1]})')
