"""Dev tool: drive the app through its screens and save a screenshot of each.

    python tools/shots.py <output folder> [ja|de|en]

Uses a throwaway data folder, so it never touches your real progress.
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
out = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "shots")
lang = sys.argv[2] if len(sys.argv) > 2 else "ja"
sys.argv = sys.argv[:1]
os.makedirs(out, exist_ok=True)
os.environ["VAC_DATA_DIR"] = tempfile.mkdtemp(prefix="vac_shots_")
os.environ.pop("GROQ_API_KEY", None)

import main  # noqa: E402  (first: it sets the window shape before Kivy opens one)

from kivy.clock import Clock  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from vac import content  # noqa: E402
from vac.content.scenarios import scenario  # noqa: E402


def seed(a):
    """A learner a few days in, so the screens have something to show."""
    from datetime import date, timedelta
    s = a.store
    level = content.course(lang)["levels"][0]
    s.set("profile", {"name": "Sasi", "lang": lang, "goal": "job", "interests": ["gaming", "tech"], "minutes": 20,
                      "level": level["id"], "band": 6.5})
    s.set("started", (date.today() - timedelta(days=9)).isoformat())
    lessons = content.lessons_of(level)
    for i, ls in enumerate(lessons[:5]):
        s.complete_lesson(ls["id"], 85)
    for back, kind, skill, minutes, score in [(6, "lesson", "vocabulary", 14, .9), (5, "lesson", "grammar", 12, .7),
                                              (4, "daily", "listening", 6, .6), (3, "talk", "speaking", 9, .75),
                                              (2, "lesson", "vocabulary", 15, .85), (1, "daily", "reading", 7, .8),
                                              (1, "talk", "speaking", 11, .5), (0, "lesson", "writing", 8, .65)]:
        day = (date.today() - timedelta(days=back)).isoformat()
        s._x("INSERT INTO activity (day, ts, kind, skill, minutes, score, detail) VALUES (?,?,?,?,?,?,?)",
             (day, 0, kind, skill, minutes, score, '{"interest": "gaming", "scenario": "voicechat"}'))
    it = lessons[1]["items"][0]
    s.mark(lang, it["t"], it["m"], False)
    s.save_test("daily", "", 75, 100, True)


class Shots(main.VacApp):
    def on_start(self):
        a = self
        seed(a)
        level = a.team.level
        lessons = content.lessons_of(level)
        main_screen = a.sm.get_screen("main")

        def tab(name):
            a.go("main")
            main_screen.show(name)

        def answer_all():
            t = a.sm.get_screen("test")
            for _ in range(len(t.paper["questions"])):
                if t.q["type"] == "mcq":
                    t.pick(t.q["a"])
                t.step() if t.q["type"] == "mcq" else t.finish()
                if a.sm.current != "test":
                    break

        steps = [
            ("onboarding1", lambda: a.go("onboarding")),
            ("onboarding2", lambda: a.sm.get_screen("onboarding").go_step(1)),
            ("onboarding3", lambda: a.sm.get_screen("onboarding").go_step(1)),
            ("onboarding4", lambda: a.sm.get_screen("onboarding").go_step(1)),
            ("onboarding5", lambda: a.sm.get_screen("onboarding").go_step(1)),
            ("home", lambda: tab("home")),
            ("learn", lambda: tab("learn")),
            ("practice", lambda: tab("practice")),
            ("tests", lambda: tab("tests")),
            ("progress", lambda: tab("progress")),
            ("lesson", lambda: a.open_lesson(lessons[9], level)),
            ("lesson_words", lambda: setattr(a.sm.get_screen("lesson").ids.scroll, "scroll_y", 0.55)),
            ("quiz", lambda: a.open_test(a.team.examiner.lesson_quiz(lessons[9], level))),
            ("quiz_answered", lambda: a.sm.get_screen("test").pick(a.sm.get_screen("test").q["a"])),
            ("exam", lambda: a.open_exam(level)),
            ("mock", lambda: a.open_test(a.team.examiner.mock(content.level_exam(level)))),
            ("result", answer_all),
            ("talk", lambda: a.open_talk("scenario", scenario("voicechat"))),
            ("sketchbook", lambda: a.go("sketchbook")),
            ("camera", lambda: a.go("camera")),
            ("settings", lambda: a.go("settings")),
        ]
        state = {"i": 0}

        def run_step(*_):
            i = state["i"]
            if i > 0:
                Window.screenshot(name=os.path.join(out, "%02d_%s.png" % (i, steps[i - 1][0])))
            if i >= len(steps):
                a.stop()
                return False
            steps[i][1]()
            state["i"] += 1

        Clock.schedule_interval(lambda *_: Window.canvas.ask_update(), 0.1)  # keep both GL buffers fresh
        Clock.schedule_interval(run_step, 1.6)


if __name__ == "__main__":
    Shots().run()
