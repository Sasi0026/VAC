"""Local learner memory (SQLite). Every agent reads and writes through this store."""
import json
import sqlite3
import threading
import time
from datetime import date, datetime, timedelta

SCHEMA = """
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS progress (lesson_id TEXT PRIMARY KEY, score REAL, day TEXT);
CREATE TABLE IF NOT EXISTS activity (
    id INTEGER PRIMARY KEY, day TEXT, ts REAL, kind TEXT, skill TEXT, minutes REAL, score REAL, detail TEXT);
CREATE TABLE IF NOT EXISTS tests (
    id INTEGER PRIMARY KEY, day TEXT, kind TEXT, exam_id TEXT, score REAL, max REAL, passed INTEGER, detail TEXT);
CREATE TABLE IF NOT EXISTS mistakes (
    lang TEXT, item TEXT, meaning TEXT, misses INTEGER, hits INTEGER, ts REAL, PRIMARY KEY (lang, item));
CREATE TABLE IF NOT EXISTS usage (day TEXT, model TEXT, tokens INTEGER, audio REAL, PRIMARY KEY (day, model));
CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS chat (id INTEGER PRIMARY KEY, thread TEXT, role TEXT, content TEXT, ts REAL);
"""


def today():
    return date.today().isoformat()


class Store:
    def __init__(self, path):
        self._lock = threading.RLock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        with self._lock:
            self._db.executescript(SCHEMA)
            self._db.commit()

    def _q(self, sql, args=()):
        with self._lock:
            return self._db.execute(sql, args).fetchall()

    def _x(self, sql, args=()):
        with self._lock:
            self._db.execute(sql, args)
            self._db.commit()

    # --- key/value -----------------------------------------------------------
    def get(self, key, default=None):
        rows = self._q("SELECT value FROM kv WHERE key=?", (key,))
        return json.loads(rows[0]["value"]) if rows else default

    def set(self, key, value):
        self._x("INSERT OR REPLACE INTO kv VALUES (?, ?)", (key, json.dumps(value, ensure_ascii=False)))

    @property
    def profile(self):
        return self.get("profile", {})

    def cache_get(self, key):
        rows = self._q("SELECT value FROM cache WHERE key=?", (key,))
        return json.loads(rows[0]["value"]) if rows else None

    def cache_set(self, key, value):
        self._x("INSERT OR REPLACE INTO cache VALUES (?, ?)", (key, json.dumps(value, ensure_ascii=False)))

    # --- lessons -------------------------------------------------------------
    def complete_lesson(self, lesson_id, score):
        self._x("INSERT OR REPLACE INTO progress VALUES (?, ?, ?)", (lesson_id, score, today()))

    def done_lessons(self):
        return {r["lesson_id"] for r in self._q("SELECT lesson_id FROM progress")}

    def lessons_since(self, days):
        since = (date.today() - timedelta(days=days)).isoformat()
        return [r["lesson_id"] for r in self._q("SELECT lesson_id FROM progress WHERE day>=? ORDER BY day", (since,))]

    # --- activity (feeds the calendar and the Scout agent) --------------------
    def log(self, kind, skill="", minutes=0, score=None, detail=None):
        self._x("INSERT INTO activity (day, ts, kind, skill, minutes, score, detail) VALUES (?,?,?,?,?,?,?)",
                (today(), time.time(), kind, skill, minutes, score, json.dumps(detail or {}, ensure_ascii=False)))

    def activities(self, days=None):
        if days is None:
            rows = self._q("SELECT * FROM activity ORDER BY ts")
        else:
            since = (date.today() - timedelta(days=days)).isoformat()
            rows = self._q("SELECT * FROM activity WHERE day>=? ORDER BY ts", (since,))
        out = []
        for r in rows:
            d = dict(r)
            d["detail"] = json.loads(d["detail"] or "{}")
            out.append(d)
        return out

    def month_days(self, year, month):
        """{'YYYY-MM-DD': {'minutes': m, 'kinds': set}} for one month."""
        prefix = "%04d-%02d" % (year, month)
        out = {}
        for r in self._q("SELECT day, kind, minutes FROM activity WHERE day LIKE ?", (prefix + "%",)):
            d = out.setdefault(r["day"], {"minutes": 0, "kinds": set()})
            d["minutes"] += r["minutes"] or 0
            d["kinds"].add(r["kind"])
        return out

    def minutes_today(self, skill=None):
        if skill:
            rows = self._q("SELECT SUM(minutes) m FROM activity WHERE day=? AND skill=?", (today(), skill))
        else:
            rows = self._q("SELECT SUM(minutes) m FROM activity WHERE day=?", (today(),))
        return rows[0]["m"] or 0

    def streak(self):
        days = {r["day"] for r in self._q("SELECT DISTINCT day FROM activity")}
        d = date.today()
        if d.isoformat() not in days:
            d -= timedelta(days=1)  # today not done yet: the streak is still alive
        n = 0
        while d.isoformat() in days:
            n += 1
            d -= timedelta(days=1)
        return n

    def active_days(self, window=14):
        since = (date.today() - timedelta(days=window - 1)).isoformat()
        return len(self._q("SELECT DISTINCT day FROM activity WHERE day>=?", (since,)))

    # --- tests ---------------------------------------------------------------
    def save_test(self, kind, exam_id, score, max_score, passed, detail=None):
        self._x("INSERT INTO tests (day, kind, exam_id, score, max, passed, detail) VALUES (?,?,?,?,?,?,?)",
                (today(), kind, exam_id, score, max_score, int(bool(passed)),
                 json.dumps(detail or {}, ensure_ascii=False)))

    def tests(self, kind=None, limit=50):
        if kind:
            rows = self._q("SELECT * FROM tests WHERE kind=? ORDER BY id DESC LIMIT ?", (kind, limit))
        else:
            rows = self._q("SELECT * FROM tests ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in rows]

    def days_since_test(self, kind):
        rows = self._q("SELECT day FROM tests WHERE kind=? ORDER BY id DESC LIMIT 1", (kind,))
        if not rows:
            start = self.get("started", today())
            return (date.today() - date.fromisoformat(start)).days, False
        return (date.today() - date.fromisoformat(rows[0]["day"])).days, True

    # --- mistakes (what to re-test) -------------------------------------------
    def mark(self, lang, item, meaning, correct):
        rows = self._q("SELECT misses, hits FROM mistakes WHERE lang=? AND item=?", (lang, item))
        misses, hits = (rows[0]["misses"], rows[0]["hits"]) if rows else (0, 0)
        if correct:
            if not rows:
                return
            hits += 1
        else:
            misses += 1
            hits = 0
        self._x("INSERT OR REPLACE INTO mistakes VALUES (?,?,?,?,?,?)", (lang, item, meaning, misses, hits, time.time()))

    def weak_items(self, lang, limit=10):
        """Items missed and not yet answered correctly twice in a row."""
        rows = self._q("SELECT item, meaning, misses FROM mistakes WHERE lang=? AND hits<2 ORDER BY misses DESC, ts DESC "
                       "LIMIT ?", (lang, limit))
        return [dict(r) for r in rows]

    # --- AI usage (free-tier budget) ------------------------------------------
    def add_usage(self, model, tokens=0, audio=0.0):
        rows = self._q("SELECT tokens, audio FROM usage WHERE day=? AND model=?", (today(), model))
        t, a = (rows[0]["tokens"], rows[0]["audio"]) if rows else (0, 0.0)
        self._x("INSERT OR REPLACE INTO usage VALUES (?,?,?,?)", (today(), model, t + tokens, a + audio))

    def usage_today(self):
        return {r["model"]: {"tokens": r["tokens"], "audio": r["audio"]}
                for r in self._q("SELECT * FROM usage WHERE day=?", (today(),))}

    # --- chat threads -----------------------------------------------------------
    def chat_add(self, thread, role, content):
        self._x("INSERT INTO chat (thread, role, content, ts) VALUES (?,?,?,?)", (thread, role, content, time.time()))

    def chat_history(self, thread, limit=40):
        rows = self._q("SELECT role, content FROM chat WHERE thread=? ORDER BY id DESC LIMIT ?", (thread, limit))
        return [dict(r) for r in reversed(rows)]

    def chat_clear(self, thread):
        self._x("DELETE FROM chat WHERE thread=?", (thread,))

    def reset(self):
        with self._lock:
            for t in ("kv", "progress", "activity", "tests", "mistakes", "usage", "cache", "chat"):
                self._db.execute("DELETE FROM " + t)
            self._db.commit()


def now_hour():
    return datetime.now().hour
