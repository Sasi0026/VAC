"""Test runner and result screen, used for lesson quizzes, check-ins and mock exams."""
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.properties import OptionProperty

from .. import content, theme
from ..ai import run
from ..speech import Unavailable, ask_permissions
from ..ui import Bar, Btn, Field, H1, H2, H3, Hero, Icon, IconBtn, Over, Page, Sub, T, TapCard, VLabel, card, col, gap, row


def app():
    return App.get_running_app()


class Option(TapCard):
    look = OptionProperty("normal", options=["normal", "picked", "right", "wrong"])

    def __init__(self, text, **kw):
        super().__init__(shadow=False, **kw)
        self.padding = (dp(16), dp(14))
        self.label = VLabel(text=text, font_size=sp(17), weight="medium")
        self.add_widget(self.label)
        self.bind(look=self._look)
        self._look()

    def _look(self, *_):
        self.bg, self.label.color = {
            "normal": (theme.WHITE, theme.INK), "picked": (theme.BLUE, theme.WHITE),
            "right": (theme.TEAL, theme.WHITE), "wrong": (theme.AMBER_TINT, theme.INK)}[self.look]


class TestScreen(Page):
    paper = None

    def show(self, paper):
        self.paper, self.i = paper, 0
        self.results = [None] * len(paper["questions"])
        self.instant = paper["kind"] != "mock"   # mocks give no feedback until the end, like the real exam
        self.session = time.time()
        self.back = "main"
        self.title = paper["title"]
        self.deadline = time.time() + paper["minutes"] * 60 if paper.get("minutes") else None
        self._stop_clock()
        if self.deadline:
            self._clock = Clock.schedule_interval(self._tick, 1)
        self.render()

    def _stop_clock(self):
        ev = getattr(self, "_clock", None)
        if ev:
            ev.cancel()
        self._clock = None

    def on_leave(self, *_):
        self._stop_clock()
        a = app()
        a.speaker.stop()
        if a.recorder.recording:
            a.recorder.stop()

    def _tick(self, *_):
        left = int(self.deadline - time.time())
        if left <= 0:
            self._stop_clock()
            return self.finish()
        if getattr(self, "timer", None):
            self.timer.text = "%d:%02d" % divmod(left, 60)
            self.timer.color = theme.AMBER if left < 60 else theme.GRAY

    # --- one question -----------------------------------------------------------------
    def render(self):
        a = app()
        self.clear()
        qs = self.paper["questions"]
        q, n = qs[self.i], len(qs)
        self.q = q
        self.timer = Sub("", halign="right")
        self.add(row(Sub("Question %d of %d" % (self.i + 1, n)), self.timer), Bar(value=self.i / n))
        if self.deadline:
            self._tick()
        if q.get("part"):
            self.add(Over(q["part"], color=theme.BLUE))
        if q.get("sub"):
            self.add(card(T(q["sub"], 17)))
        if q.get("say"):
            play = Btn(text="Play the audio", kind="soft")
            play.bind(on_release=lambda *_: a.say(q["say"], lang=self.paper["lang"]))
            self.add(play)
            Clock.schedule_once(lambda *_, s=self.session, i=self.i: self._autoplay(s, i), 0.5)
        self.add(T(q["q"], 18, "semibold"))

        self.next_btn = Btn(text="Finish" if self.i == n - 1 else "Next")
        self.next_btn.bind(on_release=lambda *_: self.advance())
        getattr(self, "_q_" + q["type"])(q)
        self.footer.add_widget(self.next_btn)
        self.to_top()

    def _autoplay(self, session, i):
        if session == self.session and i == self.i and self.manager and self.manager.current == self.name:
            app().say(self.q["say"], lang=self.paper["lang"])

    def _q_mcq(self, q):
        self.options = []
        self.next_btn.disabled = self.instant
        for idx, text in enumerate(q["o"]):
            o = Option(text)
            o.bind(on_release=lambda _, idx=idx: self.pick(idx))
            self.options.append(o)
            self.add(o)

    def pick(self, idx):
        q = self.q
        if self.instant and self.results[self.i] is not None:
            return
        ok = idx == q["a"]
        self.results[self.i] = {"points": 1 if ok else 0, "max": 1, "answer": q["o"][idx], "right": q["o"][q["a"]]}
        for k, o in enumerate(self.options):
            if self.instant:
                o.look = "right" if k == q["a"] else ("wrong" if k == idx else "normal")
            else:
                o.look = "picked" if k == idx else "normal"
        if self.instant and q.get("item") and not ok:
            self.add(Sub("%s  =  %s" % (q["item"][0], q["item"][1]), color=theme.AMBER))
        self.next_btn.disabled = False

    def _q_text(self, q):
        self.field = Field(hint_text="Type your answer")
        self.add(self.field)
        self.verdict = Sub("")
        self.add(self.verdict)

    def _q_write(self, q):
        self.field = Field(hint_text="Write your answer here", multiline=True)
        self.count = Sub("0 words" + (" · aim for %d+" % q["min_words"] if q.get("min_words") else ""))
        self.field.bind(text=lambda _, t: setattr(self.count, "text", "%d words%s" % (
            len(t.split()), " · aim for %d+" % q["min_words"] if q.get("min_words") else "")))
        self.verdict = Sub("")
        self.add(self.field, self.count, self.verdict)
        self.next_btn.text = "Submit answer"

    def _q_speak(self, q):
        a = app()
        self.mic = IconBtn(icon="microphone", bg=theme.BLUE, fg=theme.WHITE, filled=True)
        self.mic.font_size = sp(28)
        self.mic.size = (dp(64), dp(64))
        self.mic.bind(on_release=lambda *_: self.toggle_mic())
        self.verdict = Sub("Tap the microphone, speak, then tap again. You can also type what you would say."
                           if a.ai.ready else "Voice marking needs the AI team. Type what you would say instead.")
        self.field = Field(hint_text="Your words appear here", multiline=True)
        self.add(row(self.mic, self.verdict, spacing=14), self.field)
        self.next_btn.text = "Submit answer"

    def toggle_mic(self):
        a = app()
        if not a.ai.ready:
            return
        if not a.recorder.recording:
            def start(ok):
                if not ok:
                    self.verdict.text = "I need microphone permission to hear you."
                    return
                try:
                    a.recorder.start()
                except Unavailable as e:
                    self.verdict.text = str(e)
                    return
                self.mic.bg, self.mic.name = theme.AMBER, "stop"
                self.verdict.text = "Recording... tap again when you finish."
            return ask_permissions(start)
        path, secs = a.recorder.stop()
        self.mic.bg, self.mic.name = theme.BLUE, "microphone"
        self.verdict.text = "Transcribing..."
        session, i = self.session, self.i

        def done(text):
            if (session, i) == (self.session, self.i):
                self.field.text = (self.field.text + " " + text).strip()
                self.verdict.text = "Check the transcript, then submit. Record again to add more."
                a.team.record("speak", "", minutes=secs / 60)

        run(lambda: a.ai.transcribe(path, self.paper["lang"], secs), done,
            lambda msg: setattr(self.verdict, "text", msg))

    # --- moving on ------------------------------------------------------------------------
    def advance(self):
        q = self.q
        if q["type"] == "text" and (self.results[self.i] is None or not self.instant):
            ok = app().team.examiner.check_text(q, self.field.text)
            self.results[self.i] = {"points": 1 if ok else 0, "max": 1, "answer": self.field.text.strip(),
                                    "right": q["accept"][0]}
            if self.instant:
                self.verdict.text = "Correct." if ok else "Not quite. Answer: %s" % q["accept"][0]
                self.verdict.color = theme.TEAL if ok else theme.AMBER
                self.field.disabled = True
                return
        if q["type"] in ("write", "speak") and self.results[self.i] is None:
            return self.submit_open(q)
        self.step()

    def step(self):
        if self.i + 1 >= len(self.paper["questions"]):
            return self.finish()
        self.i += 1
        self.render()

    def submit_open(self, q):
        a = app()
        answer = self.field.text.strip()
        if not answer:
            self.results[self.i] = {"points": 0, "max": q["max"], "answer": "", "feedback": "No answer given.",
                                    "better": q.get("model", "")}
            return self.step()
        if not a.ai.ready:
            return self.self_assess(q, answer)
        self.next_btn.disabled = True
        self.field.disabled = True
        self.verdict.text = "Your Examiner is marking this..."
        session, i = self.session, self.i

        def done(g):
            if (session, i) != (self.session, self.i):
                return
            self.results[i] = {"points": g["score"], "max": q["max"], "answer": answer, "feedback": g["feedback"],
                               "better": g["better"] or q.get("model", "")}
            if not self.instant:
                return self.step()
            self.show_feedback(q, self.results[i])

        def fail(msg):
            if (session, i) == (self.session, self.i):
                self.verdict.text = msg + " You can mark this one yourself."
                self.self_assess(q, answer)

        run(lambda: a.team.examiner.grade_open(q, answer), done, fail)

    def show_feedback(self, q, r):
        self.verdict.text = ""
        box = card(H3("%g / %g" % (r["points"], r["max"])), T(r["feedback"], 15))
        if r.get("better"):
            box.add_widget(Sub("A STRONGER ANSWER", font_size=sp(11), weight="semibold", color=theme.BLUE))
            box.add_widget(T(r["better"], 15))
        self.add(box)
        self.next_btn.text = "Finish" if self.i == len(self.paper["questions"]) - 1 else "Next"
        self.next_btn.disabled = False
        self.to_bottom()

    def self_assess(self, q, answer):
        """No AI available: show a model answer and let the learner mark honestly."""
        self.field.disabled = True
        self.next_btn.disabled = True
        box = card(H3("Mark it yourself"))
        if q.get("model"):
            box.add_widget(Sub("MODEL ANSWER", font_size=sp(11), weight="semibold", color=theme.BLUE))
            box.add_widget(T(q["model"], 15))
        box.add_widget(Sub("Did you cover the whole task, and would a native speaker understand it?"))
        for label, frac in (("Nailed it", 1.0), ("Partly", 0.5), ("Not yet", 0.0)):
            b = Btn(text=label, kind="soft")
            b.height = dp(44)
            b.bind(on_release=lambda _, frac=frac: self._assessed(q, answer, frac))
            box.add_widget(b)
        self.add(box)
        self.to_bottom()

    def _assessed(self, q, answer, frac):
        self.results[self.i] = {"points": q["max"] * frac, "max": q["max"], "answer": answer,
                                "feedback": "Self-marked.", "better": q.get("model", "")}
        self.step()

    def finish(self):
        self._stop_clock()
        for k, q in enumerate(self.paper["questions"]):
            if self.results[k] is None:
                self.results[k] = {"points": 0, "max": q.get("max", 1), "answer": "",
                                   "right": q["o"][q["a"]] if q["type"] == "mcq" else q.get("accept", [""])[0]
                                   if q["type"] == "text" else "", "better": q.get("model", "")}
        a = app()
        result = a.team.examiner.mark(self.paper, self.results)
        a.show_result(self.paper, self.results, result)


