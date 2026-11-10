"""Dev tool: tile the screenshots from tools/shots.py into contact sheets.

    python tools/sheet.py <shots folder> [per sheet]
"""
import os
import sys

from PIL import Image

folder = sys.argv[1]
per = int(sys.argv[2]) if len(sys.argv) > 2 else 6
files = sorted(f for f in os.listdir(folder) if f.endswith(".png") and not f.startswith("sheet"))
for n in range(0, len(files), per):
    imgs = [Image.open(os.path.join(folder, f)).convert("RGB") for f in files[n:n + per]]
    w, h = imgs[0].size
    sheet = Image.new("RGB", ((w + 12) * len(imgs), h), (200, 200, 205))
    for i, im in enumerate(imgs):
        sheet.paste(im, (i * (w + 12), 0))
    name = os.path.join(folder, "sheet%d.png" % (n // per + 1))
    sheet.save(name)
    print(name, sheet.size)
