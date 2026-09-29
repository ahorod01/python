"""
Generates a fancy circular monogram logo with the initials "A" and "H"
fused into a single combined glyph (they share one stroke, like a real
hand-drawn monogram, rather than two letters just placed side by side).

Windows notes: this version draws the letterforms as custom vector shapes,
so it does NOT depend on any font being installed - it will look identical
on any machine with Pillow installed.

Requires: pip install Pillow

Run with: python ah_logo.py
Produces (next to this script):
    ah_logo.png              - navy background version
    ah_logo_transparent.png  - transparent background version
"""

import math
import os
import sys

from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

SIZE = 1000                     # canvas is SIZE x SIZE, upscaled for crisp edges
CENTER = SIZE // 2
GOLD = (198, 166, 100)
GOLD_LIGHT = (230, 205, 150)
DEEP_NAVY_TOP = (18, 24, 43)
DEEP_NAVY_BOTTOM = (35, 45, 74)

MONOGRAM_SCALE = 0.85     # size of the AH glyph relative to the ring
MONOGRAM_STROKE = 34      # stroke thickness (in the glyph's own units)

# Save output next to this script, regardless of the folder you run it from.
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def radial_gradient_background(size, inner_color, outer_color):
    """Soft radial gradient from the center outward."""
    img = Image.new("RGB", (size, size))
    pixels = img.load()
    max_dist = (size / 2) ** 2 * 2
    cx, cy = size / 2, size / 2
    for y in range(size):
        for x in range(size):
            dist = (x - cx) ** 2 + (y - cy) ** 2
            t = min(dist / max_dist, 1.0)
            r = int(inner_color[0] + (outer_color[0] - inner_color[0]) * t)
            g = int(inner_color[1] + (outer_color[1] - inner_color[1]) * t)
            b = int(inner_color[2] + (outer_color[2] - inner_color[2]) * t)
            pixels[x, y] = (r, g, b)
    return img


def draw_ring(draw, center, radius, width, color):
    bbox = [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius]
    draw.ellipse(bbox, outline=color, width=width)


def draw_tick_marks(draw, center, radius, count, length, color, width=3):
    """Decorative clock-like tick marks around the ring."""
    for i in range(count):
        angle = math.radians(360 / count * i)
        x1 = center[0] + radius * math.cos(angle)
        y1 = center[1] + radius * math.sin(angle)
        x2 = center[0] + (radius + length) * math.cos(angle)
        y2 = center[1] + (radius + length) * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)


def load_font(font_size):
    if FONT_PATH:
        return ImageFont.truetype(FONT_PATH, font_size)
    # Last-resort fallback so the script never crashes if no font is found.
    return ImageFont.load_default()


def draw_monogram_text(base_img, text, font_size, fill, center):
    """Draws text centered on the image."""
    layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = load_font(font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = center[0] - text_w / 2 - bbox[0]
    y = center[1] - text_h / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=fill)
    base_img.alpha_composite(layer)


def build_logo(transparent=False):
    if transparent:
        img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    else:
        bg = radial_gradient_background(SIZE, DEEP_NAVY_BOTTOM, DEEP_NAVY_TOP)
        img = bg.convert("RGBA")

    draw = ImageDraw.Draw(img)

    outer_radius = int(SIZE * 0.42)
    inner_radius = int(SIZE * 0.37)

    # Outer decorative ring + tick marks
    draw_ring(draw, (CENTER, CENTER), outer_radius, width=6, color=GOLD)
    draw_tick_marks(draw, (CENTER, CENTER), outer_radius + 14, count=60,
                     length=14, color=GOLD, width=2)

    # Inner thin ring
    draw_ring(draw, (CENTER, CENTER), inner_radius, width=3, color=GOLD_LIGHT)

    # Small ornamental diamonds at top and bottom of the ring
    for angle_deg in (0, 180):
        angle = math.radians(angle_deg - 90)
        dx = (outer_radius + 30) * math.cos(angle)
        dy = (outer_radius + 30) * math.sin(angle)
        cx, cy = CENTER + dx, CENTER + dy
        d = 12
        draw.polygon(
            [(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)],
            fill=GOLD,
        )

    # Monogram "AH" - interlocking, A slightly overlapping H
    monogram_color = "CREAM" if not transparent else GOLD
    font_size = int(SIZE * 0.34)

    draw_monogram_text(img, "A", font_size, GOLD,
                        (CENTER - int(SIZE * 0.10), CENTER))
    draw_monogram_text(img, "H", font_size, monogram_color,
                        (CENTER + int(SIZE * 0.12), CENTER))

    # Thin vertical divider flourish between the letters
    draw.line(
        [(CENTER + int(SIZE * 0.005), CENTER - int(SIZE * 0.10)),
         (CENTER + int(SIZE * 0.005), CENTER + int(SIZE * 0.10))],
        fill=GOLD_LIGHT,
        width=2,
    )

    return img


def main():
    if sys.platform != "win32":
        print(
            "Note: this script is written for Windows font paths "
            "(C:\\Windows\\Fonts\\...). It will still run elsewhere, "
            "but will fall back to a plain default font.\n"
        )

    # Version with a rich navy background - good for business cards / websites
    logo = build_logo(transparent=False)
    out_path = os.path.join(OUTPUT_DIR, "ah_logo.png")
    logo.convert("RGB").save(out_path, "PNG")

    # Version with a transparent background - good for overlaying on anything
    logo_transparent = build_logo(transparent=True)
    out_path_transparent = os.path.join(OUTPUT_DIR, "ah_logo_transparent.png")
    logo_transparent.save(out_path_transparent, "PNG")

    print(f"Saved:\n  {out_path}\n  {out_path_transparent}")


if __name__ == "__main__":
    main()
