"""Game rules for Wildling Quest.

Pure Python with no Kivy imports, so it is easy to test on a computer.
"""
import random

MAP = [
    "##########",
    "#..gggg..#",
    "#.gggggg.#",
    "#..ggg...#",
    "#.....#..#",
    "#H....#.S#",
    "#.gg..#..#",
    "#.gggg...#",
    "#..ggg.g.#",
    "#...WWW..#",
    "#.g.WWW.g#",
    "#ggg.....#",
    "#gggg..gg#",
    "##########",
]
START = (2, 5)
MAX_PARTY = 6
MAX_LEVEL = 50
ORB_PRICE = 15

TYPE_CHART = {
    ("Fire", "Grass"): 2.0, ("Fire", "Water"): 0.5, ("Fire", "Fire"): 0.5, ("Fire", "Rock"): 0.5,
    ("Water", "Fire"): 2.0, ("Water", "Rock"): 2.0, ("Water", "Water"): 0.5, ("Water", "Grass"): 0.5,
    ("Grass", "Water"): 2.0, ("Grass", "Rock"): 2.0, ("Grass", "Fire"): 0.5, ("Grass", "Grass"): 0.5,
    ("Electric", "Water"): 2.0, ("Electric", "Grass"): 0.5, ("Electric", "Electric"): 0.5,
    ("Electric", "Rock"): 0.5,
    ("Rock", "Fire"): 2.0, ("Rock", "Electric"): 2.0, ("Rock", "Grass"): 0.5,
}

# name: (type, power, accuracy)
MOVES = {
    "Tackle": ("Normal", 40, 100),
    "Quick Dash": ("Normal", 40, 100),
    "Body Slam": ("Normal", 70, 85),
    "Ember": ("Fire", 45, 95),
    "Flame Burst": ("Fire", 70, 85),
    "Splash Jet": ("Water", 45, 95),
    "Tidal Crash": ("Water", 70, 85),
    "Leaf Dart": ("Grass", 45, 95),
    "Thorn Lash": ("Grass", 70, 85),
    "Spark": ("Electric", 45, 95),
    "Volt Snap": ("Electric", 70, 85),
    "Rock Toss": ("Rock", 45, 95),
    "Boulder Slam": ("Rock", 70, 85),
}

SPECIES = {
    "Embrik": dict(type="Fire", hp=45, atk=52, df=43, spd=60, color=(0.95, 0.45, 0.2), catch=0.8,
                   learn={1: "Tackle", 3: "Ember", 9: "Flame Burst"}),
    "Drizzlet": dict(type="Water", hp=50, atk=48, df=55, spd=44, color=(0.3, 0.6, 0.95), catch=0.8,
                     learn={1: "Tackle", 3: "Splash Jet", 9: "Tidal Crash"}),
    "Sproutle": dict(type="Grass", hp=55, atk=49, df=52, spd=45, color=(0.4, 0.8, 0.35), catch=0.8,
                     learn={1: "Tackle", 3: "Leaf Dart", 9: "Thorn Lash"}),
    "Zapkit": dict(type="Electric", hp=40, atk=50, df=40, spd=70, color=(0.98, 0.85, 0.25), catch=0.9,
                   learn={1: "Quick Dash", 4: "Spark", 10: "Volt Snap"}),
    "Pebblo": dict(type="Rock", hp=55, atk=60, df=65, spd=25, color=(0.6, 0.55, 0.5), catch=0.8,
                   learn={1: "Tackle", 4: "Rock Toss", 10: "Boulder Slam"}),
    "Fluffum": dict(type="Normal", hp=60, atk=45, df=45, spd=50, color=(0.9, 0.78, 0.85), catch=1.0,
                    learn={1: "Tackle", 5: "Quick Dash", 12: "Body Slam"}),
    "Mossback": dict(type="Grass", hp=70, atk=55, df=70, spd=30, color=(0.3, 0.55, 0.4), catch=0.6,
                     learn={1: "Tackle", 4: "Leaf Dart", 8: "Rock Toss", 12: "Thorn Lash"}),
    "Cinderhog": dict(type="Fire", hp=65, atk=70, df=55, spd=40, color=(0.75, 0.3, 0.25), catch=0.5,
                      learn={1: "Tackle", 3: "Ember", 7: "Body Slam", 12: "Flame Burst"}),
}
STARTERS = ["Embrik", "Drizzlet", "Sproutle"]
WILD_TABLE = [("Embrik", 1.0), ("Drizzlet", 1.0), ("Sproutle", 1.0), ("Zapkit", 1.0),
              ("Pebblo", 1.0), ("Fluffum", 1.3), ("Mossback", 0.5), ("Cinderhog", 0.5)]


