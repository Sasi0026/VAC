"""VAC design tokens.

Colour: one brand hue and its neighbours. Apple blue (hue 211) is the primary; indigo and teal sit
either side of it on the wheel (an analogous trio), and a single soft amber, the complement, is kept
for warmth: streaks and corrections. Text and backgrounds are the same blue pushed towards black
and white, so nothing on screen is a foreign grey.
"""
import os

from kivy.core.text import LabelBase
from kivy.graphics.texture import Texture
from kivy.utils import get_color_from_hex as _hex


def mix(color, other, amount):
    """Blend `color` into `other`: amount 0 gives `other`, 1 gives `color`."""
    return [a * amount + b * (1 - amount) for a, b in zip(color[:3], other[:3])] + [1]


WHITE = [1, 1, 1, 1]
CLEAR = [0, 0, 0, 0]

# --- Palette (five colours) -------------------------------------------------
BLUE = _hex("#007AFF")     # primary: buttons, links, active states
INDIGO = _hex("#5856D6")   # neighbour of blue: depth in gradients, the Teacher
TEAL = _hex("#0FA89B")     # other neighbour: success, completed, streak days
AMBER = _hex("#F2A03D")    # complement, used sparingly: streak flame, corrections
INK = _hex("#1B2438")      # text: blue taken almost to black

# --- Derived ----------------------------------------------------------------
BLUE_HI = _hex("#2F95FF")   # top of the button gradient
BLUE_LO = _hex("#0066E0")   # bottom of the button gradient
TEAL_HI = _hex("#22BDAF")
TEAL_LO = _hex("#0C978B")
MIST = _hex("#F3F5FA")      # app background
GRAY = _hex("#6B7588")      # secondary text
HAIR = _hex("#E3E7EF")      # hairlines, empty tracks
FILL = _hex("#ECEFF5")      # input fields, neutral chips
PANEL = _hex("#EEF4FF")     # illustration panels
SHADOW = INK[:3] + [0.08]
BLUE_TINT = mix(BLUE, WHITE, 0.11)
INDIGO_TINT = mix(INDIGO, WHITE, 0.12)
TEAL_TINT = mix(TEAL, WHITE, 0.13)
AMBER_TINT = mix(AMBER, WHITE, 0.16)


def hexs(color):
    """Colour list -> 'rrggbb' for Kivy markup."""
    return "".join("%02x" % int(round(c * 255)) for c in color[:3])


_gradients = {}


def gradient(start, end, horizontal=False):
    """Cached two-stop gradient texture (top to bottom, or left to right)."""
    key = (tuple(start), tuple(end), horizontal)
    if key not in _gradients:
        n = 64
        stops = [mix(end, start, i / (n - 1)) for i in range(n)]
        if not horizontal:
            stops.reverse()  # texture rows run bottom to top
        data = bytes(int(round(c * 255)) for s in stops for c in s)
        tex = Texture.create(size=(n, 1) if horizontal else (1, n), colorfmt="rgba")
        tex.blit_buffer(data, colorfmt="rgba", bufferfmt="ubyte")
        tex.wrap = "clamp_to_edge"
        # Android drops GL textures when the app is paused: refill on reload
        tex.add_reload_observer(lambda t, d=data: t.blit_buffer(d, colorfmt="rgba", bufferfmt="ubyte"))
        _gradients[key] = tex
    return _gradients[key]


FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")


def register_fonts():
    def f(name):
        return os.path.join(FONTS, name)

    LabelBase.register("Inter", f("Inter-Regular.ttf"), fn_bold=f("Inter-Bold.ttf"))
    LabelBase.register("InterMedium", f("Inter-Medium.ttf"))
    LabelBase.register("InterSemi", f("Inter-SemiBold.ttf"))
    LabelBase.register("InterBold", f("Inter-Bold.ttf"))
    LabelBase.register("Noto", f("NotoSansJP-Regular.otf"), fn_bold=f("NotoSansJP-Bold.otf"))
    LabelBase.register("NotoBold", f("NotoSansJP-Bold.otf"))
    LabelBase.register("Icons", f("Phosphor.ttf"))
    LabelBase.register("IconsFill", f("Phosphor-Fill.ttf"))


def has_cjk(text):
    """True when the text needs the Japanese font (icon private-use glyphs excluded)."""
    for ch in text or "":
        o = ord(ch)
        if o >= 0x2E80 and not 0xE000 <= o <= 0xF8FF:
            return True
    return False


def font_for(text, weight="regular"):
    if has_cjk(text):
        return "NotoBold" if weight in ("semibold", "bold") else "Noto"
    return {"regular": "Inter", "medium": "InterMedium", "semibold": "InterSemi", "bold": "InterBold"}[weight]
