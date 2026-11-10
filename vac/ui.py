"""Reusable widgets: labels, cards, buttons, chips, inputs, sketches, page scaffold."""
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, InstructionGroup, Line, Mesh
from kivy.graphics.boxshadow import BoxShadow
from kivy.graphics.tesselator import TYPE_POLYGONS, WINDING_ODD, Tesselator
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import (BooleanProperty, ColorProperty, ListProperty, NumericProperty, ObjectProperty,
                             OptionProperty, StringProperty)
from kivy.uix.behaviors import ButtonBehavior, ToggleButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from . import theme
from .content.sketches import OBJECTS, SCENES
from .icons import icon
from .sketch_geo import resolve

Builder.load_string("""
#:import theme vac.theme
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp

<VLabel>:
    color: theme.INK
    font_size: sp(16)
    size_hint_y: None
    text_size: self.width, None
    height: self.texture_size[1]
    line_height: 1.12

<FLabel>:
    color: theme.INK
    font_size: sp(16)
    text_size: self.size
    halign: 'center'
    valign: 'middle'

<Icon>:
    font_name: 'IconsFill' if self.filled else 'Icons'
    font_size: sp(22)
    color: theme.INK
    size_hint: None, None
    size: self.font_size * 1.3, self.font_size * 1.3
    halign: 'center'
    valign: 'middle'
    text_size: self.size

<Card>:
    orientation: 'vertical'
    padding: dp(16)
    spacing: dp(8)
    size_hint_y: None
    height: self.minimum_height
    canvas.before:
        Color:
            rgba: self.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(self.radius)]

<TapCard>:
    canvas.after:
        Color:
            rgba: 0, 0, 0, (.05 if self.state == 'down' else 0)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(self.radius)]

<Hero>:
    padding: dp(20)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: theme.BLUE[:3] + [.30]
        BoxShadow:
            pos: self.pos
            size: self.size
            offset: 0, -dp(8)
            blur_radius: dp(24)
            spread_radius: -dp(10), -dp(10)
            border_radius: [dp(self.radius)] * 4
        Color:
            rgba: 1, 1, 1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(self.radius)]
            texture: theme.gradient(theme.BLUE, theme.INDIGO, True)
        Color:
            rgba: 1, 1, 1, .10
        Ellipse:
            pos: self.right - dp(132), self.center_y - min(dp(60), self.height / 2 - dp(8))
            size: [min(dp(120), self.height - dp(16))] * 2
        Ellipse:
            pos: self.right - dp(92), self.center_y - min(dp(36), self.height / 2 - dp(8))
            size: [min(dp(72), self.height - dp(16))] * 2

<Btn>:
    size_hint_y: None
    height: dp(54)
    font_size: sp(17)
    markup: True
    color: self.fg
    disabled_color: theme.GRAY
    canvas.before:
        Color:
            rgba: (self.glow[:3] + [.32]) if self.tex and not self.disabled else theme.CLEAR
        BoxShadow:
            pos: self.pos
            size: self.size
            offset: 0, -dp(6)
            blur_radius: dp(16)
            spread_radius: -dp(8), -dp(8)
            border_radius: [dp(16)] * 4
        Color:
            rgba: theme.HAIR if self.disabled else (theme.WHITE if self.tex else self.bg)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16)]
            texture: None if self.disabled else self.tex
    canvas.after:
        Color:
            rgba: 0, 0, 0, (.10 if self.state == 'down' else 0)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16)]

<Chip>:
    size_hint: None, None
    height: dp(38)
    width: self.texture_size[0] + dp(28)
    font_size: sp(15)
    markup: True
    color: theme.WHITE if self.state == 'down' else theme.INK
    canvas.before:
        Color:
            rgba: theme.BLUE if self.state == 'down' else theme.WHITE
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(19)]

<IconBtn>:
    size_hint: None, None
    size: dp(44), dp(44)
    opacity: .5 if self.state == 'down' else 1
    canvas.before:
        Color:
            rgba: self.bg
        Ellipse:
            pos: self.pos
            size: self.size

<Field>:
    background_normal: ''
    background_active: ''
    background_color: 0, 0, 0, 0
    foreground_color: theme.INK
    hint_text_color: theme.GRAY
    cursor_color: theme.BLUE
    font_name: 'Noto'
    font_size: sp(16)
    padding: dp(14), dp(13)
    size_hint_y: None
    height: dp(50) if not self.multiline else max(dp(96), self.minimum_height)
    canvas.before:
        Color:
            rgba: theme.FILL
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
        # TextInput draws its text with the last colour set here, so restore it after the fill
        Color:
            rgba: self.disabled_foreground_color if self.disabled else (self.hint_text_color if not self.text else self.foreground_color)

<Bar>:
    size_hint_y: None
    height: dp(8)
    canvas:
        Color:
            rgba: theme.HAIR
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.height / 2]
        Color:
            rgba: self.color
        RoundedRectangle:
            pos: self.pos
            size: max(self.height if self.value > 0 else 0, self.width * min(1, self.value)), self.height
            radius: [self.height / 2]

<Page>:
    canvas.before:
        Color:
            rgba: theme.MIST
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            id: header
            size_hint_y: None
            height: dp(56) if root.title or root.back else 0
            opacity: 1 if root.title or root.back else 0
            padding: dp(8), 0, dp(12), 0
            spacing: dp(4)
            IconBtn:
                name: 'caret-left'
                bg: theme.CLEAR
                fg: theme.BLUE
                opacity: 1 if root.back else 0
                disabled: not root.back
                on_release: root.go_back()
            FLabel:
                text: root.title
                font_name: theme.font_for(self.text, 'semibold')
                font_size: sp(17)
                shorten: True
                shorten_from: 'right'
            BoxLayout:
                id: actions
                size_hint_x: None
                width: dp(44)
        ScrollView:
            id: scroll
            do_scroll_x: False
            bar_width: 0
            BoxLayout:
                id: body
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: dp(20), dp(8), dp(20), dp(28)
                spacing: dp(14)
        BoxLayout:
            id: footer
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            padding: (dp(20), dp(8), dp(20), dp(16)) if self.children else (0, 0, 0, 0)
            spacing: dp(8)
""")


