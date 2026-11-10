"""Camera, sketchbook, exam information and settings screens."""
import os

from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

from .. import content, theme
from ..ai import CHAT_MODELS, STT_MODEL, VISION_MODEL, run
from ..content.sketches import WORDS, word_for
from ..speech import ask_permissions
from ..ui import (Bar, Btn, Field, H1, H2, H3, Icon, Over, Page, Sketch, Sub, T, TapCard, badge, card, chips, col,
                  gap, row)

Builder.load_string("""
<CamBox>:
    size_hint_y: None
    height: dp(300)
    canvas.before:
        Color:
            rgba: theme.INK
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(20)]
""")


def app():
    return App.get_running_app()


class CamBox(BoxLayout):
    pass


# ------------------------------------------------------------------------------ Camera
class CameraScreen(Page):
    cam = None

    def on_pre_enter(self, *_):
        self.back, self.title = "main", "Camera"
        self.clear()
        self.mode = "write"
        lay, self.get_mode = chips([("write", "Check my writing"), ("name", "What is this?")], selected=["write"],
                                   group="cam", on_change=self.mode_changed)
        self.add(lay)
        self.box = CamBox(padding=dp(4))
        self.add(self.box)
        self.expected = Field(hint_text="What did you write? (optional, helps the check)")
        self.add(self.expected)
        self.out = card(Sub("Hold your notebook or an object in front of the camera and take a picture. Your "
                            "teacher will look at it with you."))
        self.add(self.out)
        snap = Btn(text="Take picture")
        snap.bind(on_release=lambda *_: self.snap())
        pick = Btn(text="Choose a photo instead", kind="plain")
        pick.height = dp(36)
        pick.bind(on_release=lambda *_: self.pick())
        self.footer.add_widget(snap)
        self.footer.add_widget(pick)
        ask_permissions(self.start_camera)

    def mode_changed(self):
        self.mode = (self.get_mode() or ["write"])[0]
        self.expected.opacity = 1 if self.mode == "write" else 0
        self.expected.disabled = self.mode != "write"

    def start_camera(self, ok):
        self.box.clear_widgets()
        self.cam = None
        if ok:
            try:
                from kivy.uix.camera import Camera
                self.cam = Camera(play=True, resolution=(1280, 720), fit_mode="cover")
                self.box.add_widget(self.cam)
                return
            except Exception:
                self.cam = None
        self.box.add_widget(T("No camera available here. Use 'Choose a photo instead'.", 15, color=theme.WHITE,
                              halign="center"))

    def on_leave(self, *_):
        if self.cam:
            self.cam.play = False
        self.box.clear_widgets()
        self.cam = None

    def say(self, *widgets):
        self.out.clear_widgets()
        for w in widgets:
            self.out.add_widget(w)
        self.to_bottom()

    def snap(self):
        if not self.cam or not self.cam.texture:
            return self.say(Sub("The camera isn't running. Choose a photo instead."))
        path = os.path.join(app().user_data_dir, "vac_shot.png")
        self.cam.texture.save(path, flipped=False)
        self.look(path)

    def pick(self):
        try:
            from plyer import filechooser
            filechooser.open_file(filters=[("Images", "*.png", "*.jpg", "*.jpeg")],
                                  on_selection=lambda sel: sel and self.look(sel[0]))
        except Exception as e:
            self.say(Sub("Could not open the photo picker: %s" % e))

    def look(self, path):
        from kivy.clock import mainthread
        a = app()

        @mainthread
        def go():
            if not a.ai.ready:
                return self.say(Sub("Looking at photos needs the AI team. Add your free key in Settings."))
            self.say(Sub("Your teacher is looking..."))
            if self.mode == "write":
                expected = self.expected.text.strip()
                run(lambda: a.team.teacher.check_writing_photo(path, expected), self.wrote,
                    lambda m: self.say(Sub(m, color=theme.AMBER)))
            else:
                run(lambda: a.team.teacher.name_object(path), self.named, lambda m: self.say(Sub(m, color=theme.AMBER)))

        go()

    def wrote(self, out):
        ok = bool(out.get("correct"))
        a = app()
        a.team.record("camera", "writing", minutes=2, score=1.0 if ok else 0.5)
        self.say(row(Icon(name="check-circle" if ok else "lightbulb", filled=True,
                          color=theme.TEAL if ok else theme.AMBER, font_size=sp(24)),
                     col(Sub("I READ", font_size=sp(11), weight="semibold"), T(str(out.get("read", "")), 22, "semibold"),
                         spacing=1), spacing=12),
                 T(str(out.get("feedback", "")), 15))

    def named(self, out):
        a = app()
        word = str(out.get("word", ""))
        a.team.record("camera", "vocabulary", minutes=1)
        hear = Btn(text="Hear it", kind="soft")
        hear.height = dp(44)
        hear.bind(on_release=lambda *_: a.say(word))
        lines = [T(word, 26, "bold")]
        if out.get("reading"):
            lines.append(Sub(str(out["reading"])))
        lines += [T(str(out.get("meaning", "")), 16, color=theme.GRAY), gap(2),
                  T(str(out.get("sentence", "")), 17, "medium"), Sub(str(out.get("sentence_meaning", ""))), hear]
        self.say(*lines)
        a.say(word)


