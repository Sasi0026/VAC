"""The VAC team: five agents that share one learner memory (the Store).

    Curator   plans the course around the learner's goal, level, pace and interests
    Teacher   explains, converses, corrects writing, checks pronunciation and handwriting
    Examiner  sets and marks lesson quizzes, daily/weekly/monthly check-ins and mock exams
    Scout     studies results, participation and interests, and feeds simulations back to the Curator
    Buddy     the voice of the team: a best friend who greets, reminds and cheers

Everything that can work offline does (plans, quizzes, mock scoring, insights, cheers). Calls that
need a language model go through vac.ai and raise AIError when no key or connection is available.
"""
import difflib
import random
import re
from datetime import date

from . import content
from .content.scenarios import SCENARIOS, for_interests
from .db import now_hour, today

FRIEND = (
    "You are Vac, the learner's best friend who happens to be a brilliant language coach. You sit beside them, "
    "you are warm, relaxed and brief, you never lecture, you notice effort and you celebrate wins. "
    "Never invent exam rules. Plain text only: no markdown, no asterisks, no emoji."
)
SKILLS = ["vocabulary", "grammar", "listening", "reading", "writing", "speaking"]


def skill_of(q):
    """Which skill a question exercises."""
    if q.get("skill"):
        return q["skill"]
    if q["type"] == "write":
        return "writing"
    if q["type"] == "speak":
        return "speaking"
    part = q.get("part", "").lower()
    if q.get("say") or "hören" in part or "listening" in part or "response" in part or "verbal" in part:
        return "listening"
    if "grammar" in part:
        return "grammar"
    if "schreiben" in part:
        return "writing"
    if any(k in part for k in ("comprehension", "retrieval", "lesen", "reading")):
        return "reading"
    return "vocabulary"


class Team:
    def __init__(self, store, ai):
        self.store, self.ai = store, ai
        self.curator, self.teacher = Curator(self), Teacher(self)
        self.examiner, self.scout, self.buddy = Examiner(self), Scout(self), Buddy(self)

    # --- shared learner memory -------------------------------------------------
    @property
    def profile(self):
        return self.store.profile

    @property
    def lang(self):
        return self.profile.get("lang", "ja")

    @property
    def course(self):
        return content.course(self.lang)

    @property
    def level(self):
        lv = content.find_level(self.profile.get("level", ""))
        return lv if lv and lv["id"].startswith(self.lang) else self.course["levels"][0]

    def memory(self):
        """Compact learner summary placed in every agent's prompt."""
        p = self.profile
        weak = ", ".join(w["item"] for w in self.store.weak_items(self.lang, 6)) or "none recorded yet"
        skills = self.scout.skills()
        weakest = min(skills, key=skills.get) if skills else "unknown"
        return (
            "LEARNER: %s. Learning %s for the %s. Current level: %s (%s). Goal: %s. Interests: %s. "
            "Weak items: %s. Weakest skill: %s. Explanations are in English."
            % (p.get("name", "friend"), self.course["name"], self.course["exam"], self.level["title"],
               self.level["cefr"], p.get("goal", "everyday life"), ", ".join(p.get("interests", [])) or "general",
               weak, weakest))

    def record(self, kind, skill="", minutes=0, score=None, detail=None):
        self.store.log(kind, skill, minutes, score, detail)


