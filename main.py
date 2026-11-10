"""VAC: a language-exam coach with a team of AI agents who act like your best friend.

Run on desktop:   python main.py
Build for phone:  buildozer android debug   (see README.md)
"""
import os

from kivy.config import Config
from kivy.utils import platform

if platform not in ("android", "ios"):
    # phone-shaped window for development
    Config.set("graphics", "width", "400")
    Config.set("graphics", "height", "780")
    Config.set("graphics", "resizable", "1")
Config.set("kivy", "exit_on_escape", "0")

from kivy.app import App  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.uix.screenmanager import ScreenManager, SlideTransition  # noqa: E402

from vac import theme  # noqa: E402

theme.register_fonts()

from vac.agents import Team  # noqa: E402
from vac.ai import AI  # noqa: E402
from vac.content import COURSES  # noqa: E402
from vac.db import Store  # noqa: E402
from vac.screens.extras import CameraScreen, ExamScreen, SettingsScreen, SketchbookScreen  # noqa: E402
from vac.screens.lesson import LessonScreen  # noqa: E402
from vac.screens.onboarding import OnboardingScreen  # noqa: E402
from vac.screens.shell import MainScreen  # noqa: E402
from vac.screens.talk import TalkScreen  # noqa: E402
from vac.screens.test import ResultScreen, TestScreen  # noqa: E402
from vac.speech import Recorder, Speaker  # noqa: E402


class VacApp(App):
    title = "VAC"

    def build(self):
        Window.clearcolor = theme.MIST
        Window.softinput_mode = "below_target"
        Window.bind(on_keyboard=self.on_key)
        data = os.environ.get("VAC_DATA_DIR") or self.user_data_dir
        os.makedirs(data, exist_ok=True)
        self.store = Store(os.path.join(data, "vac.db"))
        self.ai = AI(self.store)
        self.team = Team(self.store, self.ai)
        self.speaker = Speaker()
        self.speaker.rate = self.store.get("rate", 0.9)
        self.recorder = Recorder(data)

        sm = ScreenManager(transition=SlideTransition(duration=0.22))
        self.sm = sm
        first = "main" if self.store.profile else "onboarding"
        screens = [OnboardingScreen(name="onboarding"), MainScreen(name="main"), LessonScreen(name="lesson"),
                   TalkScreen(name="talk"), TestScreen(name="test"), ResultScreen(name="result"),
                   CameraScreen(name="camera"), SketchbookScreen(name="sketchbook"), ExamScreen(name="exam"),
                   SettingsScreen(name="settings")]
        screens.sort(key=lambda s: s.name != first)  # the first screen added is the one shown
        for s in screens:
            sm.add_widget(s)
        return sm

    # --- navigation ---------------------------------------------------------------
    def go(self, name, direction="left"):
        self.sm.transition.direction = direction
        self.sm.current = name

    def open_lesson(self, lesson, level):
        self.sm.get_screen("lesson").show(lesson, level)
        self.go("lesson")

    def open_talk(self, mode, scenario=None, seed=""):
        self.sm.get_screen("talk").show(mode, scenario, seed)
        self.go("talk")

    def open_test(self, paper):
        self.sm.get_screen("test").show(paper)
        self.go("test")

    def open_exam(self, level):
        self.sm.get_screen("exam").show(level)
        self.go("exam")

    def show_result(self, paper, results, result):
        self.sm.get_screen("result").show(paper, results, result)
        self.go("result")

    def on_key(self, _window, key, *_):
        if key == 27:  # Android back button / Escape
            screen = self.sm.current_screen
            if getattr(screen, "back", ""):
                screen.go_back()
                return True
            return self.sm.current != "main"
        return False

    # --- voice ----------------------------------------------------------------------
    def say(self, text, lang=None, slow=False):
        """Speak in the course language (or the given course code)."""
        course = COURSES.get(lang) or self.team.course
        self.speaker.say(text, course["tts"], slow)

    def on_pause(self):
        return True

    def on_stop(self):
        self.speaker.stop()


if __name__ == "__main__":
    VacApp().run()