class ResultScreen(Page):
    def show(self, paper, results, result):
        a = app()
        self.clear()
        self.back = ""
        self.title = paper["title"]
        kind, passed = paper["kind"], result["passed"]
        if result["band"] is not None:
            big = "Band %g" % result["band"]
        elif kind == "mock":
            big = "%g / %g" % (result["total"], result["max"])
        else:
            big = "%d%%" % round(result["total"])
        color = theme.TEAL if passed else theme.AMBER
        self.add(gap(10), row(Icon(name="trophy" if passed else "target", filled=True, color=color, font_size=sp(40)),
                              col(H1(big), Sub(self._verdict(kind, passed, result)), spacing=2), spacing=14))
        hero = Hero()
        hero.add_widget(row(Icon(name="smiley", filled=True, color=theme.WHITE, font_size=sp(24)),
                            T(a.team.buddy.cheer(kind, passed), 16, "medium", color=theme.WHITE), spacing=12))
        self.add(hero)
        if result.get("new_level"):
            self.add(card(H3("Level up"), T("Your Curator has moved you on to %s. New lessons are waiting in Learn."
                                           % result["new_level"]["title"], 15), bg=theme.TEAL_TINT))

        if kind == "mock":
            self.add(gap(2), Over("Sections · estimated from your raw score"))
            box = card()
            for s in result["sections"]:
                need = (" · need %g" % s["pass"]) if s["pass"] else ""
                box.add_widget(row(T(s["name"], 15, "medium"),
                                   T("%g / %g%s" % (s["score"], s["max"], need), 14, halign="right",
                                     color=theme.INK if s["ok"] else theme.AMBER), spacing=8))
                box.add_widget(Bar(value=s["score"] / s["max"] if s["max"] else 0,
                                   color=theme.TEAL if s["ok"] else theme.AMBER))
            self.add(box)
            self.add(Sub("The real test scales scores statistically, so treat this as a guide. Mock questions are "
                         "original practice items in the official format."))

        missed = [(q, r) for q, r in zip(paper["questions"], results) if r["points"] < r["max"]]
        if missed:
            self.add(gap(2), Over("Review · %d to look at" % len(missed)))
            for q, r in missed[:25]:
                box = card()
                if q.get("part"):
                    box.add_widget(Sub(q["part"].upper(), font_size=sp(11), weight="semibold", color=theme.BLUE))
                if q.get("sub") and len(q["sub"]) < 160:
                    box.add_widget(T(q["sub"], 15))
                box.add_widget(T(q["q"] if len(q["q"]) < 220 else q["q"][:217] + "...", 15, "medium"))
                if q["type"] in ("mcq", "text"):
                    box.add_widget(T("Your answer: %s" % (r.get("answer") or "none"), 14, color=theme.AMBER))
                    box.add_widget(T("Correct: %s" % r.get("right", ""), 14, color=theme.TEAL))
                else:
                    box.add_widget(T("%g / %g" % (r["points"], r["max"]), 14, "semibold", color=theme.AMBER))
                    if r.get("feedback"):
                        box.add_widget(T(r["feedback"], 14))
                    if r.get("better"):
                        box.add_widget(Sub(r["better"]))
                self.add(box)

        done = Btn(text="Done")
        done.bind(on_release=lambda *_: a.go("main", "right"))
        if kind == "lesson":
            nxt = a.team.curator.next_lesson()
            found = content.find_lesson(paper.get("lesson_id") or "")
            if passed and nxt:
                b = Btn(text="Next lesson: " + nxt[1]["title"])
                b.bind(on_release=lambda *_: a.open_lesson(nxt[1], a.team.level))
                self.footer.add_widget(b)
                done.kind = "plain"
            elif not passed and found:
                b = Btn(text="Go through the lesson again")
                b.bind(on_release=lambda *_: a.open_lesson(found[3], found[1]))
                self.footer.add_widget(b)
                done.kind = "plain"
        self.footer.add_widget(done)
        self.to_top()

    @staticmethod
    def _verdict(kind, passed, result):
        if kind == "lesson":
            return "Lesson complete" if passed else "70% finishes the lesson. One more go."
        if kind == "mock":
            if result["band"] is not None:
                return ("On target for your goal band" if passed else
                        "Target is band %g" % (result["pass_total"] / len(result["sections"])))
            return ("Pass: you cleared %g and every section minimum" % result["pass_total"] if passed else
                    "Pass mark is %g, with a minimum in every section" % result["pass_total"])
        return "Passed" if passed else "Pass mark is 60%"