class VLabel(Label):
    """Auto-height wrapping label. Picks Inter or Noto (Japanese) from its text."""
    weight = OptionProperty("regular", options=["regular", "medium", "semibold", "bold"])

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(text=self._font, weight=self._font)
        self._font()

    def _font(self, *_):
        self.font_name = theme.font_for(self.text, self.weight)


class FLabel(Label):
    """Label that fills its box (centred by default)."""


class Icon(Label):
    name = StringProperty("question")
    filled = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(name=self._set)
        self._set()

    def _set(self, *_):
        self.text = icon(self.name)


class Card(BoxLayout):
    bg = ColorProperty(theme.WHITE)
    radius = NumericProperty(22)
    shadow = BooleanProperty(True)

    def __init__(self, **kw):
        super().__init__(**kw)
        self._shadow = None
        self.bind(shadow=self._set_shadow, pos=self._place_shadow, size=self._place_shadow,
                  radius=self._place_shadow)
        self._set_shadow()

    def _set_shadow(self, *_):
        """The soft shadow is costly to create, so only cards that show one carry it."""
        if self.shadow and not self._shadow:
            group = InstructionGroup()
            group.add(Color(*theme.SHADOW))
            self._box = BoxShadow(offset=(0, -dp(4)), blur_radius=dp(20), spread_radius=(-dp(3), -dp(3)))
            group.add(self._box)
            self.canvas.before.insert(0, group)
            self._shadow = group
            self._place_shadow()
        elif not self.shadow and self._shadow:
            self.canvas.before.remove(self._shadow)
            self._shadow = None

    def _place_shadow(self, *_):
        if self._shadow:
            self._box.pos, self._box.size = self.pos, self.size
            self._box.border_radius = [dp(self.radius)] * 4


