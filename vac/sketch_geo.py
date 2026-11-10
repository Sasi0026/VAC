"""Pure-Python geometry for the illustrations (no Kivy imports, so it is testable).

A drawing lives on a 100x100 canvas with y pointing down. Strokes:
    ("l", [x1, y1, x2, y2, ...])              polyline
    ("c", cx, cy, r)                          circle
    ("e", cx, cy, rx, ry)                     ellipse
    ("a", cx, cy, r, deg0, deg1)              arc, degrees clockwise from 3 o'clock
    ("q", [x0, y0, cx, cy, x1, y1, ...])      one or more chained quadratic curves
After the geometry a stroke may carry a line colour ("blue") and a fill ("f:blue").
"""
import math
import random

COLOR_KEYS = ("blue", "indigo", "teal", "amber", "ink")


def split_style(stroke):
    """-> (geometry, line colour, fill colour or None)"""
    line, fill = "ink", None
    end = len(stroke)
    while end > 1 and isinstance(stroke[end - 1], str):
        token = stroke[end - 1]
        if token.startswith("f:"):
            fill = token[2:]
        else:
            line = token
        end -= 1
    return stroke[:end], line, fill


def sample(stroke):
    """Stroke -> list of (x, y) points."""
    stroke = split_style(stroke)[0]
    kind = stroke[0]
    if kind == "l":
        p = stroke[1]
        pts = []
        for i in range(0, len(p) - 2, 2):
            x0, y0, x1, y1 = p[i], p[i + 1], p[i + 2], p[i + 3]
            n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 6))
            for k in range(n):
                t = k / n
                pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
        pts.append((p[-2], p[-1]))
        return pts
    if kind in ("c", "e", "a"):
        if kind == "c":
            cx, cy, rx = stroke[1:4]
            ry, a0, a1 = rx, 0, 360
        elif kind == "e":
            cx, cy, rx, ry = stroke[1:5]
            a0, a1 = 0, 360
        else:
            cx, cy, rx, a0, a1 = stroke[1:6]
            ry = rx
        n = max(10, int(abs(a1 - a0) / 9))
        return [
            (cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n)))
            for k in range(n + 1)
        ]
    if kind == "q":
        p = stroke[1]
        pts = [(p[0], p[1])]
        for i in range(0, len(p) - 2, 4):
            x0, y0, cx, cy, x1, y1 = p[i:i + 6]
            for k in range(1, 13):
                t = k / 12
                pts.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1,
                            (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1))
        return pts
    raise ValueError("unknown stroke %r" % (kind,))


def wobble(points, seed, amount=0.22):
    """A trace of seeded jitter keeps lines hand-made without looking shaky."""
    rnd = random.Random(seed)
    closed = len(points) > 2 and points[0] == points[-1]
    out = []
    for i, (x, y) in enumerate(points):
        a = amount if 0 < i < len(points) - 1 else 0
        out.append((x + rnd.uniform(-a, a), y + rnd.uniform(-a, a)))
    if closed:
        out[-1] = out[0]
    return out


def resolve(name, library, scenes, _depth=0):
    """Name -> flat list of (points, line colour, fill colour or None).
    Scenes place objects as (object, x, y, scale) and may add loose strokes."""
    if name in library:
        out = []
        for i, s in enumerate(library[name]):
            _, line, fill = split_style(s)
            out.append((wobble(sample(s), hash_seed(name, i)), line, fill))
        return out
    if name in scenes and _depth < 2:
        out = []
        for j, part in enumerate(scenes[name]):
            if part[0] in library:
                obj, ox, oy, sc = part
                for pts, line, fill in resolve(obj, library, scenes, _depth + 1):
                    out.append(([(ox + x * sc, oy + y * sc) for x, y in pts], line, fill))
            else:
                _, line, fill = split_style(part)
                out.append((wobble(sample(part), hash_seed(name, 1000 + j)), line, fill))
        return out
    return []


def hash_seed(name, i):
    return sum(ord(c) * (k + 1) for k, c in enumerate(name)) * 31 + i
