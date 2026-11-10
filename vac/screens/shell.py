"""The main shell: five tabs (Home, Learn, Practice, Tests, Progress) and the tab bar."""
import calendar
from datetime import date

from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ColorProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager
from kivy.uix.widget import Widget

from .. import content, theme
from ..agents import SKILLS
from ..ai import run
from ..db import today
from ..ui import (Bar, Btn, Card, Field, H1, H2, H3, Hero, Icon, IconBtn, Over, Page, Sketch, Sub, T, badge, card,
                  chips, col, gap, list_card, pill, row)

Builder.load_string("""
<TabItem>:
    orientation: 'vertical'
    padding: 0, dp(9), 0, dp(7)
    spacing: dp(3)
    canvas.before:
        Color:
            rgba: theme.BLUE_TINT if self.active else theme.CLEAR
        RoundedRectangle:
            pos: self.center_x - dp(28), self.top - dp(39)
            size: dp(56), dp(30)
            radius: [dp(15)]
    Icon:
        name: root.icon
        filled: root.active
        color: theme.BLUE if root.active else theme.GRAY
        font_size: sp(22)
        size_hint: 1, 1
    Label:
        text: root.text
        font_name: 'InterSemi' if root.active else 'InterMedium'
        font_size: sp(10.5)
        color: theme.BLUE if root.active else theme.GRAY
        size_hint_y: None
        height: dp(14)

<TabBar>:
    size_hint_y: None
    height: dp(66)
    padding: dp(6), 0
    canvas.before:
        Color:
            rgba: theme.SHADOW
        BoxShadow:
            pos: self.pos
            size: self.size
            offset: 0, dp(2)
            blur_radius: dp(18)
            border_radius: [dp(22), dp(22), 0, 0]
        Color:
            rgba: theme.WHITE
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(22), dp(22), 0, 0]

<DayCell>:
    font_name: 'InterMedium'
    font_size: sp(14)
    color: self.fg
    size_hint_y: None
    height: dp(40)
    canvas.before:
        Color:
            rgba: self.fill
        Ellipse:
            pos: self.center_x - dp(17), self.center_y - dp(17)
            size: dp(34), dp(34)
        Color:
            rgba: self.ring
        Line:
            circle: self.center_x, self.center_y, dp(17)
            width: dp(1.4)

<LessonRow>:
    size_hint_y: None
    height: dp(46)
    spacing: dp(10)
    opacity: .5 if self.state == 'down' else 1
""")

TABS = [("home", "Home", "house"), ("learn", "Learn", "book-open"), ("practice", "Practice", "chat-circle-dots"),
        ("tests", "Tests", "exam"), ("progress", "Progress", "calendar-blank")]


class TabItem(ButtonBehavior, BoxLayout):
    icon = StringProperty("house")
    text = StringProperty("")
    active = BooleanProperty(False)


class TabBar(BoxLayout):
    pass


class DayCell(Label):
    fill = ColorProperty(theme.CLEAR)
    ring = ColorProperty(theme.CLEAR)
    fg = ColorProperty(theme.INK)


class LessonRow(ButtonBehavior, BoxLayout):
    pass


def app():
    return App.get_running_app()


def stat(icon, value, label, color, tint):
    c = Card()
    c.padding = dp(12)
    c.spacing = dp(4)
    c.add_widget(badge(icon, color, tint, size=34))
    c.add_widget(T(value, 20, "bold"))
    c.add_widget(Sub(label, font_size=sp(12)))
    return c


class Agent(ButtonBehavior, BoxLayout):
    """Round avatar with a name: one member of the team."""

    def __init__(self, icon, name, color, tint, target, **kw):
        super().__init__(orientation="vertical", spacing=dp(6), **kw)
        holder = BoxLayout()
        holder.add_widget(Widget())
        holder.add_widget(badge(icon, color, tint, size=50))
        holder.add_widget(Widget())
        self.add_widget(holder)
        self.add_widget(Label(text=name, font_name="InterMedium", font_size=sp(12), color=theme.INK,
                              size_hint_y=None, height=dp(16)))
        self.bind(on_release=lambda *_: target())
        self.bind(state=lambda _, st: setattr(self, "opacity", .55 if st == "down" else 1))


class Tab(Page):
    """A tab is a Page with no header that rebuilds itself each time it is shown."""

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        self.clear()
        self.build()

    def build(self):
        pass