# ------------------------------------------------------------------------------ Sketchbook
class SketchbookScreen(Page):
    def on_pre_enter(self, *_):
        a = app()
        self.back, self.title = "main", "Sketchbook"
        self.clear()
        lang = a.team.lang
        self.add(Sub("Tap a drawing to hear the word in %s." % a.team.course["name"]))
        grid = GridLayout(cols=2, spacing=dp(12), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for name in WORDS:
            text, reading, english = word_for(name, lang)
            c = TapCard(shadow=False)
            c.padding = dp(10)
            c.spacing = dp(2)
            c.add_widget(Sketch(name=name, animate=False, size_hint_y=None, height=dp(96), stroke=1.3))
            c.add_widget(T(text, 18, "semibold", halign="center"))
            c.add_widget(Sub(" · ".join(x for x in (reading, english if lang != "en" else "") if x) or " ",
                             halign="center", font_size=sp(12)))
            c.bind(on_release=lambda c, text=text: self.tap(c, text))
            grid.add_widget(c)
        self.add(grid)
        self.to_top()

    def tap(self, c, text):
        sk = c.children[-1]
        sk.animate = True
        sk._load()
        sk.animate = False
        app().say(text)


# ------------------------------------------------------------------------------ Exam info
class ExamScreen(Page):
    def show(self, level):
        a = app()
        t = a.team
        exam_id = content.level_exam(level)
        spec = content.EXAMS[exam_id]
        self.back, self.title = "main", spec["name"]
        self.clear()
        self.add(H2(spec["name"]), Sub("Run by " + spec["body"]), card(T(spec["can_do"], 15)))

        self.add(gap(2), Over("The real exam"))
        box = card()
        for name, minutes in spec["official"]:
            box.add_widget(row(T(name, 15), T("%d min" % minutes, 15, "semibold", halign="right", size_hint_x=.3),
                               spacing=8))
        self.add(box)

        self.add(gap(2), Over("How you pass"))
        box = card()
        if spec.get("band"):
            box.add_widget(T("Each section gets a band from 0 to 9. Your overall band is the average, rounded to the "
                             "nearest half. Your target: band %g." % t.profile.get("band", 6.0), 15))
        else:
            box.add_widget(T("Overall pass mark: %g of %g." % (spec["pass_total"], spec["total"]), 15, "semibold"))
            for s in spec["score_sections"]:
                box.add_widget(T("%s: 0 to %g%s" % (s["name"], s["max"], (", minimum %g" % s["pass"]) if s["pass"] else ""),
                                 15))
            if any(s["pass"] for s in spec["score_sections"]):
                box.add_widget(Sub("Missing one section minimum is a fail, whatever the total."))
        self.add(box)
        if spec.get("item_types"):
            self.add(gap(2), Over("Question types"))
            box = card()
            for sec, kinds in spec["item_types"].items():
                box.add_widget(col(T(sec, 15, "semibold"), Sub(", ".join(kinds)), spacing=1))
            self.add(box)
        self.add(Sub("Source: %s%s" % (spec["url"], "" if spec["verified"] else
                                       ". Timings for this level were not re-checked when the app was built: confirm "
                                       "them on the official site before you book.")))

        d, n = content.level_progress(level, a.store.done_lessons())
        builtin = content.has_mock(exam_id)
        self.status = Sub("")
        self.start = Btn(text="Start the mock test")
        if d < n:
            self.start.disabled = True
            self.start.text = "Locked: %d lesson%s to go" % (n - d, "" if n - d == 1 else "s")
            self.status.text = "The mock opens when you finish every %s lesson, so it tests what you've learned." % level["name"]
        elif builtin:
            self.status.text = content.MOCKS[exam_id]["note"]
            self.start.bind(on_release=lambda *_: a.open_test(t.examiner.mock(exam_id)))
        else:
            self.status.text = ("Your Examiner writes this mock to the official blueprint the first time, then keeps "
                                "it on your phone. Needs the AI team.")
            self.start.bind(on_release=lambda *_: self.generate(level))
        self.footer.add_widget(self.status)
        self.footer.add_widget(self.start)
        self.to_top()

    def generate(self, level):
        a = app()
        if not a.ai.ready:
            self.status.text = "Add your free AI key in Settings so the Examiner can write this paper."
            return
        self.start.disabled = True
        self.status.text = "Your Examiner is writing the paper. This takes up to a minute..."

        def fail(msg):
            self.start.disabled = False
            self.status.text = msg

        run(lambda: a.team.examiner.generate_mock(level), a.open_test, fail)


# ------------------------------------------------------------------------------ Settings
class SettingsScreen(Page):
    def on_pre_enter(self, *_):
        a = app()
        self.back, self.title = "main", "Settings"
        self.clear()
        p = a.team.profile

        self.add(Over("You"))
        edit = Btn(text="Change language, goal or interests", kind="soft")
        edit.bind(on_release=lambda *_: a.go("onboarding"))
        self.add(card(H3(p.get("name", "friend")),
                      Sub("%s · %s · %d min a day" % (a.team.course["name"], a.team.level["title"], p.get("minutes", 20))),
                      edit))

        self.add(gap(2), Over("AI team"))
        self.key = Field(hint_text="Groq API key (gsk_...)", text=a.store.get("groq_key", ""))
        self.status = Sub("Free key: console.groq.com/keys. It is stored only on this phone.")
        test = Btn(text="Save and test")
        test.bind(on_release=lambda *_: self.save_key(test))
        self.add(card(self.key, self.status, test))
        if a.ai.ready:
            b = a.ai.budget()
            self.add(card(H3("Today's free allowance"), Bar(value=b["fraction"], color=theme.TEAL),
                          Sub("%s of %s tokens left across %d models: about %d min of speaking or %d min of guided "
                              "learning." % (format(b["tokens_left"], ","), format(b["tokens_total"], ","),
                                             len(CHAT_MODELS), b["speaking_min"], b["learning_min"]))))
        self.add(card(H3("Open models in use"),
                      Sub("Teaching and conversation: %s\nListening to you: %s\nCamera: %s\nSpeaking to you: your "
                          "phone's own voices (offline, unlimited)"
                          % (", ".join(m.split("/")[-1] for m in CHAT_MODELS[:2]), STT_MODEL, VISION_MODEL.split("/")[-1]))))

        self.add(gap(2), Over("Voice speed"))
        lay, self.get_rate = chips([(0.7, "Slow"), (0.9, "Normal"), (1.05, "Fast")], selected=[a.speaker.rate],
                                   group="rate", on_change=self.set_rate)
        self.add(lay)

        self.add(gap(2), Over("Data"))
        wipe = Btn(text="Erase all progress", kind="plain")
        wipe.fg = theme.AMBER
        self.confirm = False
        wipe.bind(on_release=lambda *_: self.wipe(wipe))
        self.add(card(Sub("Everything is stored on this device: your profile, progress, test history and chats."), wipe))
        self.to_top()

    def set_rate(self):
        a = app()
        rate = (self.get_rate() or [0.9])[0]
        a.speaker.rate = rate
        a.store.set("rate", rate)

    def save_key(self, btn):
        a = app()
        a.store.set("groq_key", self.key.text.strip())
        if not a.ai.ready:
            self.status.text = "Key removed. The app keeps working offline."
            return
        btn.disabled = True
        self.status.text = "Checking the key with Groq..."

        def done(_):
            btn.disabled = False
            self.status.color = theme.TEAL
            self.status.text = "Connected. Your AI team is awake."

        def fail(msg):
            btn.disabled = False
            self.status.color = theme.AMBER
            self.status.text = msg

        run(a.ai.ping, done, fail)

    def wipe(self, btn):
        a = app()
        if not self.confirm:
            self.confirm = True
            btn.text = "Tap again to erase everything"
            return
        a.store.reset()
        a.go("onboarding")
