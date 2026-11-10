"""First-run setup (and later profile edits): name, language, goal, interests, pace, AI key."""
from kivy.app import App
from kivy.metrics import dp

from .. import content, theme
from ..content.scenarios import GOALS, INTERESTS
from ..db import today
from ..ui import Bar, Btn, Field, H1, H3, Over, Page, Sub, T, card, chips, gap, list_card, sketch_card


def app():
    return App.get_running_app()


BANDS = [5.5, 6.0, 6.5, 7.0, 7.5]
MINUTES = [10, 20, 30, 45, 60]


class OnboardingScreen(Page):
    def on_pre_enter(self, *_):
        p = dict(app().store.profile)
        self.editing = bool(p)
        self.data = {"name": p.get("name", ""), "lang": p.get("lang", "ja"), "goal": p.get("goal", "job"),
                     "interests": list(p.get("interests", [])), "minutes": p.get("minutes", 20),
                     "level": p.get("level", ""), "band": p.get("band", 6.0)}
        self.step = 0
        self.render()

    def render(self):
        self.clear()
        self.back = ""
        self.title = ""
        self.add(gap(10), Bar(value=(self.step + 1) / 5))
        [self.s_welcome, self.s_language, self.s_goal, self.s_interests, self.s_ai][self.step]()
        nxt = Btn(text="Start learning" if self.step == 4 else "Continue")
        nxt.bind(on_release=lambda *_: self.forward())
        self.footer.add_widget(nxt)
        if self.step > 0:
            back = Btn(text="Back", kind="plain")
            back.height = dp(36)
            back.bind(on_release=lambda *_: self.go_step(-1))
            self.footer.add_widget(back)
        self.to_top()

    def go_step(self, d):
        self.step += d
        self.render()

    # --- steps ------------------------------------------------------------------------
    def s_welcome(self):
        self.add(sketch_card("greeting", 190), H1("Hi, I'm Vac."),
                 T("I'm the friend who learns with you: I plan your course, explain things, test you, notice what "
                   "you find hard, and cheer when you get it. The goal is simple: pass your language exam.", 16,
                   color=theme.GRAY))
        self.name_field = Field(hint_text="What should I call you?", text=self.data["name"])
        self.add(self.name_field)

    def s_language(self):
        self.add(H1("What are we learning?"), Sub("Each course follows the official exam syllabus."))
        for code, name, native, exams in content.LANGS:
            on = self.data["lang"] == code
            self.add(list_card("translate", name if name == native else "%s · %s" % (name, native), exams, tap=lambda code=code: self.pick_lang(code),
                               color=theme.WHITE if on else theme.BLUE, tint=theme.BLUE if on else theme.BLUE_TINT,
                               trailing="check-circle" if on else "", trailing_color=theme.BLUE))

    def pick_lang(self, code):
        if code != self.data["lang"]:
            self.data["lang"], self.data["level"] = code, ""
        self.render()

    def s_goal(self):
        c = content.course(self.data["lang"])
        self.add(H1("Why %s?" % c["name"]), Sub("Your Curator plans everything backwards from this."))
        lay, self.get_goal = chips([(g, label) for g, label, _ in GOALS], selected=[self.data["goal"]], group="goal")
        self.add(lay, gap(4), Over("Where do you start?"))
        levels = [(lv["id"], "%s · %s" % (lv["name"], lv["cefr"])) for lv in c["levels"]]
        cur = self.data["level"] if self.data["level"].startswith(self.data["lang"]) else levels[0][0]
        lay, self.get_level = chips(levels, selected=[cur], group="level")
        self.add(lay, Sub("New to the language? Keep the first one."))
        self.get_band = None
        if c["exam"] == "IELTS":
            self.add(gap(4), Over("Target band"))
            lay, self.get_band = chips([(b, "%g" % b) for b in BANDS], selected=[self.data["band"]], group="band")
            self.add(lay)

    def s_interests(self):
        self.add(H1("What do you love?"),
                 Sub("Your Scout uses these to build conversations and exercises you'll actually care about."))
        lay, self.get_interests = chips([(i, label) for i, label, _ in INTERESTS], selected=self.data["interests"])
        self.add(lay, gap(4), Over("Minutes a day"))
        lay, self.get_minutes = chips([(m, "%d min" % m) for m in MINUTES], selected=[self.data["minutes"]], group="min")
        self.add(lay, Sub("Twenty focused minutes a day beats two hours on Sunday."))

    def s_ai(self):
        a = app()
        self.add(H1("Wake up the AI team"),
                 T("VAC runs on open-source models served free by Groq: gpt-oss for teaching and conversation, "
                   "Whisper for listening to you. The free allowance covers well over 30 minutes of speaking and an "
                   "hour of learning every day.", 16, color=theme.GRAY))
        self.key = Field(hint_text="Paste your Groq API key (starts with gsk_)", text=a.store.get("groq_key", ""))
        self.add(card(H3("Free key in one minute"),
                      Sub("1. Open console.groq.com/keys and sign in\n2. Create an API key\n3. Paste it here"),
                      self.key))
        self.add(Sub("You can skip this. Lessons, quizzes, mock tests and the calendar work without it, and you can "
                     "add the key later in Settings. The key stays on this phone."))

    # --- collect and save ------------------------------------------------------------
    def forward(self):
        a, d = app(), self.data
        if self.step == 0:
            d["name"] = self.name_field.text.strip() or "friend"
        elif self.step == 2:
            d["goal"] = (self.get_goal() or ["job"])[0]
            d["level"] = (self.get_level() or [""])[0]
            if self.get_band:
                d["band"] = (self.get_band() or [6.0])[0]
        elif self.step == 3:
            d["interests"] = self.get_interests()
            d["minutes"] = (self.get_minutes() or [20])[0]
        elif self.step == 4:
            if self.key.text.strip():
                a.store.set("groq_key", self.key.text.strip())
            if not d["level"].startswith(d["lang"]):
                d["level"] = content.course(d["lang"])["levels"][0]["id"]
            a.store.set("profile", d)
            if not a.store.get("started"):
                a.store.set("started", today())
            return a.go("main")
        self.step += 1
        self.render()