# ------------------------------------------------------------------------------ Home
class HomeTab(Tab):
    def build(self):
        a = app()
        t, s = a.team, a.store
        hello, head, msg = t.buddy.greeting()
        tasks = t.curator.today()
        gear = IconBtn(icon="gear", bg=theme.WHITE, fg=theme.INK)
        gear.font_size = sp(20)
        gear.size = (dp(40), dp(40))
        gear.bind(on_release=lambda *_: a.go("settings"))
        streak = s.streak()
        self.add(gap(4), row(pill("fire", "%d day%s" % (streak, "" if streak == 1 else "s"), theme.AMBER),
                             pill("clock", "%dm today" % round(s.minutes_today()), theme.BLUE), Widget(), gear,
                             height=40, spacing=8))
        self.add(col(Sub(hello, font_size=sp(15)), H1(head), spacing=0))

        hero = Hero()
        hero.add_widget(row(Icon(name="smiley", filled=True, color=theme.WHITE, font_size=sp(18)),
                            T("VAC · YOUR FRIEND", 12, "semibold", color=[1, 1, 1, .82]), spacing=6))
        hero.add_widget(T(t.buddy.nudge() or msg, 18, "semibold", color=theme.WHITE))
        todo = [x for x in tasks if not x["done"]]
        if todo:
            go = Btn(text="Start: " + todo[0]["title"], kind="white")
            go.height = dp(48)
            go.shorten = True
            go.bind(width=lambda _, w: setattr(go, "text_size", (w - dp(24), None)))
            go.halign = "center"
            go.bind(on_release=lambda *_: self.open(todo[0]))
            hero.add_widget(gap(2))
            hero.add_widget(go)
        self.add(hero)

        self.add(gap(2), Over("Your team"))
        team = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(78))
        for icon, name, color, tint, target in (
                ("compass", "Curator", theme.BLUE, theme.BLUE_TINT, lambda: a.sm.get_screen("main").show("learn")),
                ("chalkboard-teacher", "Teacher", theme.INDIGO, theme.INDIGO_TINT, lambda: a.open_talk("teacher")),
                ("exam", "Examiner", theme.TEAL, theme.TEAL_TINT, lambda: a.sm.get_screen("main").show("tests")),
                ("binoculars", "Scout", theme.AMBER, theme.AMBER_TINT, lambda: a.sm.get_screen("main").show("progress")),
                ("smiley", "Vac", theme.BLUE, theme.BLUE_TINT, lambda: a.open_talk("teacher"))):
            team.add_widget(Agent(icon, name, color, tint, target))
        self.add(team)

        done, total = content.level_progress(t.level, s.done_lessons())
        self.add(gap(2), Over("Today, planned by your Curator"))
        for task in tasks:
            self.add(list_card(
                task["icon"], task["title"], task["sub"], tap=lambda task=task: self.open(task),
                color=theme.TEAL if task["done"] else theme.BLUE,
                tint=theme.TEAL_TINT if task["done"] else theme.BLUE_TINT,
                trailing="check-circle" if task["done"] else "caret-right",
                trailing_color=theme.TEAL if task["done"] else None))

        self.add(gap(2), Over("AI energy today"))
        if a.ai.ready:
            b = a.ai.budget()
            self.add(card(Bar(value=b["fraction"], color=theme.TEAL),
                          Sub("Enough for about %d min of speaking or %d min of guided learning. Resets every day."
                              % (b["speaking_min"], b["learning_min"]))))
        else:
            wake = Btn(text="Add free AI key", kind="soft")
            wake.bind(on_release=lambda *_: a.go("settings"))
            self.add(card(Sub("Lessons, quizzes, mock tests and your calendar work offline. Add a free Groq key to "
                              "switch on live conversation, corrections, pronunciation and the camera."), wake))

        exam = content.EXAMS[content.level_exam(t.level)]
        self.add(gap(2), Over("Your goal"))
        self.add(card(H3(exam["name"]), Sub(t.curator.pace()), Bar(value=done / total if total else 0)))

    def open(self, task):
        a = app()
        kind = task["kind"]
        if kind == "lesson":
            a.open_lesson(task["lesson"], a.team.level)
        elif kind == "scenario":
            a.open_talk("scenario", task["scenario"])
        elif kind == "mock":
            a.open_exam(a.team.level)
        else:
            a.open_test(a.team.examiner.checkin(kind))