class Hero(Card):
    """The one gradient card on a screen: blue running into its neighbour, indigo."""


class TapCard(ButtonBehavior, Card):
    pass


class Btn(ButtonBehavior, Label):
    """Primary button: Apple blue fill. kind='soft' is the tinted secondary; 'plain' is text only."""
    bg = ColorProperty(theme.BLUE)
    fg = ColorProperty(theme.WHITE)
    glow = ColorProperty(theme.BLUE)
    tex = ObjectProperty(None, allownone=True)
    kind = OptionProperty("primary", options=["primary", "soft", "plain", "white", "done"])

    def __init__(self, **kw):
        super().__init__(**kw)
        self.font_name = "InterSemi"
        self.bind(kind=self._kind, text=self._font)
        self._kind()
        self._font()

    def _font(self, *_):
        self.font_name = theme.font_for(self.text, "semibold")

    def _kind(self, *_):
        self.bg, self.fg, self.glow, self.tex = {
            "primary": (theme.BLUE, theme.WHITE, theme.BLUE_LO, theme.gradient(theme.BLUE_HI, theme.BLUE_LO)),
            "done": (theme.TEAL, theme.WHITE, theme.TEAL_LO, theme.gradient(theme.TEAL_HI, theme.TEAL_LO)),
            "soft": (theme.BLUE_TINT, theme.BLUE, theme.BLUE, None),
            "white": (theme.WHITE, theme.BLUE, theme.BLUE, None),
            "plain": (theme.CLEAR, theme.BLUE, theme.BLUE, None),
        }[self.kind]


class Chip(ToggleButtonBehavior, Label):
    value = ObjectProperty(None)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(text=self._font)
        self._font()

    def _font(self, *_):
        self.font_name = theme.font_for(self.text, "medium")


class IconBtn(ButtonBehavior, Icon):
    bg = ColorProperty(theme.BLUE_TINT)
    fg = ColorProperty(theme.BLUE)

    def __init__(self, **kw):
        kw.setdefault("name", kw.pop("icon", "question"))
        super().__init__(**kw)
        self.bind(fg=lambda *_: setattr(self, "color", self.fg))
        self.color = self.fg

    def _get_icon(self):
        return self.name

    def _set_icon(self, v):
        self.name = v

    icon = property(_get_icon, _set_icon)


class Field(TextInput):
    def __init__(self, **kw):
        kw.setdefault("multiline", False)
        kw.setdefault("write_tab", False)
        super().__init__(**kw)


class Bar(Widget):
    value = NumericProperty(0)
    color = ColorProperty(theme.BLUE)


