"""Dev tool: render every illustration to a PNG contact sheet (needs Pillow).

    python tools/render_sketches.py out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw  # noqa: E402

from vac.content.sketches import OBJECTS, SCENES  # noqa: E402
from vac.sketch_geo import resolve  # noqa: E402

LINE = {"ink": (27, 36, 56), "blue": (0, 122, 255), "indigo": (88, 86, 214), "teal": (15, 168, 155),
        "amber": (242, 160, 61)}
FILL = {k: tuple(int(255 - (255 - c) * 0.24) for c in v) for k, v in LINE.items()}
FILL["white"] = (255, 255, 255)
FILL["ink"] = (222, 227, 236)
CELL, COLS, S = 220, 8, 3  # drawn at 3x and reduced, for smooth edges


def main(out):
    names = list(OBJECTS) + list(SCENES)
    rows = (len(names) + COLS - 1) // COLS
    sheet = Image.new("RGB", (CELL * COLS * S, CELL * rows * S), (238, 244, 255))
    draw = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        ox, oy = (i % COLS) * CELL * S, (i // COLS) * CELL * S
        k = (CELL - 40) / 100 * S
        for pts, line, fill in resolve(name, OBJECTS, SCENES):
            xy = [(ox + 20 * S + x * k, oy + 10 * S + y * k) for x, y in pts]
            if fill and len(xy) > 2:
                draw.polygon(xy, fill=FILL[fill])
            draw.line(xy, fill=LINE[line], width=3 * S, joint="curve")
        draw.text((ox + 8 * S, oy + (CELL - 18) * S), name, fill=(107, 117, 136))
    sheet = sheet.resize((CELL * COLS, CELL * rows), Image.LANCZOS)
    sheet.save(out)
    print("wrote", out, len(names), "illustrations")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sketches.png")