def effectiveness(move_type, target_type):
    return TYPE_CHART.get((move_type, target_type), 1.0)


def _stat(base, level, is_hp=False):
    if is_hp:
        return base * 2 * level // 50 + level + 10
    return base * 2 * level // 50 + 5


class Creature:
    def __init__(self, species, level, xp=0, hp=None):
        self.species = species
        self.level = level
        self.xp = xp
        self._recalc()
        self.hp = self.max_hp if hp is None else max(0, min(hp, self.max_hp))

    def _recalc(self):
        s = SPECIES[self.species]
        self.max_hp = _stat(s["hp"], self.level, True)
        self.atk = _stat(s["atk"], self.level)
        self.df = _stat(s["df"], self.level)
        self.spd = _stat(s["spd"], self.level)

    @property
    def name(self):
        return self.species

    @property
    def type(self):
        return SPECIES[self.species]["type"]

    @property
    def color(self):
        return SPECIES[self.species]["color"]

    @property
    def catch(self):
        return SPECIES[self.species]["catch"]

    @property
    def moves(self):
        learn = SPECIES[self.species]["learn"]
        known = [m for lv, m in sorted(learn.items()) if lv <= self.level]
        return known[-4:]

    def xp_needed(self):
        return self.level * 10

    def gain_xp(self, amount):
        msgs = []
        if self.level >= MAX_LEVEL:
            return msgs
        self.xp += amount
        while self.level < MAX_LEVEL and self.xp >= self.xp_needed():
            self.xp -= self.xp_needed()
            self.level += 1
            old_max = self.max_hp
            self._recalc()
            self.hp = min(self.max_hp, self.hp + (self.max_hp - old_max))
            msgs.append(f"{self.name} grew to level {self.level}!")
            new_move = SPECIES[self.species]["learn"].get(self.level)
            if new_move:
                msgs.append(f"{self.name} learned {new_move}!")
        return msgs

    def to_dict(self):
        return {"species": self.species, "level": self.level, "xp": self.xp, "hp": self.hp}

    @classmethod
    def from_dict(cls, d):
        return cls(d["species"], int(d["level"]), int(d.get("xp", 0)), int(d.get("hp", 9999)))