class Sketch(Widget):
    """Draws a named sketch stroke by stroke, like a pencil."""
    name = StringProperty("")
    progress = NumericProperty(1.0)
    animate = BooleanProperty(True)
    stroke = NumericProperty(1.6)

    LINES = {"ink": theme.INK, "blue": theme.BLUE, "indigo": theme.INDIGO, "teal": theme.TEAL, "amber": theme.AMBER}
    FILLS = {"blue": theme.mix(theme.BLUE, theme.WHITE, .24), "indigo": theme.mix(theme.INDIGO, theme.WHITE, .24),
             "teal": theme.mix(theme.TEAL, theme.WHITE, .24), "amber": theme.mix(theme.AMBER, theme.WHITE, .24),
             "ink": theme.mix(theme.INK, theme.WHITE, .14), "white": theme.WHITE}

    def __init__(self, **kw):
        super().__init__(**kw)
        self._strokes = []
        self._redraw = Clock.create_trigger(self._draw, -1)  # one draw per frame, however many things change
        self.bind(name=self._load, pos=self._redraw, size=self._redraw, progress=self._redraw)
        self._load()

    def _load(self, *_):
        self._strokes = resolve(self.name, OBJECTS, SCENES)
        Animation.cancel_all(self, "progress")
        if self.animate and self._strokes:
            self.progress = 0
            Animation(progress=1, duration=min(2.2, 0.25 + 0.05 * len(self._strokes)), t="out_quad").start(self)
        else:
            self.progress = 1
            self._redraw()

    def _draw(self, *_):
        self.canvas.clear()
        if not self._strokes:
            return
        side = min(self.width, self.height)
        ox = self.x + (self.width - side) / 2
        oy = self.y + (self.height - side) / 2
        k = side / 100.0
        total = sum(len(p) for p, _, _ in self._strokes)
        budget = int(total * self.progress)
        with self.canvas:
            for pts, line, fill in self._strokes:
                if budget <= 1:
                    break
                n = min(len(pts), budget)
                budget -= n
                flat = []
                for x, y in pts[:n]:
                    flat += [ox + x * k, oy + (100 - y) * k]
                if fill and n == len(pts) and n > 2:  # a shape is filled once its outline is complete
                    tess = Tesselator()
                    tess.add_contour(flat)
                    if tess.tesselate(WINDING_ODD, TYPE_POLYGONS):
                        Color(*self.FILLS[fill])
                        for vertices, indices in tess.meshes:
                            Mesh(vertices=vertices, indices=indices, mode="triangle_fan")
                Color(*self.LINES[line])
                Line(points=flat, width=dp(self.stroke), cap="round", joint="round")


class Page(Screen):
    """Screen scaffold: optional header with back button, scrolling body, sticky footer."""
    title = StringProperty("")
    back = StringProperty("")  # screen name to return to ('' hides the back button)

    @property
    def body(self):
        return self.ids.body

    @property
    def footer(self):
        return self.ids.footer

    def clear(self):
        self.ids.body.clear_widgets()
        self.ids.footer.clear_widgets()
        self.ids.actions.clear_widgets()

    def add(self, *widgets):
        for w in widgets:
            self.ids.body.add_widget(w)
        return widgets[-1] if widgets else None

    def to_top(self):
        Clock.schedule_once(lambda *_: setattr(self.ids.scroll, "scroll_y", 1), 0)

    def to_bottom(self):
        Clock.schedule_once(lambda *_: setattr(self.ids.scroll, "scroll_y", 0), 0.05)

    def go_back(self):
        if self.back and self.manager:
            self.manager.transition.direction = "right"
            self.manager.current = self.back

    def go(self, name):
        self.manager.transition.direction = "left"
        self.manager.current = name


# --- builders ---------------------------------------------------------------

def ic(name, color=None, size=None, fill=False):
    """Inline icon markup for labels/buttons with markup=True."""
    s = "[font=%s]%s[/font]" % ("IconsFill" if fill else "Icons", icon(name))
    if size:
        s = "[size=%d]%s[/size]" % (sp(size), s)
    if color:
        s = "[color=%s]%s[/color]" % (theme.hexs(color), s)
    return s


def esc(text):
    """Escape user/AI text for markup labels."""
    return str(text).replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")


def T(text, size=16, weight="regular", color=None, halign="left", markup=False, **kw):
    kw.setdefault("font_size", sp(size))
    return VLabel(text=str(text), weight=weight, color=color or theme.INK, halign=halign, markup=markup, **kw)


def H1(text, **kw):
    return T(text, 30, "bold", **kw)


def H2(text, **kw):
    return T(text, 21, "bold", **kw)


def H3(text, **kw):
    return T(text, 17, "semibold", **kw)


def Sub(text, **kw):
    kw.setdefault("color", theme.GRAY)
    return T(text, 14, **kw)


def Over(text, color=None):
    """Small uppercase section label."""
    return T(text.upper(), 12, "semibold", color=color or theme.GRAY)


def gap(h=8):
    return Widget(size_hint_y=None, height=dp(h))


def row(*widgets, height=None, spacing=10, **kw):
    b = BoxLayout(orientation="horizontal", spacing=dp(spacing), size_hint_y=None, **kw)
    if height:
        b.height = dp(height)
    else:
        b.bind(minimum_height=b.setter("height"))
    for w in widgets:
        b.add_widget(w)
    return b