# ============================================================================== Curator
class Curator:
    def __init__(self, team):
        self.t = team

    def custom_lessons(self):
        return self.t.store.get("custom:" + self.t.lang, [])

    def next_lesson(self):
        """First unfinished lesson of the current level -> (unit, lesson) or None."""
        done = self.t.store.done_lessons()
        for u in self.t.level["units"]:
            for ls in u["lessons"]:
                if ls["id"] not in done:
                    return u, ls
        return None

    def level_complete(self, level=None):
        d, n = content.level_progress(level or self.t.level, self.t.store.done_lessons())
        return n > 0 and d >= n

    def mock_passed(self, exam_id):
        return any(t["passed"] for t in self.t.store.tests("mock") if t["exam_id"] == exam_id)

    def maybe_advance(self):
        """Move to the next level once the lessons are done and the mock is passed. Returns the new level."""
        lv = self.t.level
        if not (self.level_complete(lv) and self.mock_passed(content.level_exam(lv))):
            return None
        levels = self.t.course["levels"]
        i = levels.index(lv)
        if i + 1 >= len(levels):
            return None
        p = self.t.profile
        p["level"] = levels[i + 1]["id"]
        self.t.store.set("profile", p)
        return levels[i + 1]

    def pace(self):
        """Plain-language forecast for the current level."""
        d, n = content.level_progress(self.t.level, self.t.store.done_lessons())
        per_day = max(1, round(self.t.profile.get("minutes", 20) / 20))
        days = -(-(n - d) // per_day)
        if n - d == 0:
            return "All %d lessons done. The mock test is open." % n
        return "%d of %d lessons done. At %d a day you finish %s in about %d day%s." % (
            d, n, per_day, self.t.level["name"], days, "" if days == 1 else "s")

    def today(self):
        """Today's plan: ordered task dicts for the Home screen."""
        s = self.t.store
        acts = [a for a in s.activities(0)]
        kinds = {a["kind"] for a in acts}
        tasks = []
        nxt = self.next_lesson()
        if nxt:
            unit, ls = nxt
            did = bool(s.lessons_since(0))
            tasks.append({"kind": "lesson", "icon": "book-open", "title": ls["title"],
                          "sub": "Today's lesson is done. Tap to keep going." if did else
                                 "Lesson · %s · %s" % (self.t.level["name"], unit["title"]),
                          "done": did, "lesson": ls})
        else:
            exam_id = content.level_exam(self.t.level)
            tasks.append({"kind": "mock", "icon": "seal-check", "title": content.EXAMS[exam_id]["name"] + " mock",
                          "sub": "You finished every lesson. Time to sit the mock.", "done": self.mock_passed(exam_id),
                          "exam_id": exam_id})
        tasks.append({"kind": "daily", "icon": "list-checks", "title": "Daily check-in",
                      "sub": "5 minutes on what you learned, weak spots first", "done": "daily" in kinds})
        sc = self.t.scout.suggest(1)[0]
        tasks.append({"kind": "scenario", "icon": sc["icon"], "title": sc["title"],
                      "sub": "Speaking simulation picked for your interests", "done": "talk" in kinds,
                      "scenario": sc})
        for kind, every, label in (("weekly", 7, "Weekly test"), ("monthly", 30, "Monthly test")):
            days, _ = s.days_since_test(kind)
            if days >= every and s.done_lessons():
                tasks.append({"kind": kind, "icon": "exam", "title": label,
                              "sub": "Due now: covers the last %d days" % every, "done": False})
        return tasks

    def write_lesson(self, topic):
        """AI: a personal lesson on a topic the learner cares about. Saved under 'For you'."""
        t = self.t
        data = t.ai.chat([
            {"role": "system", "content": FRIEND + " You are acting as the Curator, who designs lessons. " + t.memory()},
            {"role": "user", "content":
                "Design one short %s lesson at %s level about: %s. It must teach language the learner can use in that "
                "situation and stay within the level. Return JSON only with keys: title (English, max 5 words), "
                "goal (English, one sentence), intro (English, two sentences), items (8 objects with t = %s word or "
                "phrase, r = romanised reading or empty string, m = English meaning), points (1 or 2 objects with "
                "p = pattern, m = English meaning, ex = 2 objects of t, r, m), dialogue (4 objects with s = speaker, "
                "t, r, m), quiz (3 objects with q = question, o = 4 options with the correct one FIRST)."
                % (t.course["name"], t.level["title"], topic, t.course["name"])}],
            json_mode=True, max_tokens=1800, temperature=0.5)
        ls = clean_lesson(data, "custom-%s-%d" % (t.lang, random.randrange(10 ** 8)))
        ls["custom"] = True
        saved = self.custom_lessons()
        saved.insert(0, ls)
        t.store.set("custom:" + t.lang, saved[:20])
        return ls


def clean_lesson(data, lid, base=None):
    """Validate AI lesson JSON into the lesson schema (raises ValueError if unusable)."""
    def s(v):
        return str(v).strip() if v is not None else ""

    def item(d):
        return {"t": s(d.get("t")), "r": s(d.get("r")), "m": s(d.get("m"))}

    if not isinstance(data, dict):
        raise ValueError("lesson is not an object")
    ls = dict(base or {})
    ls.update({
        "id": lid, "title": s(data.get("title")) or ls.get("title", "Lesson"),
        "goal": s(data.get("goal")) or ls.get("goal", ""), "intro": s(data.get("intro")),
        "items": [item(d) for d in data.get("items", []) if isinstance(d, dict) and d.get("t")],
        "points": [{"p": s(d.get("p")), "m": s(d.get("m")),
                    "ex": [item(e) for e in d.get("ex", []) if isinstance(e, dict) and e.get("t")]}
                   for d in data.get("points", []) if isinstance(d, dict) and d.get("p")],
        "dialogue": [{"s": s(d.get("s")) or "A", "t": s(d.get("t")), "r": s(d.get("r")), "m": s(d.get("m"))}
                     for d in data.get("dialogue", []) if isinstance(d, dict) and d.get("t")],
        "quiz": [{"type": "mcq", "q": s(d.get("q")), "o": [s(o) for o in d["o"]][:4], "a": 0}
                 for d in data.get("quiz", [])
                 if isinstance(d, dict) and d.get("q") and isinstance(d.get("o"), list) and len(d["o"]) >= 2],
        "sketch": ls.get("sketch"), "kind": "ai", "ai": False,
    })
    if not ls["items"] and not ls["points"]:
        raise ValueError("lesson has no content")
    return ls


# ============================================================================== Teacher
class Teacher:
    def __init__(self, team):
        self.t = team

    def _system(self, mode, scenario=None):
        t = self.t
        lang = t.course["name"]
        if mode == "scenario":
            tasks = "; ".join("%d) %s" % (i, x) for i, x in enumerate(scenario["tasks"]))
            return (
                FRIEND + " Right now you are role-playing so the learner can rehearse real life. " + t.memory() +
                " SCENE: %s You play %s. Speak only %s, at %s level, one or two short sentences per turn, and "
                "always end with something the learner can respond to. Learner goals: %s. "
                "Return JSON only: reply (your line in %s), translation (English), fix (empty string, or one short "
                "English sentence correcting the learner's most important mistake and showing the right form), "
                "tasks_done (list of goal numbers the learner has achieved so far)."
                % (scenario["situation"], scenario["role"], lang, t.level["title"], tasks, lang))
        if mode == "writing":
            return (
                FRIEND + " You are acting as the Teacher marking a piece of writing. " + t.memory() +
                " Return JSON only: reply (two sentences of honest, kind feedback in English), corrected (the "
                "learner's text rewritten correctly in %s), mistakes (up to 5 objects with wrong, right, why in "
                "English), score (0 to 10 for this level)." % lang)
        return (
            FRIEND + " You are acting as the Teacher. " + t.memory() +
            " Answer questions about %s clearly in English with short %s examples (give a reading for Japanese). "
            "If the learner writes in %s, reply to it and correct mistakes. Keep answers under 110 words. "
            "Return JSON only: reply (your answer), translation (empty string), fix (empty string, or one sentence "
            "correcting a mistake in the learner's %s), tasks_done (empty list)." % (lang, lang, lang, lang))

    def reply(self, thread, mode, text, scenario=None):
        """One conversational turn. Stores both sides in the thread and returns the parsed reply."""
        s = self.t.store
        history = s.chat_history(thread, 8)
        msgs = [{"role": "system", "content": self._system(mode, scenario)}]
        msgs += [{"role": h["role"], "content": h["content"]} for h in history]
        msgs.append({"role": "user", "content": text})
        out = self.t.ai.chat(msgs, json_mode=True, max_tokens=900 if mode == "writing" else 320,
                             temperature=0.3 if mode == "writing" else 0.7)
        out.setdefault("reply", "")
        s.chat_add(thread, "user", text)
        s.chat_add(thread, "assistant", str(out.get("reply", "")))
        return out

    def expand(self, lesson, level):
        """AI: write the content of an outline lesson once, then cache it."""
        t = self.t
        cached = t.store.cache_get("lesson:" + lesson["id"])
        if cached:
            return cached
        data = t.ai.chat([
            {"role": "system", "content": FRIEND + " You are acting as the Teacher writing a lesson. " + t.memory()},
            {"role": "user", "content":
                "Write the lesson '%s' (%s) for %s, a level of the %s course. Stay inside what that level of the "
                "%s tests. Return JSON only with keys: intro (English, 2-3 sentences that explain the idea), items "
                "(8 objects: t = %s word or phrase, r = romanised reading or empty string, m = English meaning), "
                "points (2 objects: p = pattern, m = English explanation, ex = 2 objects of t, r, m), dialogue "
                "(4 objects: s = speaker, t, r, m), quiz (4 objects: q = question, o = 4 options with the correct "
                "one FIRST)." % (lesson["title"], lesson["goal"], level["title"], t.course["name"], t.course["exam"],
                                 t.course["name"])}],
            json_mode=True, max_tokens=2000, temperature=0.4)
        ls = clean_lesson(data, lesson["id"], base=lesson)
        t.store.cache_set("lesson:" + lesson["id"], ls)
        return ls

    @staticmethod
    def pronunciation(target, heard):
        """Compare what the speech model heard with the target. -> (score 0-100, verdict)."""
        def norm(x):
            return re.sub(r"[\s\W_]+", "", x.lower(), flags=re.U)

        a, b = norm(target), norm(heard)
        if not b:
            return 0, "I couldn't hear anything. Hold the button and speak a little closer."
        score = int(round(difflib.SequenceMatcher(None, a, b).ratio() * 100))
        if score >= 90:
            return score, "That was clear. The speech model heard exactly what you meant."
        if score >= 65:
            return score, "Close. Compare what was heard with the target and try the part that differs."
        return score, "Not there yet. Listen once more, slow down, and say it in two halves."

    def check_writing_photo(self, image_path, expected=""):
        t = self.t
        ask = ("The learner is practising handwriting in %s (%s level)." % (t.course["name"], t.level["title"]))
        if expected:
            ask += " They were asked to write: %s." % expected
        ask += (" Read the handwriting in the photo (phone cameras may deliver it turned on its side). Return JSON only: read (exactly what is written), correct "
                "(true or false), feedback (two friendly English sentences: what is right, and one concrete thing to "
                "fix about a stroke, shape, spelling or grammar).")
        return t.ai.see(image_path, ask)

    def name_object(self, image_path):
        t = self.t
        return t.ai.see(image_path, (
            "Name the main object in this photo for a %s learner at %s level. Return JSON only: word (in %s), "
            "reading (romanised reading, or empty string), meaning (English), sentence (one simple %s sentence using "
            "the word), sentence_meaning (English)." % (t.course["name"], t.level["title"], t.course["name"],
                                                         t.course["name"])))


# ============================================================================== Examiner
class Examiner:
    def __init__(self, team):
        self.t = team

    # --- building papers --------------------------------------------------------
    @staticmethod
    def _prep(q):
        """Copy a question and shuffle its options (the source always lists the answer first)."""
        q = dict(q)
        if q["type"] == "mcq":
            opts = list(dict.fromkeys(q["o"]))
            right = q["o"][q.get("a", 0)]
            random.shuffle(opts)
            q["o"], q["a"] = opts, opts.index(right)
        return q

    def _item_q(self, it, pool, mode):
        lang = self.t.lang
        others = [p for p in pool if p["t"] != it["t"] and p["m"] != it["m"]]
        random.shuffle(others)
        picks, seen = [], set()
        for p in others:
            key = p["m"] if mode != "reverse" else p["t"]
            if key not in seen:
                seen.add(key)
                picks.append(p)
            if len(picks) == 3:
                break
        if mode == "reverse":
            q = {"type": "mcq", "q": "How do you say this in %s?" % self.t.course["name"], "sub": it["m"],
                 "o": [it["t"]] + [p["t"] for p in picks], "skill": "vocabulary"}
        elif mode == "listen":
            opts = "t" if lang == "en" else "m"
            q = {"type": "mcq", "q": "Listen. What did you hear?", "say": it["t"],
                 "o": [it[opts]] + [p[opts] for p in picks], "skill": "listening"}
        else:
            q = {"type": "mcq", "q": "What does this mean?", "sub": it["t"],
                 "o": [it["m"]] + [p["m"] for p in picks], "skill": "vocabulary"}
        q.update(a=0, sec="all", item=[it["t"], it["m"]])
        return q

    def _paper(self, title, kind, questions, pass_total, minutes=0, lesson_id=None):
        return {"title": title, "kind": kind, "exam_id": "", "minutes": minutes, "lang": self.t.lang,
                "sections": [{"id": "all", "name": "Score", "max": 100, "pass": 0}], "pass_total": pass_total,
                "total": 100, "band": False, "lesson_id": lesson_id,
                "questions": [self._prep(dict(q, sec="all")) for q in questions]}

    def lesson_quiz(self, lesson, level):
        pool = content.item_pool(level) if level else list(lesson["items"])
        if len(pool) < 4:
            pool = pool + lesson["items"]
        items = list(lesson["items"])
        random.shuffle(items)
        qs = []
        for i, it in enumerate(items[:7]):
            qs.append(self._item_q(it, pool, ("meaning", "reverse", "listen")[i % 3]))
        qs += [dict(q, skill="grammar") for q in lesson.get("quiz", [])]
        random.shuffle(qs)
        return self._paper(lesson["title"], "lesson", qs, 70, lesson_id=lesson["id"])

    def _learned(self, days=None):
        """Items and authored questions from finished lessons (optionally only recent ones)."""
        s = self.t.store
        ids = set(s.lessons_since(days)) if days else s.done_lessons()
        items, quiz = [], []
        lessons = content.lessons_of(self.t.level) + self.t.curator.custom_lessons()
        for ls in lessons:
            if ls["id"] in ids:
                ls = s.cache_get("lesson:" + ls["id"]) or ls
                items += ls["items"]
                quiz += ls.get("quiz", [])
        if not items:  # nothing finished yet: preview the first lesson
            first = self.t.level["units"][0]["lessons"][0]
            items, quiz = list(first["items"]), list(first.get("quiz", []))
        return items, quiz

    def checkin(self, kind):
        """Daily (8 questions + writing), weekly (16 + writing + speaking) or monthly (24 + 2 + 1)."""
        t = self.t
        n, days, title = {"daily": (8, None, "Daily check-in"), "weekly": (16, 7, "Weekly test"),
                          "monthly": (24, 30, "Monthly test")}[kind]
        items, quiz = self._learned(days)
        pool = content.item_pool(t.level) or items
        weak = {w["item"] for w in t.store.weak_items(t.lang, 12)}
        ranked = sorted(items, key=lambda it: (it["t"] not in weak, random.random()))
        qs = []
        n_items = n - min(len(quiz), n // 3)
        for i, it in enumerate(ranked[:n_items]):
            qs.append(self._item_q(it, pool, ("meaning", "listen", "reverse")[i % 3]))
        random.shuffle(quiz)
        qs += [dict(q, skill="grammar") for q in quiz[:n - len(qs)]]
        random.shuffle(qs)
        scenes = for_interests(t.profile.get("interests", []))
        random.shuffle(scenes[:4])
        rubric = ("Short everyday writing at %s level: the task is done, the message is understandable, and grammar "
                  "and vocabulary fit the level." % t.level["title"])
        sc = random.choice(scenes[:4])
        qs.append({"type": "write", "part": "Scenario writing", "max": 5, "min_words": 0, "rubric": rubric, "model": "",
                   "q": "%s\nWrite 3 to 5 sentences in %s." % (sc["write"], t.course["name"]), "scenario": sc["id"]})
        if kind != "daily":
            sc2 = random.choice(scenes[:4])
            qs.append({"type": "speak", "part": "Scenario speaking", "max": 5, "rubric": rubric.replace("writing", "speaking"),
                       "model": "", "q": "Imagine this: %s\nSay 3 or 4 sentences in %s: %s."
                                         % (sc2["situation"], t.course["name"], sc2["tasks"][0].lower())})
        if kind == "monthly":
            qs.append({"type": "write", "part": "Exam-style writing", "max": 5, "min_words": 0, "rubric": rubric,
                       "model": "", "q": "Write a short message (about 40 words) in %s to a friend about what you did "
                                         "this month and what you plan next month." % t.course["name"]})
        return self._paper(title, kind, qs, 60, minutes={"daily": 0, "weekly": 15, "monthly": 25}[kind])

    def mock(self, exam_id):
        src, spec = content.MOCKS[exam_id], content.EXAMS[exam_id]
        pass_total = spec["pass_total"]
        if spec.get("band"):
            pass_total = float(self.t.profile.get("band", 6.0)) * 4
        return {"title": src["title"], "kind": "mock", "exam_id": exam_id, "minutes": src["minutes"],
                "lang": exam_id.split("-")[0], "sections": spec["score_sections"], "pass_total": pass_total,
                "total": spec["total"], "band": bool(spec.get("band")), "note": src["note"], "lesson_id": None,
                "questions": [self._prep(q) for q in src["questions"]]}

    def generate_mock(self, level):
        """AI: a compact mock for a level with no built-in paper, written to the official blueprint. Cached."""
        t = self.t
        exam_id = content.level_exam(level)
        spec = content.EXAMS[exam_id]
        key = "mock:" + exam_id
        cached = t.store.cache_get(key)
        if not cached:
            secs = ", ".join("%s (id %s)" % (s["name"], s["id"]) for s in spec["score_sections"])
            types = "; ".join("%s: %s" % (k, ", ".join(v)) for k, v in spec.get("item_types", {}).items())
            data = t.ai.chat([
                {"role": "system", "content": "You are an examiner who writes original practice papers that follow "
                                              "official test formats exactly. Never copy real past papers."},
                {"role": "user", "content":
                    "Write a compact mock for %s (%s). Scoring sections: %s. %s Official sections and minutes: %s. "
                    "Write 6 questions per scoring section at exactly this level. Return JSON only: questions = list "
                    "of objects with sec (section id), part (item type name), q (the question), sub (passage or "
                    "sentence shown to the candidate, or empty string), say (for listening items only: the script to "
                    "be read aloud, otherwise empty string), o (3 or 4 options with the correct one FIRST)."
                    % (spec["name"], spec["can_do"], secs, ("Item types: " + types + ".") if types else "",
                       "; ".join("%s %d min" % o for o in spec["official"]))}],
                json_mode=True, max_tokens=6000, temperature=0.5)
            ids = {s["id"] for s in spec["score_sections"]}
            qs = []
            for d in data.get("questions", []) if isinstance(data, dict) else []:
                if isinstance(d, dict) and d.get("q") and isinstance(d.get("o"), list) and len(d["o"]) >= 2 \
                        and d.get("sec") in ids:
                    q = {"type": "mcq", "sec": d["sec"], "part": str(d.get("part", "")), "q": str(d["q"]),
                         "sub": str(d.get("sub") or ""), "o": [str(o) for o in d["o"]][:4], "a": 0}
                    if d.get("say"):
                        q["say"] = str(d["say"])
                    qs.append(q)
            if len(qs) < 8:
                raise ValueError("The Examiner could not write a full paper. Try again.")
            cached = qs
            t.store.cache_set(key, cached)
        return {"title": spec["name"] + " mock test", "kind": "mock", "exam_id": exam_id, "minutes": 30,
                "lang": exam_id.split("-")[0], "sections": spec["score_sections"], "pass_total": spec["pass_total"],
                "total": spec["total"], "band": bool(spec.get("band")), "lesson_id": None,
                "note": "Written by the Examiner agent to the official blueprint.",
                "questions": [self._prep(q) for q in cached]}

    # --- marking ----------------------------------------------------------------
    def grade_open(self, q, answer):
        """AI: mark a writing or speaking answer. -> {'score', 'feedback', 'better'}"""
        t = self.t
        out = t.ai.chat([
            {"role": "system", "content": FRIEND + " You are acting as the Examiner: fair, exact, encouraging. " +
                                          t.memory()},
            {"role": "user", "content":
                "Task: %s\nMarking criteria: %s\nMaximum score: %s\n%sCandidate's answer%s:\n%s\n\n"
                "Return JSON only: score (number from 0 to %s, halves allowed), feedback (two or three English "
                "sentences: what worked, then the one change that would raise the score most), better (a model "
                "answer at this level)."
                % (q["q"], q["rubric"], q["max"],
                   ("Minimum words: %d\n" % q["min_words"]) if q.get("min_words") else "",
                   " (speech transcript)" if q["type"] == "speak" else "", answer, q["max"])}],
            json_mode=True, max_tokens=900, temperature=0.2)
        try:
            score = float(out.get("score", 0))
        except (TypeError, ValueError):
            score = 0.0
        return {"score": max(0.0, min(float(q["max"]), score)), "feedback": str(out.get("feedback", "")),
                "better": str(out.get("better", ""))}

    @staticmethod
    def check_text(q, answer):
        norm = re.sub(r"[\s£$.,!?]+", " ", answer.lower()).strip()
        return any(norm == re.sub(r"[\s£$.,!?]+", " ", a.lower()).strip() for a in q["accept"])

    def mark(self, paper, results):
        """results: one {'points', 'max'} per question -> full result dict; also updates the learner memory."""
        t = self.t
        secs = []
        for s in paper["sections"]:
            got = sum(r["points"] for q, r in zip(paper["questions"], results) if q.get("sec", "all") == s["id"])
            mx = sum(r["max"] for q, r in zip(paper["questions"], results) if q.get("sec", "all") == s["id"])
            scaled = (got / mx * s["max"]) if mx else 0
            if paper["band"]:
                scaled = round(scaled * 2) / 2
            secs.append({"name": s["name"], "score": round(scaled, 1), "max": s["max"], "pass": s["pass"],
                         "ok": scaled >= s["pass"]})
        total = sum(s["score"] for s in secs)
        passed = total >= paper["pass_total"] and all(s["ok"] for s in secs)
        result = {"sections": secs, "total": round(total, 1), "max": paper["total"], "passed": passed,
                  "pass_total": paper["pass_total"], "band": None}
        if paper["band"]:
            result["band"] = round(total / len(secs) * 2) / 2
        # learner memory: per-skill scores, weak items, test history
        by_skill = {}
        for q, r in zip(paper["questions"], results):
            a = by_skill.setdefault(skill_of(q), [0, 0])
            a[0] += r["points"]
            a[1] += r["max"]
            if q.get("item"):
                t.store.mark(paper["lang"], q["item"][0], q["item"][1], r["points"] >= r["max"])
        # a failed lesson quiz is logged as practice, so the lesson stays on today's plan
        kind = "practice" if paper["kind"] == "lesson" and not passed else paper["kind"]
        for skill, (got, mx) in by_skill.items():
            if mx:
                t.record(kind, skill, minutes=0, score=got / mx)
        minutes = max(2, len(paper["questions"]) * 0.6)
        t.record(kind, "", minutes=minutes, score=total / paper["total"] if paper["total"] else 0,
                 detail={"title": paper["title"]})
        if paper["kind"] == "lesson":
            if passed and paper.get("lesson_id"):
                t.store.complete_lesson(paper["lesson_id"], total)
        else:
            t.store.save_test(paper["kind"], paper["exam_id"], total, paper["total"], passed, {"sections": secs})
        result["new_level"] = t.curator.maybe_advance() if paper["kind"] == "mock" and passed else None
        return result


# ============================================================================== Scout
class Scout:
    def __init__(self, team):
        self.t = team

    def skills(self, days=30):
        """Average score per skill (0-1) from recent graded work."""
        agg = {}
        for a in self.t.store.activities(days):
            if a["skill"] and a["score"] is not None:
                agg.setdefault(a["skill"], []).append(a["score"])
        return {k: sum(v) / len(v) for k, v in agg.items()}

    def interest_counts(self):
        counts = {}
        for a in self.t.store.activities(60):
            if a["kind"] == "talk":
                i = a["detail"].get("interest")
                counts[i] = counts.get(i, 0) + 1
        return counts

    def suggest(self, n=4):
        """Simulations for this learner: their interests first, least-practised first."""
        played = {}
        for a in self.t.store.activities(60):
            if a["kind"] == "talk":
                sid = a["detail"].get("scenario")
                played[sid] = played.get(sid, 0) + 1
        ordered = for_interests(self.t.profile.get("interests", []))
        mine = sum(1 for s in ordered if s["interest"] in self.t.profile.get("interests", []))
        head = sorted(ordered[:mine], key=lambda s: played.get(s["id"], 0))
        tail = sorted(ordered[mine:], key=lambda s: played.get(s["id"], 0))
        return (head + tail)[:n]

    def insights(self):
        """Plain-language findings for the Progress screen (works offline)."""
        s, t = self.t.store, self.t
        out = []
        active = s.active_days(14)
        if active == 0:
            return ["No activity yet. Finish one lesson and I'll start learning how you learn."]
        out.append("You showed up on %d of the last 14 days." % active +
                   (" That rhythm is what passes exams." if active >= 10 else " Short daily sessions beat long rare ones."))
        skills = self.skills()
        if skills:
            best, worst = max(skills, key=skills.get), min(skills, key=skills.get)
            if best != worst:
                out.append("Strongest: %s (%d%%). Needs work: %s (%d%%), so I've asked the Examiner to weight it."
                           % (best, skills[best] * 100, worst, skills[worst] * 100))
            else:
                out.append("%s is at %d%% so far." % (best.capitalize(), skills[best] * 100))
        weak = s.weak_items(t.lang, 5)
        if weak:
            out.append("Keeps slipping: " + ", ".join(w["item"] for w in weak) + ". These come back in your next check-in.")
        talk = sum(a["minutes"] for a in s.activities(7) if a["kind"] == "talk")
        if talk < 20:
            out.append("Only %d minutes of speaking this week. Try a simulation today: %s."
                       % (talk, self.suggest(1)[0]["title"]))
        counts = self.interest_counts()
        if counts:
            top = max(counts, key=counts.get)
            out.append("You keep choosing %s scenarios, so the Curator will add more of them." % top)
        return out

    def reflect(self):
        """AI: a short personal note, refreshed at most once a day."""
        s = self.t.store
        note = s.get("scout_note", {})
        if note.get("day") == today():
            return note["text"]
        text = self.t.ai.chat([
            {"role": "system", "content": FRIEND + " You are acting as the Scout, who studies how the learner learns. " +
                                          self.t.memory()},
            {"role": "user", "content": "Findings: %s\nWrite three short sentences to the learner: one thing they are "
                                        "doing well, one pattern you noticed, and one specific exercise for today "
                                        "that fits their interests." % " ".join(self.insights())}],
            max_tokens=220, temperature=0.7)
        s.set("scout_note", {"day": today(), "text": text})
        return text


# ============================================================================== Buddy
class Buddy:
    """Local, instant and free: the friend's voice never waits for a network call."""

    def __init__(self, team):
        self.t = team

    def _name(self):
        return self.t.profile.get("name") or "friend"

    def greeting(self):
        """-> (hello, headline, message) for the Home screen."""
        s, name, h = self.t.store, self._name(), now_hour()
        hello = "Good morning" if h < 12 else "Good afternoon" if h < 18 else "Good evening"
        streak, done_today = s.streak(), s.minutes_today() > 0
        tasks = self.t.curator.today()
        left = [x for x in tasks if not x["done"]]
        head = "Ready to learn?"
        if not s.activities():
            head = "Let's begin."
            msg = "I'm Vac. I'll sit with you every day until you pass. Let's start with one small lesson."
        elif done_today and not left:
            head = "All done today."
            msg = "Everything for today is done. I'm proud of you. Rest, or talk with me for fun."
        elif done_today:
            head = "Keep it going."
            msg = "Nice work so far. %d thing%s left today, starting with %s." % (
                len(left), "" if len(left) == 1 else "s", left[0]["title"])
        elif streak >= 2:
            head = "%d days strong." % streak
            msg = "%d days in a row. Let's not break it: %s will take a few minutes." % (streak, left[0]["title"])
        elif h >= 20:
            msg = "It's getting late, but five minutes still counts. Shall we do the check-in together?"
        else:
            msg = "I saved your seat. Today we start with %s." % left[0]["title"]
        return "%s, %s" % (hello, name), head, msg

    def cheer(self, kind, passed=True, score=None, streak=None):
        name = self._name()
        streak = self.t.store.streak() if streak is None else streak
        if kind == "lesson":
            lines = ["Lesson done, %s. That's one more thing you can say out loud." % name,
                     "Got it. I knew you would. On to the next when you're ready.",
                     "Done! Say one of those sentences to someone today."]
        elif kind == "mock" and passed:
            lines = ["YOU PASSED THE MOCK, %s! This is exactly what exam day will feel like." % name]
        elif kind == "mock":
            lines = ["Not a pass yet, and that's fine: now we know precisely what to fix. I've marked the weak "
                     "sections for this week."]
        elif passed:
            lines = ["Passed. You're getting sharper every day, %s." % name,
                     "That's a pass! The work is showing."]
        else:
            lines = ["Below the line today. No drama: the tricky ones come back tomorrow and we get them together."]
        msg = random.choice(lines)
        if streak in (3, 7, 14, 30, 60, 100):
            msg += " And that's a %d-day streak!" % streak
        return msg

    def nudge(self):
        """A reminder if the learner is drifting, else None."""
        s = self.t.store
        if s.minutes_today() > 0:
            return None
        last = s.activities()
        if not last:
            return None
        gap = (date.today() - date.fromisoformat(last[-1]["day"])).days
        if gap >= 3:
            return "I missed you these %d days. No catching up needed: one short lesson and we're back." % gap
        if gap >= 1 and now_hour() >= 18:
            return "Evening check: we haven't practised today. Five minutes?"
        return None


__all__ = ["Team", "SCENARIOS", "SKILLS", "skill_of"]