class Game:
    def __init__(self):
        self.party = []
        self.box = []
        self.orbs = 8
        self.coins = 30
        self.x, self.y = START

    @classmethod
    def new(cls, starter):
        g = cls()
        g.party = [Creature(starter, 5)]
        return g

    def heal_all(self):
        for c in self.party:
            c.hp = c.max_hp

    def has_alive(self):
        return any(c.hp > 0 for c in self.party)

    def add_creature(self, creature):
        if len(self.party) < MAX_PARTY:
            self.party.append(creature)
            return "joined your team"
        self.box.append(creature)
        return "was sent to your box"

    def random_encounter(self):
        base = max(c.level for c in self.party)
        level = max(2, min(MAX_LEVEL, base + random.randint(-2, 1)))
        names = [n for n, _ in WILD_TABLE]
        weights = [w for _, w in WILD_TABLE]
        return Creature(random.choices(names, weights)[0], level)

    def to_dict(self):
        return {"party": [c.to_dict() for c in self.party],
                "box": [c.to_dict() for c in self.box],
                "orbs": self.orbs, "coins": self.coins, "x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, d):
        g = cls()
        g.party = [Creature.from_dict(c) for c in d["party"]]
        g.box = [Creature.from_dict(c) for c in d.get("box", [])]
        g.orbs = int(d.get("orbs", 8))
        g.coins = int(d.get("coins", 0))
        g.x, g.y = int(d.get("x", START[0])), int(d.get("y", START[1]))
        if not g.party:
            raise ValueError("empty party")
        if not (0 <= g.y < len(MAP) and 0 <= g.x < len(MAP[0])) or MAP[g.y][g.x] in "#W":
            g.x, g.y = START
        return g


class Battle:
    """One wild encounter. Every action returns a list of log lines."""

    def __init__(self, game, wild):
        if not game.has_alive():
            game.heal_all()
        self.game = game
        self.wild = wild
        self.idx = next(i for i, c in enumerate(game.party) if c.hp > 0)
        self.over = False
        self.result = None  # win, lose, run, caught
        self.need_switch = False
        self.summary = ""

    @property
    def mine(self):
        return self.game.party[self.idx]

    @property
    def wild_label(self):
        return "Wild " + self.wild.name

    def _hit(self, att, dfn, move, att_name, dfn_name):
        mtype, power, acc = MOVES[move]
        lines = [f"{att_name} used {move}!"]
        if random.randint(1, 100) > acc:
            lines.append("But it missed!")
            return lines
        eff = effectiveness(mtype, dfn.type)
        stab = 1.5 if mtype == att.type else 1.0
        base = ((2 * att.level / 5 + 2) * power * att.atk / dfn.df) / 50 + 2
        dmg = max(1, int(base * stab * eff * random.uniform(0.85, 1.0)))
        dfn.hp = max(0, dfn.hp - dmg)
        if eff > 1:
            lines.append("It's super effective!")
        elif eff < 1:
            lines.append("It's not very effective...")
        lines.append(f"{dfn_name} took {dmg} damage.")
        return lines

    def _win(self):
        w = self.wild
        xp = 12 + w.level * 6
        coins = 8 + w.level * 3
        self.game.coins += coins
        lines = [f"{self.wild_label} fainted!", f"{self.mine.name} gained {xp} XP."]
        lines += self.mine.gain_xp(xp)
        lines.append(f"You found {coins} coins.")
        self.over, self.result = True, "win"
        self.summary = f"You won the battle and found {coins} coins."
        return lines

    def _player_fainted(self):
        lines = [f"{self.mine.name} fainted!"]
        if any(c.hp > 0 for c in self.game.party):
            self.need_switch = True
            lines.append("Choose your next partner.")
        else:
            self.game.coins //= 2
            self.game.heal_all()
            self.game.x, self.game.y = START
            self.over, self.result = True, "lose"
            lines.append("You blacked out...")
            self.summary = "You blacked out and woke up at the heal center. You lost half your coins."
        return lines

    def _enemy_turn(self):
        move = random.choice(self.wild.moves)
        lines = self._hit(self.wild, self.mine, move, self.wild_label, self.mine.name)
        if self.mine.hp <= 0:
            lines += self._player_fainted()
        return lines

    def fight(self, move_idx):
        if self.over or self.need_switch:
            return []
        moves = self.mine.moves
        mine_move = moves[move_idx % len(moves)]
        wild_move = random.choice(self.wild.moves)
        me, foe = self.mine, self.wild
        player_first = me.spd > foe.spd or (me.spd == foe.spd and random.random() < 0.5)
        order = ["p", "w"] if player_first else ["w", "p"]
        lines = []
        for who in order:
            if who == "p":
                lines += self._hit(me, foe, mine_move, me.name, self.wild_label)
                if foe.hp <= 0:
                    lines += self._win()
                    break
            else:
                lines += self._hit(foe, me, wild_move, self.wild_label, me.name)
                if me.hp <= 0:
                    lines += self._player_fainted()
                    break
        return lines

    def throw_orb(self):
        if self.over or self.need_switch:
            return []
        if self.game.orbs <= 0:
            return ["You're out of Catch Orbs!"]
        self.game.orbs -= 1
        w = self.wild
        chance = min(0.95, (1.0 - 0.65 * w.hp / w.max_hp) * w.catch * 0.9)
        lines = ["You threw a Catch Orb!"]
        if random.random() < chance:
            where = self.game.add_creature(w)
            lines.append(f"Gotcha! {w.name} {where}.")
            self.over, self.result = True, "caught"
            self.summary = f"You caught {w.name}! It {where}."
            return lines
        lines.append("Oh no! It broke free!")
        return lines + self._enemy_turn()

    def run(self):
        if self.over or self.need_switch:
            return []
        chance = max(0.25, min(0.9, 0.5 + (self.mine.spd - self.wild.spd) / 200))
        if random.random() < chance:
            self.over, self.result = True, "run"
            self.summary = "You got away safely."
            return ["You got away safely!"]
        return ["You couldn't get away!"] + self._enemy_turn()

    def switch(self, idx):
        if self.over:
            return []
        if not (0 <= idx < len(self.game.party)) or self.game.party[idx].hp <= 0:
            return ["That one can't fight!"]
        if idx == self.idx and not self.need_switch:
            return ["That one is already fighting!"]
        forced = self.need_switch
        self.idx = idx
        self.need_switch = False
        lines = [f"Go, {self.mine.name}!"]
        if not forced:
            lines += self._enemy_turn()
        return lines
