"""Conversation screen: ask the teacher, role-play a scenario, or get writing corrected.
Works by typing or by voice (tap the microphone, speak, tap again)."""
import time

from kivy.app import App
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from .. import theme
from ..ai import run
from ..speech import Unavailable, ask_permissions
from ..ui import Btn, Card, Field, H3, Icon, IconBtn, Page, Sub, T, card, col, row, sketch_card


def app():
    return App.get_running_app()


TITLES = {"teacher": "Your teacher", "writing": "Writing desk"}
HINTS = {"teacher": "Ask anything, in English or in your new language",
         "writing": "Write a few sentences and I'll correct them",
         "scenario": "Type your line, or tap the microphone"}


class TalkScreen(Page):
    mode = "teacher"
    scenario = None
    thread = "teacher"

    def show(self, mode, scenario=None, seed=""):
        a = app()
        self.mode, self.scenario = mode, scenario
        self.back = "main"
        self.title = scenario["title"] if scenario else TITLES[mode]
        self.thread = ("scenario:" + scenario["id"]) if scenario else mode
        self.turns, self.t0, self.done_tasks = 0, time.time(), set()
        self.clear()

        if mode == "scenario":
            a.store.chat_clear(self.thread)  # every rehearsal starts fresh
            self.add(sketch_card(scenario["sketch"], 130))
            self.task_rows = []
            box = card(H3("Your mission"), Sub(scenario["situation"]))
            for task in scenario["tasks"]:
                ic_ = Icon(name="check-circle", color=theme.HAIR, font_size=sp(20))
                self.task_rows.append(ic_)
                box.add_widget(row(ic_, T(task, 15), spacing=10))
            self.add(box)
            opener = scenario["open"][a.team.lang]
            a.store.chat_add(self.thread, "assistant", opener)
            self.bubble(opener, mine=False, speak=True)
            a.say(opener)
        else:
            intro = ("Hi! Ask me why something is said the way it is, or try a sentence and I'll fix it with you."
                     if mode == "teacher" else
                     "Write a message, a diary line or an exam answer. I'll give it back corrected, with the reason "
                     "for each change.")
            self.bubble(intro, mine=False)
            for h in a.store.chat_history(self.thread, 6):
                self.bubble(h["content"], mine=h["role"] == "user")

        if not a.ai.ready:
            b = Btn(text="Add free AI key", kind="soft")
            b.bind(on_release=lambda *_: a.go("settings"))
            self.add(card(Sub("Live conversation needs the AI team. It takes one minute to add your free key."), b))

        self.input = Field(hint_text=HINTS[mode], multiline=mode == "writing")
        self.input.text = seed
        self.send_btn = IconBtn(icon="paper-plane-tilt", bg=theme.BLUE, fg=theme.WHITE, filled=True)
        self.mic = IconBtn(icon="microphone", bg=theme.BLUE_TINT, fg=theme.BLUE, filled=True)
        self.send_btn.bind(on_release=lambda *_: self.send(self.input.text))
        self.mic.bind(on_release=lambda *_: self.toggle_mic())
        if mode != "writing":
            self.input.bind(on_text_validate=lambda *_: self.send(self.input.text))
            self.input.multiline = False
        bar = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None)
        self.input.bind(height=lambda _, h: setattr(bar, "height", max(dp(50), h)))
        bar.height = self.input.height
        bar.add_widget(self.input)
        bar.add_widget(self.mic)
        bar.add_widget(self.send_btn)
        self.footer.add_widget(bar)
        self.to_bottom()

    # --- bubbles --------------------------------------------------------------------
    def bubble(self, text, mine, translation="", fix="", speak=False, pending=False):
        a = app()
        c = Card(bg=theme.BLUE if mine else theme.WHITE, radius=18, shadow=not mine)
        c.padding = (dp(14), dp(10))
        c.spacing = dp(4)
        c.size_hint_x = .84
        main = T(text, 16, color=theme.WHITE if mine else (theme.GRAY if pending else theme.INK))
        c.add_widget(main)
        if translation:
            c.add_widget(Sub(translation))
        if speak:
            say = IconBtn(icon="speaker-high")
            say.font_size = sp(16)
            say.size = (dp(32), dp(32))
            say.bind(on_release=lambda *_: a.say(text))
            c.add_widget(say)
        line = BoxLayout(orientation="horizontal", size_hint_y=None)
        c.bind(height=line.setter("height"))
        if mine:
            line.add_widget(Widget(size_hint_x=.16))
            line.add_widget(c)
        else:
            line.add_widget(c)
            line.add_widget(Widget(size_hint_x=.16))
        self.add(line)
        if fix:
            self.add(card(row(Icon(name="lightbulb", color=theme.AMBER, font_size=sp(18), filled=True), T(fix, 14),
                              spacing=8), bg=theme.AMBER_TINT, shadow=False, radius=14))
        self.to_bottom()
        return line

    # --- sending ----------------------------------------------------------------------
    def send(self, text):
        a = app()
        text = (text or "").strip()
        if not text:
            return
        if not a.ai.ready:
            self.bubble("I can't answer yet: add your free AI key in Settings and I'm all yours.", mine=False)
            return
        self.input.text = ""
        self.bubble(text, mine=True)
        self.turns += 1
        wait = self.bubble("...", mine=False, pending=True)
        self.send_btn.disabled = True

        def done(out):
            self.body.remove_widget(wait)
            self.send_btn.disabled = False
            reply = str(out.get("reply", "")).strip() or "(no reply)"
            fix = str(out.get("fix") or "").strip()
            if self.mode == "writing":
                self.show_corrections(out)
                return
            self.bubble(reply, mine=False, translation=str(out.get("translation") or ""), fix=fix,
                        speak=self.mode == "scenario")
            if self.mode == "scenario":
                a.say(reply)
                for i in out.get("tasks_done") or []:
                    if isinstance(i, int) and 0 <= i < len(self.task_rows):
                        self.done_tasks.add(i)
                        self.task_rows[i].color = theme.TEAL
                        self.task_rows[i].filled = True
                if len(self.done_tasks) == len(self.task_rows) and not getattr(self, "cheered", False):
                    self.cheered = True
                    self.add(card(T("Mission complete. You just handled that in %s. Keep chatting or head back."
                                    % a.team.course["name"], 15, "medium", color=theme.WHITE), bg=theme.TEAL))
                    self.to_bottom()

        def fail(msg):
            self.body.remove_widget(wait)
            self.send_btn.disabled = False
            self.bubble(msg, mine=False, pending=True)

        self.cheered = getattr(self, "cheered", False) if self.turns > 1 else False
        run(lambda: a.team.teacher.reply(self.thread, self.mode, text, self.scenario), done, fail)

    def show_corrections(self, out):
        self.bubble(str(out.get("reply", "")), mine=False)
        box = card(H3("Corrected"), T(str(out.get("corrected", "")), 16))
        for m in (out.get("mistakes") or [])[:5]:
            if isinstance(m, dict):
                box.add_widget(col(T("%s  →  %s" % (m.get("wrong", ""), m.get("right", "")), 15, "medium",
                                     color=theme.AMBER), Sub(str(m.get("why", ""))), spacing=1))
        try:
            score = float(out.get("score", 0))
            box.add_widget(Sub("Score for your level: %g / 10" % score))
            app().team.record("write", "writing", minutes=2, score=max(0, min(1, score / 10)))
        except (TypeError, ValueError):
            pass
        self.add(box)
        self.to_bottom()

    # --- voice ------------------------------------------------------------------------
    def toggle_mic(self):
        a = app()
        if not a.ai.ready:
            return self.bubble("Voice needs the AI team to hear you. Add your free key in Settings.", mine=False)
        if not a.recorder.recording:
            def start(ok):
                if not ok:
                    return self.bubble("I need microphone permission to hear you.", mine=False, pending=True)
                try:
                    a.recorder.start()
                except Unavailable as e:
                    return self.bubble(str(e), mine=False, pending=True)
                a.speaker.stop()
                self.mic.bg, self.mic.fg, self.mic.name = theme.AMBER, theme.WHITE, "stop"
                self.input.hint_text = "Listening... tap the button again to send"
            return ask_permissions(start)

        path, secs = a.recorder.stop()
        self.mic.bg, self.mic.fg, self.mic.name = theme.BLUE_TINT, theme.BLUE, "microphone"
        self.input.hint_text = "Transcribing..."

        def done(text):
            self.input.hint_text = HINTS[self.mode]
            if text:
                self.send(text)
            else:
                self.bubble("I couldn't hear that. Try once more, a little closer to the phone.", mine=False, pending=True)

        def fail(msg):
            self.input.hint_text = HINTS[self.mode]
            self.bubble(msg, mine=False, pending=True)

        lang = a.team.course["stt"] if self.mode != "teacher" else None
        run(lambda: a.ai.transcribe(path, lang or a.team.course["stt"], secs), done, fail)

    # --- leaving: log the time for the calendar and the Scout -----------------------------
    def on_leave(self, *_):
        a = app()
        if a.recorder.recording:
            a.recorder.stop()
        a.speaker.stop()
        if not getattr(self, "turns", 0):
            return
        minutes = min(60, (time.time() - self.t0) / 60)
        if self.mode == "scenario":
            done = len(self.done_tasks) / max(1, len(self.task_rows))
            a.team.record("talk", "speaking", minutes, score=done,
                          detail={"scenario": self.scenario["id"], "interest": self.scenario["interest"]})
        elif self.mode == "teacher":
            a.team.record("chat", "", minutes)
        self.turns = 0
