"""Wildling Quest - a creature-collecting adventure built with Kivy."""
import json
import os
import random

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, Triangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager
from kivy.uix.widget import Widget

import logic

TILE_COLORS = {
    ".": (0.86, 0.79, 0.6),
    "g": (0.33, 0.68, 0.3),
    "#": (0.1, 0.32, 0.15),
    "W": (0.25, 0.5, 0.85),
    "H": (0.86, 0.79, 0.6),
    "S": (0.86, 0.79, 0.6),
}


def left_label(**kw):
    lab = Label(halign="left", valign="middle", **kw)
    lab.bind(size=lambda w, s: setattr(w, "text_size", s))
    return lab


class CreatureView(Widget):
    """Draws a creature as simple shapes based on its type and color."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.species = None
        self.bind(pos=self.redraw, size=self.redraw)

    def set_species(self, species):
        self.species = species
        self.redraw()

    def redraw(self, *_):
        self.canvas.clear()
        if not self.species:
            return
        sp_ = logic.SPECIES[self.species]
        r, g, b = sp_["color"]
        t = sp_["type"]
        cx, cy = self.center
        s = min(self.width, self.height) * 0.4
        with self.canvas:
            # features behind the body
            if t == "Fire":
                Color(1.0, 0.75, 0.15)
                Triangle(points=[cx - s * 0.35, cy + s * 0.7, cx, cy + s * 1.55, cx + s * 0.35, cy + s * 0.7])
                Color(1.0, 0.4, 0.1)
                Triangle(points=[cx - s * 0.2, cy + s * 0.7, cx, cy + s * 1.2, cx + s * 0.2, cy + s * 0.7])
            elif t == "Water":
                Color(r * 0.7, g * 0.8, 1.0)
                Triangle(points=[cx - s * 0.3, cy + s * 0.7, cx, cy + s * 1.5, cx + s * 0.3, cy + s * 0.7])
                Triangle(points=[cx - s * 1.0, cy - s * 0.1, cx - s * 1.5, cy + s * 0.3, cx - s * 1.0, cy + s * 0.4])
            elif t == "Grass":
                Color(0.2, 0.6, 0.2)
                Ellipse(pos=(cx - s * 0.7, cy + s * 0.65), size=(s * 0.6, s * 0.9))
                Ellipse(pos=(cx + s * 0.1, cy + s * 0.65), size=(s * 0.6, s * 0.9))
            elif t == "Electric":
                Color(r, g, b)
                Triangle(points=[cx - s * 0.9, cy + s * 0.4, cx - s * 0.7, cy + s * 1.5, cx - s * 0.2, cy + s * 0.7])
                Triangle(points=[cx + s * 0.9, cy + s * 0.4, cx + s * 0.7, cy + s * 1.5, cx + s * 0.2, cy + s * 0.7])
                Color(0.95, 0.7, 0.1)
                Triangle(points=[cx + s * 0.9, cy - s * 0.2, cx + s * 1.6, cy + s * 0.5, cx + s * 1.0, cy + s * 0.3])
            elif t == "Rock":
                Color(r * 0.7, g * 0.7, b * 0.7)
                for dx in (-0.6, 0.0, 0.6):
                    Ellipse(pos=(cx + s * dx - s * 0.25, cy + s * 0.6), size=(s * 0.5, s * 0.5))
            else:  # Normal
                Color(r, g, b)
                Ellipse(pos=(cx - s * 0.95, cy + s * 0.4), size=(s * 0.6, s * 0.8))
                Ellipse(pos=(cx + s * 0.35, cy + s * 0.4), size=(s * 0.6, s * 0.8))
            # body
            Color(r, g, b)
            Ellipse(pos=(cx - s, cy - s * 0.85), size=(2 * s, 1.7 * s))
            Color(1, 1, 1, 0.28)
            Ellipse(pos=(cx - s * 0.55, cy - s * 0.8), size=(s * 1.1, s * 0.9))
            # eyes
            Color(1, 1, 1)
            Ellipse(pos=(cx - s * 0.6, cy + s * 0.05), size=(s * 0.45, s * 0.5))
            Ellipse(pos=(cx + s * 0.15, cy + s * 0.05), size=(s * 0.45, s * 0.5))
            Color(0.08, 0.08, 0.12)
            Ellipse(pos=(cx - s * 0.45, cy + s * 0.12), size=(s * 0.22, s * 0.3))
            Ellipse(pos=(cx + s * 0.3, cy + s * 0.12), size=(s * 0.22, s * 0.3))
            # smile
            Line(points=[cx - s * 0.25, cy - s * 0.2, cx, cy - s * 0.35, cx + s * 0.25, cy - s * 0.2], width=1.5)


class InfoPanel(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", size_hint_y=None, height=dp(54), **kw)
        self.label = left_label(font_size=sp(15), size_hint_y=0.62)
        self.bar = ProgressBar(max=1, value=1, size_hint_y=0.38)
        self.add_widget(self.label)
        self.add_widget(self.bar)

    def show(self, c, prefix=""):
        self.label.text = f"{prefix}{c.name}  Lv{c.level}  [{c.type}]   HP {c.hp}/{c.max_hp}"
        self.bar.max = max(1, c.max_hp)
        self.bar.value = c.hp


class StartScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self.root_box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        self.add_widget(self.root_box)
        self.build_ui()

    def build_ui(self):
        rb = self.root_box
        rb.clear_widgets()
        rb.add_widget(Label(text="WILDLING QUEST", font_size=sp(30), bold=True, size_hint_y=0.14))
        rb.add_widget(Label(text="Pick your first partner!", font_size=sp(18), size_hint_y=0.08))
        row = BoxLayout(spacing=dp(8), size_hint_y=0.58)
        for name in logic.STARTERS:
            col = BoxLayout(orientation="vertical", spacing=dp(6))
            view = CreatureView()
            view.set_species(name)
            col.add_widget(view)
            btn = Button(text=f"{name}\n{logic.SPECIES[name]['type']}", size_hint_y=None,
                         height=dp(70), font_size=sp(15))
            btn.bind(on_release=lambda _b, n=name: self.app.new_game(n))
            col.add_widget(btn)
            row.add_widget(col)
        rb.add_widget(row)
        if self.app.has_save():
            cont = Button(text="Continue saved game", size_hint_y=None, height=dp(56), font_size=sp(17))
            cont.bind(on_release=lambda *_: self.app.continue_game())
            rb.add_widget(cont)
        rb.add_widget(Label(text="Explore the tall grass, battle, catch, and grow your team.",
                            font_size=sp(13), size_hint_y=None, height=dp(30)))


class WorldView(Widget):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self.bind(pos=self.redraw, size=self.redraw)

    def redraw(self, *_):
        self.canvas.clear()
        game = self.app.game
        if game is None:
            return
        rows, cols = len(logic.MAP), len(logic.MAP[0])
        ts = min(self.width / cols, self.height / rows)
        if ts <= 0:
            return
        ox = self.x + (self.width - ts * cols) / 2
        oy = self.y + (self.height - ts * rows) / 2
        with self.canvas:
            for r, row in enumerate(logic.MAP):
                for c, ch in enumerate(row):
                    px, py = ox + c * ts, oy + (rows - 1 - r) * ts
                    Color(*TILE_COLORS[ch])
                    Rectangle(pos=(px, py), size=(ts, ts))
                    if ch == "g":
                        Color(0.12, 0.45, 0.15)
                        for f in (0.2, 0.5, 0.8):
                            Line(points=[px + ts * f, py + ts * 0.12, px + ts * f, py + ts * 0.6], width=1.4)
                    elif ch == "#":
                        Color(0.07, 0.25, 0.1)
                        Ellipse(pos=(px + ts * 0.08, py + ts * 0.08), size=(ts * 0.84, ts * 0.84))
                    elif ch == "W":
                        Color(0.4, 0.65, 0.95)
                        Line(points=[px + ts * 0.15, py + ts * 0.5, px + ts * 0.85, py + ts * 0.5], width=1.2)
                    elif ch == "H":
                        Color(1, 1, 1)
                        Rectangle(pos=(px + ts * 0.1, py + ts * 0.1), size=(ts * 0.8, ts * 0.8))
                        Color(0.9, 0.2, 0.25)
                        Rectangle(pos=(px + ts * 0.42, py + ts * 0.22), size=(ts * 0.16, ts * 0.56))
                        Rectangle(pos=(px + ts * 0.22, py + ts * 0.42), size=(ts * 0.56, ts * 0.16))
                    elif ch == "S":
                        Color(0.95, 0.78, 0.2)
                        Rectangle(pos=(px + ts * 0.1, py + ts * 0.1), size=(ts * 0.8, ts * 0.8))
                        Color(0.5, 0.3, 0.1)
                        Ellipse(pos=(px + ts * 0.3, py + ts * 0.3), size=(ts * 0.4, ts * 0.4))
            # the player, drawn as the lead creature's color
            lead = game.party[0]
            r, g, b = lead.color
            px, py = ox + game.x * ts, oy + (rows - 1 - game.y) * ts
            Color(0.05, 0.05, 0.1)
            Ellipse(pos=(px + ts * 0.1, py + ts * 0.08), size=(ts * 0.8, ts * 0.84))
            Color(r, g, b)
            Ellipse(pos=(px + ts * 0.16, py + ts * 0.14), size=(ts * 0.68, ts * 0.72))
            Color(1, 1, 1)
            Ellipse(pos=(px + ts * 0.28, py + ts * 0.46), size=(ts * 0.17, ts * 0.2))
            Ellipse(pos=(px + ts * 0.55, py + ts * 0.46), size=(ts * 0.17, ts * 0.2))
            Color(0.05, 0.05, 0.1)
            Ellipse(pos=(px + ts * 0.33, py + ts * 0.5), size=(ts * 0.08, ts * 0.12))
            Ellipse(pos=(px + ts * 0.6, py + ts * 0.5), size=(ts * 0.08, ts * 0.12))


class WorldScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        root = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(4))
        self.hud = left_label(font_size=sp(14), size_hint_y=None, height=dp(38))
        self.view = WorldView(app)
        self.msg = Label(font_size=sp(14), size_hint_y=None, height=dp(34), color=(1, 0.95, 0.6, 1))
        root.add_widget(self.hud)
        root.add_widget(self.view)
        root.add_widget(self.msg)

        controls = BoxLayout(size_hint_y=None, height=dp(170), spacing=dp(10))
        pad = GridLayout(cols=3, spacing=dp(4))
        cells = [None, ("^", 0, -1), None, ("<", -1, 0), None, (">", 1, 0), None, ("v", 0, 1), None]
        for cell in cells:
            if cell is None:
                pad.add_widget(Widget())
            else:
                label, dx, dy = cell
                b = Button(text=label, font_size=sp(24), bold=True)
                b.bind(on_press=lambda _b, dx=dx, dy=dy: self.app.move(dx, dy))
                pad.add_widget(b)
        side = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_x=0.55)
        party = Button(text="Team", font_size=sp(16))
        party.bind(on_release=lambda *_: self.app.open_party())
        save = Button(text="Save", font_size=sp(16))
        save.bind(on_release=lambda *_: self.app.manual_save())
        side.add_widget(party)
        side.add_widget(save)
        controls.add_widget(pad)
        controls.add_widget(side)
        root.add_widget(controls)
        self.add_widget(root)

    def refresh(self):
        g = self.app.game
        if g is None:
            return
        lead = g.party[0]
        self.hud.text = (f"Orbs: {g.orbs}   Coins: {g.coins}\n"
                         f"Lead: {lead.name} Lv{lead.level}  HP {lead.hp}/{lead.max_hp}")
        self.view.redraw()


class BattleScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self.battle = None
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(4))
        self.enemy_info = InfoPanel()
        self.enemy_view = CreatureView(size_hint_y=0.3)
        self.mine_view = CreatureView(size_hint_y=0.3)
        self.mine_info = InfoPanel()
        self.log = left_label(font_size=sp(14), size_hint_y=0.17)
        self.log.valign = "top"
        self.actions = GridLayout(cols=2, spacing=dp(6), size_hint_y=0.25)
        for w in (self.enemy_info, self.enemy_view, self.mine_view, self.mine_info, self.log, self.actions):
            root.add_widget(w)
        self.add_widget(root)

    def start(self, battle):
        self.battle = battle
        self.log.text = f"A wild {battle.wild.name} appeared!"
        self.refresh()
        self.show_main()

    def refresh(self):
        b = self.battle
        self.enemy_info.show(b.wild, "Wild ")
        self.enemy_view.set_species(b.wild.species)
        self.mine_info.show(b.mine)
        self.mine_view.set_species(b.mine.species)

    def _clear(self, cols=2):
        self.actions.clear_widgets()
        self.actions.cols = cols

    def _btn(self, text, cb):
        btn = Button(text=text, font_size=sp(16))
        btn.bind(on_release=lambda *_: cb())
        self.actions.add_widget(btn)

    def show_main(self):
        self._clear()
        self._btn("Fight", self.show_moves)
        self._btn(f"Catch Orb ({self.app.game.orbs})", self.do_orb)
        self._btn("Switch", self.show_switch)
        self._btn("Run", self.do_run)

    def show_moves(self):
        self._clear()
        for i, mv in enumerate(self.battle.mine.moves):
            mtype, power, _acc = logic.MOVES[mv]
            self._btn(f"{mv}\n{mtype}  Pwr {power}", lambda i=i: self.after(self.battle.fight(i)))
        self._btn("Back", self.show_main)

    def show_continue(self):
        self._clear(cols=1)
        self._btn("Continue", self.app.finish_battle)

    def show_switch(self):
        forced = self.battle.need_switch
        self.app.open_party(on_pick=self.do_switch, forced=forced, title="Choose a partner")

    def do_switch(self, idx):
        self.after(self.battle.switch(idx))

    def do_orb(self):
        self.after(self.battle.throw_orb())

    def do_run(self):
        self.after(self.battle.run())

    def after(self, lines):
        if lines:
            self.log.text = "\n".join(lines[-4:])
        self.refresh()
        b = self.battle
        if b.over:
            self.show_continue()
        elif b.need_switch:
            self._clear(cols=1)
            self._btn("Choose next partner", self.show_switch)
            self.show_switch()
        else:
            self.show_main()


class WildlingApp(App):
    title = "Wildling Quest"

    def build(self):
        Window.clearcolor = (0.08, 0.1, 0.14, 1)
        self.game = None
        self.save_path = os.path.join(self.user_data_dir, "wildling_save.json")
        self.sm = ScreenManager(transition=NoTransition())
        self.start_screen = StartScreen(self, name="start")
        self.world = WorldScreen(self, name="world")
        self.battle_screen = BattleScreen(self, name="battle")
        for s in (self.start_screen, self.world, self.battle_screen):
            self.sm.add_widget(s)
        return self.sm

    # ---- saving ----
    def has_save(self):
        return os.path.exists(self.save_path)

    def save(self):
        if self.game is None:
            return
        try:
            with open(self.save_path, "w", encoding="utf-8") as f:
                json.dump(self.game.to_dict(), f)
        except OSError:
            pass

    def manual_save(self):
        self.save()
        self.world.msg.text = "Game saved!"

    def new_game(self, starter):
        self.game = logic.Game.new(starter)
        self.save()
        self.enter_world(f"{starter} is ready for adventure!")

    def continue_game(self):
        try:
            with open(self.save_path, "r", encoding="utf-8") as f:
                self.game = logic.Game.from_dict(json.load(f))
        except (OSError, ValueError, KeyError, TypeError):
            self.start_screen.build_ui()
            return
        self.enter_world("Welcome back!")

    def enter_world(self, message=""):
        self.world.msg.text = message
        self.world.refresh()
        self.sm.current = "world"

    # ---- overworld ----
    def move(self, dx, dy):
        g = self.game
        nx, ny = g.x + dx, g.y + dy
        if not (0 <= ny < len(logic.MAP) and 0 <= nx < len(logic.MAP[0])):
            return
        tile = logic.MAP[ny][nx]
        if tile in "#W":
            return
        g.x, g.y = nx, ny
        self.world.msg.text = ""
        self.world.refresh()
        if tile == "H":
            g.heal_all()
            self.world.msg.text = "Your team was fully healed!"
            self.world.refresh()
            self.save()
        elif tile == "S":
            self.open_shop()
        elif tile == "g" and random.random() < 0.2:
            self.start_battle()

    def start_battle(self):
        battle = logic.Battle(self.game, self.game.random_encounter())
        self.battle_screen.start(battle)
        self.sm.current = "battle"

    def finish_battle(self):
        summary = self.battle_screen.battle.summary
        self.save()
        self.enter_world(summary)

    # ---- popups ----
    def open_party(self, on_pick=None, forced=False, title="Your team"):
        box = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(6))
        pop = Popup(title=title, content=box, size_hint=(0.94, 0.85), auto_dismiss=not forced)
        for i, c in enumerate(self.game.party):
            txt = f"{c.name}  Lv{c.level}  [{c.type}]\nHP {c.hp}/{c.max_hp}"
            if c.hp <= 0:
                txt += "  (fainted)"
            btn = Button(text=txt, font_size=sp(15))
            btn.bind(on_release=lambda _b, i=i: self._pick(pop, i, on_pick))
            box.add_widget(btn)
        hint = "Tap a partner to send it out." if on_pick else "Tap a partner to make it your leader."
        box.add_widget(Label(text=f"{hint}\nBox: {len(self.game.box)} stored", font_size=sp(13),
                             size_hint_y=None, height=dp(44)))
        if not forced:
            close = Button(text="Close", size_hint_y=None, height=dp(48))
            close.bind(on_release=lambda *_: pop.dismiss())
            box.add_widget(close)
        pop.open()

    def _pick(self, pop, idx, on_pick):
        pop.dismiss()
        if on_pick:
            on_pick(idx)
        else:
            self.game.party.insert(0, self.game.party.pop(idx))
            self.world.refresh()

    def open_shop(self):
        g = self.game
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        info = Label(font_size=sp(16))
        buy = Button(text=f"Buy Catch Orb ({logic.ORB_PRICE} coins)", font_size=sp(16))
        close = Button(text="Leave shop", font_size=sp(16))
        pop = Popup(title="Wildling Shop", content=box, size_hint=(0.88, 0.5))

        def refresh_info():
            info.text = f"Coins: {g.coins}     Catch Orbs: {g.orbs}"
            self.world.refresh()

        def do_buy(*_):
            if g.coins >= logic.ORB_PRICE and g.orbs < 99:
                g.coins -= logic.ORB_PRICE
                g.orbs += 1
            refresh_info()

        buy.bind(on_release=do_buy)
        close.bind(on_release=lambda *_: pop.dismiss())
        for w in (info, buy, close):
            box.add_widget(w)
        refresh_info()
        pop.open()


if __name__ == "__main__":
    WildlingApp().run()