# ------------------------------------------------------------------------------ Learn
class LearnTab(Tab):
    shown_level = None

    def build(self):
        a = app()
        t, s = a.team, a.store
        course = t.course
        if self.shown_level is None or not self.shown_level.startswith(course["code"]):
            self.shown_level = t.level["id"]
        level = content.find_level(self.shown_level)
        done = s.done_lessons()

        self.add(gap(6), H1("Learn"), Sub("%s · built on the %s syllabus" % (course["name"], course["exam"])))
        lay, _ = chips([(lv["id"], lv["name"]) for lv in course["levels"]], selected=[level["id"]], group="lv")
        for c in lay.children:
            c.bind(on_release=lambda c: self.pick(c.value))
        self.add(lay)
        d, n = content.level_progress(level, done)
        self.add(card(row(col(H3(level["title"]), Sub("%s · %d of %d lessons" % (level["cefr"], d, n)), spacing=2),
                          spacing=8), Bar(value=d / n if n else 0, color=theme.TEAL)))

        nxt = t.curator.next_lesson() if level is t.level else None
        for u in level["units"]:
            ud = sum(1 for ls in u["lessons"] if ls["id"] in done)
            sk = Sketch(name=u["sketch"], animate=False, size_hint=(None, None), size=(dp(64), dp(64)), stroke=1.1)
            box = card(row(sk, col(H3(u["title"]), Sub(u["summary"]), spacing=2), spacing=12))
            box.add_widget(Bar(value=ud / len(u["lessons"]), color=theme.TEAL))
            for ls in u["lessons"]:
                box.add_widget(self.lesson_row(ls, level, ls["id"] in done, bool(nxt and nxt[1] is ls)))
            self.add(box)

        self.add(gap(2), Over("For you, written by your Curator"))
        for ls in t.curator.custom_lessons():
            self.add(list_card("sparkle", ls["title"], ls["goal"], tap=lambda ls=ls: a.open_lesson(ls, None),
                               color=theme.AMBER, tint=theme.AMBER_TINT))
        self.topic = Field(hint_text="A situation you care about, e.g. ordering at a ramen shop")
        self.make = Btn(text="Write me a lesson", kind="soft")
        self.make.bind(on_release=lambda *_: self.write())
        self.status = Sub("Tell me what you need the language for and I'll build a lesson around it.")
        self.add(card(self.status, self.topic, self.make))

    def lesson_row(self, ls, level, is_done, is_next):
        r = LessonRow()
        r.add_widget(Icon(name="check-circle" if is_done else ("play" if is_next else "book-open"), filled=is_done or is_next,
                          color=theme.TEAL if is_done else (theme.BLUE if is_next else theme.GRAY), font_size=sp(20),
                          size_hint_y=1))
        lab = T(ls["title"], 15, "semibold" if is_next else "regular", color=theme.INK)
        holder = BoxLayout(orientation="vertical")
        holder.add_widget(Widget())
        holder.add_widget(lab)
        holder.add_widget(Widget())
        r.add_widget(holder)
        if ls.get("ai"):
            r.add_widget(Icon(name="sparkle", color=theme.AMBER, font_size=sp(16), size_hint_y=1))
        r.add_widget(Icon(name="caret-right", color=theme.HAIR, font_size=sp(18), size_hint_y=1))
        r.bind(on_release=lambda *_: app().open_lesson(ls, level))
        return r

    def pick(self, level_id):
        self.shown_level = level_id
        self.refresh()

    def write(self):
        a = app()
        topic = self.topic.text.strip()
        if not topic:
            self.status.text = "Type a situation first, like 'talking to my landlord'."
            return
        if not a.ai.ready:
            self.status.text = "Personal lessons need the AI team. Add your free key in Settings."
            return
        self.make.disabled = True
        self.status.text = "Your Curator is writing a lesson about %s..." % topic

        def fail(msg):
            self.make.disabled = False
            self.status.text = msg

        run(lambda: a.team.curator.write_lesson(topic), lambda ls: a.open_lesson(ls, None), fail)


# ------------------------------------------------------------------------------ Practice
class PracticeTab(Tab):
    def build(self):
        a = app()
        self.add(gap(6), H1("Practice"), Sub("Your teacher is here whenever you want to talk, write or show something."))
        self.add(list_card("chalkboard-teacher", "Ask your teacher", "Explanations, examples and corrections",
                           tap=lambda: a.open_talk("teacher")))
        self.add(list_card("pen-nib", "Writing desk", "Write anything and get it corrected line by line",
                           tap=lambda: a.open_talk("writing")))
        self.add(list_card("camera", "Show the camera", "Check your handwriting or learn the word for what you see",
                           tap=lambda: a.go("camera")))
        self.add(list_card("image", "Sketchbook", "Everyday words as drawings: fruit, transport, places",
                           tap=lambda: a.go("sketchbook")))
        self.add(gap(2), Over("Simulations picked by your Scout"))
        mine = set(a.team.profile.get("interests", []))
        for sc in a.team.scout.suggest(12):
            hit = sc["interest"] in mine
            self.add(list_card(sc["icon"], sc["title"], sc["situation"], tap=lambda sc=sc: a.open_talk("scenario", sc),
                               color=theme.AMBER if hit else theme.BLUE,
                               tint=theme.AMBER_TINT if hit else theme.BLUE_TINT))


