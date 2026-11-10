"""Lesson screen: sketch, explanation, words with listen/speak, patterns, conversation, then a quiz."""
from kivy.app import App
from kivy.metrics import dp, sp

from .. import content, theme
from ..ai import run
from ..speech import Unavailable, ask_permissions
from ..ui import Btn, H1, H3, IconBtn, Over, Page, Sketch, Sub, T, badge, card, col, gap, row, sketch_card


def app():
    return App.get_running_app()


class LessonScreen(Page):
    lesson = None
    level = None

    def show(self, lesson, level):
        self.lesson, self.level = lesson, level
        self.back = "main"
        self.title = level["title"] if level else "For you"
        self.clear()
        a = app()
        if lesson.get("ai"):
            cached = a.store.cache_get("lesson:" + lesson["id"])
            if cached:
                self.lesson = cached
            else:
                return self.build_outline()
        self.build()
        self.to_top()

    # --- outline lessons are written by the Teacher on first open ----------------
    def build_outline(self):
        a, ls = app(), self.lesson
        self.add(sketch_card("study", 150), H1(ls["title"]), Sub(ls["goal"]))
        self.status = T("", 15)
        self.add(card(row(badge("sparkle", theme.AMBER, theme.AMBER_TINT),
                          col(H3("Written for you"), self.status, spacing=2), spacing=12)))
        if not a.ai.ready:
            self.status.text = ("Lessons above the starter level are written by your Teacher the first time you open "
                                "them, then kept on your phone. Add your free AI key in Settings to unlock them.")
            b = Btn(text="Open Settings")
            b.bind(on_release=lambda *_: a.go("settings"))
            self.footer.add_widget(b)
            return
        self.status.text = "Your Teacher is writing this lesson to the %s syllabus. It takes a few seconds..." % (
            a.team.course["exam"])

        def done(full):
            if self.lesson is ls:
                self.lesson = full
                self.clear()
                self.build()

        def fail(msg):
            self.status.text = msg
            retry = Btn(text="Try again", kind="soft")
            retry.bind(on_release=lambda *_: self.show(ls, self.level))
            self.footer.add_widget(retry)

        run(lambda: a.team.teacher.expand(ls, self.level), done, fail)

    # --- the lesson ---------------------------------------------------------------
    def build(self):
        a, ls = app(), self.lesson
        scene = ls.get("sketch")
        if not scene and self.level:
            found = content.find_lesson(ls["id"])
            scene = found[2]["sketch"] if found else None
        self.add(sketch_card(scene or "study", 170))
        self.add(H1(ls["title"]), Sub(ls["goal"]))
        if ls.get("intro"):
            self.add(card(T(ls["intro"], 16)))

        if ls["items"]:
            self.add(gap(2), Over("Words and phrases · listen, then say it"))
            for it in ls["items"]:
                self.add(self.item_card(it))

        if ls["points"]:
            self.add(gap(2), Over("Patterns"))
            for p in ls["points"]:
                box = card(T(p["p"], 19, "bold", color=theme.BLUE), Sub(p["m"]))
                for ex in p["ex"]:
                    say = IconBtn(icon="speaker-high")
                    say.font_size = sp(18)
                    say.size = (dp(36), dp(36))
                    say.bind(on_release=lambda _, t=ex["t"]: a.say(t))
                    lines = col(T(ex["t"], 17, "medium"), spacing=1)
                    if ex.get("r"):
                        lines.add_widget(Sub(ex["r"]))
                    lines.add_widget(Sub(ex["m"]))
                    box.add_widget(row(lines, say, spacing=8))
                self.add(box)

        if ls["dialogue"]:
            self.add(gap(2), Over("Conversation"))
            box = card()
            for d in ls["dialogue"]:
                lines = col(Sub(d["s"].upper(), font_size=sp(11), weight="semibold", color=theme.BLUE),
                            T(d["t"], 17, "medium"), spacing=1)
                if d.get("r"):
                    lines.add_widget(Sub(d["r"]))
                lines.add_widget(Sub(d["m"]))
                box.add_widget(lines)
            play = Btn(text="Play the conversation", kind="soft")
            play.bind(on_release=lambda *_: a.say("  ".join(d["t"] for d in ls["dialogue"])))
            box.add_widget(play)
            self.add(box)

        go = Btn(text="Practise and finish")
        go.bind(on_release=lambda *_: a.open_test(a.team.examiner.lesson_quiz(ls, self.level)))
        ask = Btn(text="Ask your teacher about this", kind="plain")
        ask.height = dp(36)
        ask.bind(on_release=lambda *_: a.open_talk("teacher", seed="Can you explain '%s' with two more examples?" % ls["title"]))
        self.footer.add_widget(go)
        self.footer.add_widget(ask)

    def item_card(self, it):
        a = app()
        text = col(T(it["t"], 22, "semibold"), spacing=1)
        if it.get("r"):
            text.add_widget(Sub(it["r"]))
        text.add_widget(T(it["m"], 15, color=theme.GRAY))
        heard = Sub("", color=theme.AMBER)
        heard.opacity = 0
        text.add_widget(heard)
        say = IconBtn(icon="speaker-high")
        mic = IconBtn(icon="microphone", bg=theme.FILL, fg=theme.INK)
        say.bind(on_release=lambda *_: a.say(it["t"]))
        mic.bind(on_release=lambda *_: self.try_say(it, mic, heard))
        parts = []
        if it.get("sk"):
            parts.append(Sketch(name=it["sk"], size_hint=(None, None), size=(dp(60), dp(60)), stroke=1.2))
        parts += [text, say, mic]
        c = card(row(*parts, spacing=10))
        c.padding = (dp(14), dp(12))
        return c

    def try_say(self, it, mic, heard):
        """Tap to record, tap again to stop: the speech model's transcript is compared with the target."""
        a = app()

        def note(msg, color=theme.AMBER):
            heard.text, heard.color, heard.opacity = msg, color, 1

        if not a.ai.ready:
            return note("Pronunciation check needs the AI team. Add your free key in Settings.")
        if not a.recorder.recording:
            def start(ok):
                if not ok:
                    return note("I need microphone permission to hear you.")
                try:
                    a.recorder.start()
                except Unavailable as e:
                    return note(str(e))
                mic.bg, mic.fg, mic.name = theme.AMBER, theme.WHITE, "stop"
                note("Listening... tap again when you're done.", theme.GRAY)
            return ask_permissions(start)

        path, secs = a.recorder.stop()
        mic.bg, mic.fg, mic.name = theme.FILL, theme.INK, "microphone"
        note("Checking...", theme.GRAY)

        def done(text):
            score, verdict = a.team.teacher.pronunciation(it["t"], text)
            a.team.record("speak", "speaking", minutes=max(secs, 5) / 60, score=score / 100)
            note("%d%% · heard: %s\n%s" % (score, text or "(nothing)", verdict),
                 theme.TEAL if score >= 90 else theme.AMBER)

        run(lambda: a.ai.transcribe(path, a.team.course["stt"], secs, hint=it["t"]), done, note)