def col(*widgets, spacing=6, **kw):
    b = BoxLayout(orientation="vertical", spacing=dp(spacing), size_hint_y=None, **kw)
    b.bind(minimum_height=b.setter("height"))
    for w in widgets:
        b.add_widget(w)
    return b


def card(*widgets, tap=None, bg=None, **kw):
    c = TapCard(**kw) if tap else Card(**kw)
    if bg:
        c.bg = bg
    if tap:
        c.bind(on_release=lambda *_: tap())
    for w in widgets:
        c.add_widget(w)
    return c


def badge(icon_name, color=None, tint=None, size=44, fill=True):
    """Round tinted icon badge."""
    b = IconBtn(icon=icon_name, bg=tint or theme.BLUE_TINT, fg=color or theme.BLUE, filled=fill, disabled=True)
    b.font_size = sp(size * 0.5)
    b.size = (dp(size), dp(size))
    b.disabled_color = color or theme.BLUE
    return b


def list_card(icon_name, title, subtitle="", tap=None, color=None, tint=None, trailing="caret-right",
              trailing_color=None):
    """Icon badge + title/subtitle + chevron, the standard tappable row."""
    text = col(H3(title), spacing=2)
    if subtitle:
        text.add_widget(Sub(subtitle))
    holder = BoxLayout(orientation="vertical")
    holder.add_widget(Widget())
    holder.add_widget(text)
    holder.add_widget(Widget())
    parts = [badge(icon_name, color, tint), holder]
    if trailing:
        t = Icon(name=trailing, color=trailing_color or theme.HAIR, font_size=sp(20), filled=trailing != "caret-right")
        t.size_hint_y = 1
        parts.append(t)
    r = BoxLayout(orientation="horizontal", spacing=dp(12), size_hint_y=None)
    for p in parts:
        r.add_widget(p)
    text.bind(height=lambda _, h: setattr(r, "height", max(dp(44), h)))
    r.height = dp(44)
    c = card(r, tap=tap)
    c.padding = (dp(14), dp(14))
    return c


def chips(options, selected=(), group=None, on_change=None):
    """Wrapping chip row. options: list of (value, label). Returns (layout, get_selected)."""
    from kivy.uix.stacklayout import StackLayout
    lay = StackLayout(size_hint_y=None, spacing=dp(8))
    lay.bind(minimum_height=lay.setter("height"))
    made = []
    for value, label in options:
        c = Chip(text=label, value=value, group=group, state="down" if value in selected else "normal")
        if group:
            c.allow_no_selection = False
        if on_change:
            c.bind(state=lambda *_: on_change())
        lay.add_widget(c)
        made.append(c)

    def get():
        return [c.value for c in made if c.state == "down"]

    return lay, get


def pill(icon_name, text, color=None):
    """Small white capsule with an icon and a value, sized to its content."""
    c = Card(orientation="horizontal", radius=20)
    c.size_hint = (None, None)
    c.height = dp(40)
    c.padding = (dp(12), 0, dp(14), 0)
    c.spacing = dp(6)
    ic_ = Icon(name=icon_name, filled=True, color=color or theme.BLUE, font_size=sp(18))
    ic_.size = (dp(22), dp(40))
    c.add_widget(ic_)
    lab = Label(text=text, font_name="InterSemi", font_size=sp(14), color=theme.INK, size_hint=(None, None),
                height=dp(40))
    lab.bind(texture_size=lambda _, ts: setattr(lab, "width", ts[0]))
    c.add_widget(lab)
    c.bind(minimum_width=c.setter("width"))
    return c


def sketch_card(name, height=170, bg=None):
    c = Card(bg=bg or theme.PANEL, shadow=False)
    c.padding = dp(10)
    c.add_widget(Sketch(name=name, size_hint_y=None, height=dp(height)))
    return c