# ------------------------------------------------------------------------------ Tests
class TestsTab(Tab):
    def build(self):
        a = app()
        t, s = a.team, a.store
        self.add(gap(6), H1("Tests"), Sub("Set and marked by your Examiner, from what you have actually learned."))
        self.add(Over("Check-ins"))
        for kind, every, title, icon in (("daily", 1, "Daily check-in", "list-checks"),
                                         ("weekly", 7, "Weekly test", "calendar-blank"),
                                         ("monthly", 30, "Monthly test", "medal")):
            days, taken = s.days_since_test(kind)
            if taken and days == 0:
                sub, ok = "Done today", True
            elif days >= every or kind == "daily":
                sub, ok = "Ready now", False
            else:
                sub, ok = "Next one in %d day%s (you can also take it now)" % (every - days, "" if every - days == 1 else "s"), False
            self.add(list_card(icon, title, sub, tap=lambda kind=kind: a.open_test(t.examiner.checkin(kind)),
                               color=theme.TEAL if ok else theme.BLUE, tint=theme.TEAL_TINT if ok else theme.BLUE_TINT,
                               trailing="check-circle" if ok else "caret-right", trailing_color=theme.TEAL if ok else None))

        self.add(gap(2), Over("Mock exams · official format"))
        done = s.done_lessons()
        seen = set()
        for lv in t.course["levels"]:
            exam_id = content.level_exam(lv)
            if exam_id in seen:
                continue
            seen.add(exam_id)
            d, n = content.level_progress(lv, done)
            spec = content.EXAMS[exam_id]
            if t.curator.mock_passed(exam_id):
                sub, icon, col_, tint, trail = "Passed. Retake any time.", "seal-check", theme.TEAL, theme.TEAL_TINT, "check-circle"
            elif d >= n:
                sub, icon, col_, tint, trail = "Unlocked. You finished the lessons.", "seal-check", theme.BLUE, theme.BLUE_TINT, "caret-right"
            else:
                sub = "Unlocks after %d more %s lesson%s" % (n - d, lv["name"], "" if n - d == 1 else "s")
                icon, col_, tint, trail = "lock", theme.GRAY, theme.FILL, "caret-right"
            self.add(list_card(icon, spec["name"] + " mock", sub, tap=lambda lv=lv: a.open_exam(lv), color=col_, tint=tint,
                               trailing=trail, trailing_color=theme.TEAL if trail == "check-circle" else None))

        hist = s.tests(limit=6)
        if hist:
            self.add(gap(2), Over("Recent results"))
            box = card()
            for h in hist:
                name = {"daily": "Daily check-in", "weekly": "Weekly test", "monthly": "Monthly test"}.get(
                    h["kind"], content.EXAMS.get(h["exam_id"], {}).get("name", "Mock") + " mock")
                box.add_widget(row(
                    Icon(name="check-circle" if h["passed"] else "x-circle", filled=True,
                         color=theme.TEAL if h["passed"] else theme.AMBER, font_size=sp(20)),
                    col(T(name, 15, "medium"), Sub("%s · %g of %g" % (h["day"], round(h["score"], 1), h["max"])), spacing=1),
                    spacing=10))
            self.add(box)


