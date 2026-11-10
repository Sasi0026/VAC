"""Small constructors that keep the course files readable."""


def W(t, r, m, sk=None):
    """Word/phrase: target text, reading (romaji or ''), meaning, optional sketch name."""
    d = {"t": t, "r": r, "m": m}
    if sk:
        d["sk"] = sk
    return d


def G(pattern, meaning, *examples):
    """Grammar point with examples given as W(...) items."""
    return {"p": pattern, "m": meaning, "ex": list(examples)}


def D(speaker, t, r, m):
    """Dialogue line."""
    return {"s": speaker, "t": t, "r": r, "m": m}


def Q(q, options, answer=0, sub=""):
    """Multiple-choice question; `answer` indexes the correct option as written here."""
    d = {"type": "mcq", "q": q, "o": list(options), "a": answer}
    if sub:
        d["sub"] = sub
    return d


def L(lid, title, goal, intro="", items=(), points=(), dialogue=(), quiz=(), sketch=None, kind="words"):
    return {"id": lid, "title": title, "goal": goal, "intro": intro, "items": list(items), "points": list(points),
            "dialogue": list(dialogue), "quiz": list(quiz), "sketch": sketch, "kind": kind}


def O(lid, title, goal):
    """Outline lesson: the Teacher agent writes the content on first open, then it is cached."""
    return {"id": lid, "title": title, "goal": goal, "ai": True, "intro": "", "items": [], "points": [],
            "dialogue": [], "quiz": [], "sketch": None, "kind": "ai"}


def U(uid, title, summary, sketch, lessons):
    return {"id": uid, "title": title, "summary": summary, "sketch": sketch, "lessons": list(lessons)}


def outline_units(prefix, spec):
    """[(title, summary, sketch, [(lesson title, goal), ...]), ...] -> outline units."""
    units = []
    for i, (title, summary, sketch, lessons) in enumerate(spec, 1):
        uid = "%s-u%d" % (prefix, i)
        units.append(U(uid, title, summary, sketch,
                       [O("%s-l%d" % (uid, j), lt, lg) for j, (lt, lg) in enumerate(lessons, 1)]))
    return units