# ------------------------------------------------------------------------------ Progress
class ProgressTab(Tab):
    ym = None

    def build(self):
        a = app()
        t, s = a.team, a.store
        if self.ym is None:
            self.ym = (date.today().year, date.today().month)
        y, m = self.ym
        self.add(gap(6), H1("Progress"))

        prev, nxt = IconBtn(icon="caret-left", bg=theme.CLEAR), IconBtn(icon="caret-right", bg=theme.CLEAR)
        prev.bind(on_release=lambda *_: self.shift(-1))
        nxt.bind(on_release=lambda *_: self.shift(1))
        title = T(date(y, m, 1).strftime("%B %Y"), 17, "semibold", halign="center")
        th = BoxLayout(orientation="vertical")
        th.add_widget(Widget())
        th.add_widget(title)
        th.add_widget(Widget())
        cal = card(row(prev, th, nxt, height=44))
        grid = GridLayout(cols=7, size_hint_y=None, spacing=(0, dp(2)))
        grid.bind(minimum_height=grid.setter("height"))
        for wd in "MTWTFSS":
            grid.add_widget(Label(text=wd, font_name="InterSemi", font_size=sp(11), color=theme.GRAY, size_hint_y=None,
                                  height=dp(22)))
        days = s.month_days(y, m)
        for week in calendar.Calendar(firstweekday=0).monthdayscalendar(y, m):
            for d in week:
                if not d:
                    grid.add_widget(Widget(size_hint_y=None, height=dp(40)))
                    continue
                iso = date(y, m, d).isoformat()
                cell = DayCell(text=str(d))
                if iso in days:
                    cell.fill, cell.fg = theme.TEAL, theme.WHITE
                if iso == today():
                    cell.ring = theme.BLUE
                    if iso not in days:
                        cell.fg = theme.BLUE
                grid.add_widget(cell)
        cal.add_widget(grid)
        month_min = sum(v["minutes"] for v in days.values())
        cal.add_widget(Sub("%d active day%s · %d minutes this month" % (len(days), "" if len(days) == 1 else "s",
                                                                       round(month_min)), halign="center"))
        self.add(cal)

        done, total = content.level_progress(t.level, s.done_lessons())
        tests = s.tests()
        self.add(row(stat("fire", str(s.streak()), "day streak", theme.AMBER, theme.AMBER_TINT),
                     stat("book-open", str(len(s.done_lessons())), "lessons done", theme.BLUE, theme.BLUE_TINT),
                     stat("seal-check", str(sum(1 for x in tests if x["passed"])), "tests passed", theme.TEAL,
                          theme.TEAL_TINT), spacing=10))

        self.add(gap(2), Over("Skills, measured by your Examiner"))
        skills = t.scout.skills()
        box = card()
        for sk in SKILLS:
            v = skills.get(sk)
            box.add_widget(row(T(sk.capitalize(), 15, "medium"),
                               T("%d%%" % (v * 100) if v is not None else "not tested yet", 14, color=theme.GRAY,
                                 halign="right"), spacing=8))
            box.add_widget(Bar(value=v or 0, color=theme.TEAL if (v or 0) >= .7 else theme.BLUE))
        self.add(box)

        self.add(gap(2), Over("What your Scout noticed"))
        box = card()
        for line in t.scout.insights():
            box.add_widget(row(Icon(name="binoculars", color=theme.BLUE, font_size=sp(18)), T(line, 15), spacing=10))
        self.note = Sub("")
        ask = Btn(text="Ask Scout for today's advice", kind="soft")
        ask.bind(on_release=lambda *_: self.reflect(ask))
        box.add_widget(self.note)
        box.add_widget(ask)
        self.add(box)

    def reflect(self, btn):
        a = app()
        if not a.ai.ready:
            self.note.text = "Scout's personal advice needs the AI team. Add your free key in Settings."
            return
        btn.disabled = True
        self.note.text = "Scout is looking through your week..."

        def done(text):
            self.note.color = theme.INK
            self.note.text = text
            btn.disabled = False

        def fail(msg):
            self.note.text = msg
            btn.disabled = False

        run(a.team.scout.reflect, done, fail)

    def shift(self, delta):
        y, m = self.ym
        m += delta
        if m < 1:
            y, m = y - 1, 12
        elif m > 12:
            y, m = y + 1, 1
        self.ym = (y, m)
        self.refresh()


# ------------------------------------------------------------------------------ Shell
class MainScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical")
        self.tabs = ScreenManager(transition=NoTransition())
        for name, cls in (("home", HomeTab), ("learn", LearnTab), ("practice", PracticeTab), ("tests", TestsTab),
                          ("progress", ProgressTab)):
            self.tabs.add_widget(cls(name=name))
        self.bar = TabBar()
        self.items = {}
        for name, text, icon in TABS:
            it = TabItem(icon=icon, text=text, active=name == "home")
            it.bind(on_release=lambda _, n=name: self.show(n))
            self.items[name] = it
            self.bar.add_widget(it)
        root.add_widget(self.tabs)
        root.add_widget(self.bar)
        self.add_widget(root)

    def show(self, name):
        for n, it in self.items.items():
            it.active = n == name
        if self.tabs.current == name:
            self.tabs.current_screen.refresh()
        else:
            self.tabs.current = name

    def on_pre_enter(self, *_):
        if self.tabs.current_screen:
            self.tabs.current_screen.refresh()
