#!/usr/bin/env python3
"""Game & Watch Super Mario Bros. YM-105. LCD art from gnw_smb.svg."""

import os
from io import BytesIO

import numpy as np
import pygame

try:
    import cairosvg
    from lxml import etree
except ImportError:
    print("Need: sudo apt install python3-cairosvg python3-lxml")
    raise SystemExit(1)

pygame.init()
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    AUDIO = True
except pygame.error:
    AUDIO = False

WIDTH, HEIGHT = 1000, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("G&W SMB — arrows move, space jumps")
clock = pygame.time.Clock()
FPS = 60

BG = (185, 195, 168)
INK = (20, 20, 20)
font = pygame.font.SysFont("monospace", 16, bold=True)

# Rows: 0 top, 1 middle, 2 bottom. Six columns across the glass.
PLAT = {
    0: ["1.0.1", "2.0.1", "1.13.3", "1.11.1", "0.10.1", "1.8.1"],
    1: ["1.0.2", "2.0.2", "0.14.2", "0.12.2", "0.10.2", "1.8.2"],
    2: ["1.0.0", "1.15.0", "0.14.0", "0.12.0", "0.10.0", "1.8.0"],
}
MARIO = {
    0: ["0.0.1", "0.1.1", "1.14.3", "1.11.3", "0.10.3", "0.7.1"],
    1: ["0.0.2", "0.1.2", "1.14.1", "1.12.1", "1.10.2", "0.7.2"],
    2: ["0.0.0", "1.1.0", "1.14.2", "0.13.2", "0.11.0", "0.7.0"],
}
# Vertical step on the right edge of columns 0..4.
# 0 sits between the top and the middle. 1 sits between the middle and the ground.
WALL = {
    0: ["2.1.2", "0.15.1", "0.13.1", "0.11.2", "0.9.1"],
    1: ["2.1.0", "0.15.2", "1.13.2", "1.11.0", "0.9.2"],
}
# The tall piece above the top row. Together with wall 0 it makes the high barrier.
ABOVE = ["2.1.1", "0.15.3", "1.12.3", "1.10.3", "0.9.3"]
PEACH = "0.8.1"
LIVES = ("0.2.3", "0.2.0", "0.2.1")
# The splash figures along the bottom edge, left to right.
DROWN = ("0.15.0", "0.13.0", "1.9.0", "0.9.0")


def add_finale(add):
    """Last stretch, shared by both levels. Peach is at distance 0."""
    add(6)
    add(2, n=2)
    add(3)
    add(1)
    add(3)
    add(2)
    add(6)
    add(6)
    add(2)
    add(3)
    add(1, n=4)


def build_level():
    """Opening matches the first photo. Every column has a floor — no pit to jump across.
    The path changes height the whole way. Only the last few columns are the top."""
    cols = []

    def add(mask, wall=None, n=1):
        for _ in range(n):
            cols.append((mask, wall))

    # First screen: left ledge, step, then the ground. The ground keeps going
    # so the empty space on the right of the photo is not a pit.
    add(2)
    add(2, wall=1)
    add(4, n=4)
    # Up to the middle, back down.
    add(6)
    add(2, n=3)
    add(6)
    add(4, n=4)
    # Up to the top for a short stretch, then all the way back down.
    add(6)
    add(2)
    add(3)
    add(1, n=2)
    add(3)
    add(2)
    add(6)
    add(4, n=4)
    # Middle road, then the ground again.
    add(6)
    add(2, n=4)
    add(6)
    add(4, n=4)
    add(6)
    add(2, n=2)
    add(6)
    add(4, n=3)
    # Touch the top once more, then come back down. Not the ending.
    add(2, n=2)
    add(3)
    add(1)
    add(3)
    add(2, n=2)
    add(6)
    add(4, n=4)
    add(6)
    add(2, n=3)
    add(6)
    add(4, n=3)
    add_finale(add)
    return cols


def build_level_2():
    """Same length as level 1. Low walls block the ground, high walls block the middle.
    Jump, then move, to get over them."""
    cols = []

    def add(mask, wall=None, n=1):
        for _ in range(n):
            cols.append((mask, wall))

    add(4, n=4)
    add(4, wall=1)
    add(2, n=3)
    add(6)
    add(4, n=3)
    add(4, wall=1)
    add(2, wall=0)
    add(1, n=2)
    add(3)
    add(2)
    add(6)
    add(4)
    # Around distance 50 this is on screen: ground, a wall, a higher road,
    # then another wall up to the top.
    add(4, wall=1)
    add(2, n=2)
    add(4, wall=1)
    add(2, wall=0)
    add(3)
    add(2)
    add(6)
    add(4, n=4)
    add(4, wall=1)
    add(2, n=2)
    add(2, wall=0)
    add(1, n=2)
    add(3)
    add(2)
    add(6)
    add(4, n=3)
    add(4, wall=1)
    add(6)
    add(2, wall=0)
    add(1)
    add(3)
    add(2, n=2)
    add(6)
    add(4, n=4)
    add(4, wall=1)
    add(2, n=2)
    add(6)
    add(4, n=4)
    add_finale(add)
    return cols


def build_level_3():
    """Opens like level 2. Then the path from the two middle screenshots, repeated.
    A high wall is only passable on the ground. To climb back up: jump left, then up-right."""
    cols = []

    def add(mask, wall=None, n=1):
        for _ in range(n):
            cols.append((mask, wall))

    # First screen, same as level 2.
    add(4, n=4)
    add(4, wall=1)
    add(2)
    # One pass of the photographed obstacle. Walls are on the right edge.
    # mid, ground, mid+ground, top+ground, mid, top+ground, mid+ground, ground, mid
    pattern = (
        (2, 1),
        (4, 0),
        (6, None),
        (5, 0),
        (2, 1),
        (5, 0),
        (6, (0, 2)),
        (4, None),
        (2, None),
    )
    for _ in range(6):
        for mask, wall in pattern:
            add(mask, wall)
    add(2)
    add(6)
    add(2)
    add(6)
    add_finale(add)
    return cols


def build_level_7():
    """Twice as long. Opens like level 1, uses the level 3 obstacles, returns
    to level 1, then a new rising-and-falling road. The last steps are three
    on the ground, three on the middle, then Peach."""
    cols = []

    def add(mask, wall=None, n=1):
        for _ in range(n):
            cols.append((mask, wall))

    # The opening of level 1, through the first drop back to the ground.
    add(2)
    add(2, wall=1)
    add(4, n=4)
    add(6)
    add(2, n=3)
    add(6)
    add(4, n=4)
    add(6)
    add(2)
    add(3)
    add(1, n=2)
    add(3)
    add(2)
    add(6)
    add(4, n=4)
    pattern = (
        (2, 1),
        (4, 0),
        (6, None),
        (5, 0),
        (2, 1),
        (5, 0),
        (6, (0, 2)),
        (4, None),
        (2, None),
    )
    for _ in range(4):
        for mask, wall in pattern:
            add(mask, wall)
    # A stretch of the level 1 road again.
    add(6)
    add(2, n=4)
    add(6)
    add(4, n=4)
    add(6)
    add(2, n=2)
    add(6)
    add(4, n=3)
    # New road: up to the top, down again, and a low wall that has to be jumped.
    add(4, n=4)

    def ribbon():
        add(4)
        add(4)
        add(2)
        add(2)
        add(1)
        add(1)
        add(2)
        add(4)
        add(4, wall=1)
        add(2)
        add(6)

    for _ in range(5):
        ribbon()
    add(4, n=3)
    add(2, n=3)
    add(1)
    return cols


def build_level_8():
    """A one-second course. The road bounces, a ceiling hides a high road,
    two walls close the lane you're standing in, and one tall wall has to be
    ducked. Every column has a floor."""
    cols = []

    def add(mask, wall=None, n=1):
        for _ in range(n):
            cols.append((mask, wall))

    # Bounce: ground, middle, top, and back down. Then the same idea again.
    add(4, n=2)
    add(2, n=2)
    add(4, n=2)
    add(2, n=2)
    add(1, n=2)
    add(2, n=2)
    add(4, n=2)
    add(2, n=2)
    # Step onto this middle floor and jump, or walk under the ceiling.
    add(3, n=4)
    add(2, n=2)
    add(4, n=2)
    # The lane closes. Leave it before the wall, then come back down.
    add(4, wall=1)
    add(2, n=2)
    add(2, wall=0)
    add(1, n=2)
    add(2)
    add(4)
    add(4, wall=1)
    add(2)
    add(1)
    add(2)
    # One tall wall. The way through is along the ground, then back up.
    for mask, wall in (
        (2, 1),
        (4, 0),
        (6, None),
        (5, 0),
        (2, 1),
        (5, 0),
        (6, (0, 2)),
        (4, None),
        (2, None),
    ):
        add(mask, wall)
    # Hopscotch. Each step changes floor.
    add(4)
    add(2)
    add(4)
    add(2)
    add(4)
    add(2)
    add(4)
    add(2)
    add(4, n=2)
    add(2, n=2)
    add(1, n=3)
    add(2)
    add(6)
    add(4, n=2)
    add_finale(add)
    return cols


def build_level_9():
    """Fences. Every vertical line is met on the ground or the middle,
    jumped, and the landing is the ground again."""
    cols = []

    def add(mask, wall=None, n=1):
        for _ in range(n):
            cols.append((mask, wall))

    def low():
        add(4, wall=1)
        add(4)

    def mid():
        add(2, wall=0)
        add(4)

    add(4, n=3)
    low()
    low()
    low()
    add(4, n=2)
    mid()
    add(4, n=2)
    low()
    mid()
    low()
    mid()
    add(4, n=2)
    add(2)
    mid()
    low()
    low()
    add(4, n=2)
    mid()
    add(4)
    mid()
    add(4)
    mid()
    add(4, n=2)
    low()
    low()
    low()
    low()
    add(4, n=2)
    add(2)
    mid()
    low()
    add(4, n=5)
    add_finale(add)
    return cols


def make_spec(cols, start, interval, distance=70):
    return {"cols": cols, "start": start, "distance": distance, "interval": interval}


_lap = (
    make_spec(build_level(), (1, 1), 1.0),
    make_spec(build_level_2(), (1, 2), 1.0),
    make_spec(build_level_3(), (1, 2), 1.0),
    make_spec(build_level_8(), (1, 2), 1.0),
    make_spec(build_level_9(), (1, 2), 1.0),
    make_spec(build_level_7(), (1, 1), 1.0, 140),
)
LEVELS = _lap + tuple(
    {"cols": spec["cols"], "start": spec["start"], "distance": spec["distance"], "interval": 0.8}
    for spec in _lap
)


def make_click(freq, duration, volume):
    if not AUDIO:
        return type("D", (), {"play": lambda self: None})()
    sr = 22050
    n = int(sr * duration)
    t = np.linspace(0, duration, n, False)
    wave = np.sin(2 * np.pi * freq * t) * np.exp(-t * 36)
    wave = (wave * volume * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack((wave, wave)))


CLICK = make_click(900, 0.028, 0.22)
MOVE = make_click(620, 0.02, 0.12)
JUMP = make_click(1180, 0.04, 0.16)


def make_error():
    """Two tones a semitone apart. The beats read as an error, not a tune."""
    if not AUDIO:
        return type("D", (), {"play": lambda self: None})()
    sr = 22050
    duration = 0.17
    n = int(sr * duration)
    t = np.linspace(0, duration, n, False)
    wave = (np.sin(2 * np.pi * 185 * t) + np.sin(2 * np.pi * 196 * t)) * 0.5
    wave = wave * np.exp(-t * 16)
    wave = (wave * 0.42 * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack((wave, wave)))


ERROR = make_error()
# Same beep voice as the rest of the game, just a short rising phrase.
FANFARE = (
    (0.00, 523),
    (0.18, 659),
    (0.36, 784),
    (0.54, 1047),
    (0.78, 784),
    (0.96, 1175),
    (1.14, 1319),
    (1.38, 1047),
    (1.62, 1568),
)
FANFARE_SOUNDS = tuple((t, make_click(f, 0.11, 0.2)) for t, f in FANFARE)
HEART_TIMES = (0.36, 0.96)
FANFARE_END = 2.15
# Played once, only when the whole game is cleared.
FINALE = (
    (0.00, 523),
    (0.14, 659),
    (0.28, 784),
    (0.42, 1047),
    (0.62, 988),
    (0.74, 1047),
    (0.86, 1175),
    (1.02, 1047),
    (1.20, 1319),
    (1.34, 1175),
    (1.46, 1319),
    (1.62, 1568),
    (1.84, 1319),
    (1.98, 1568),
    (2.12, 1760),
    (2.34, 1568),
    (2.56, 2093),
    (2.86, 1568),
    (3.08, 2093),
)
FINALE_SOUNDS = tuple((t, make_click(f, 0.12, 0.2)) for t, f in FINALE)
FINALE_HEARTS = (0.42, 1.62)
FINALE_END = 3.55
PEACH_DISTANCE = 0
# Drowning Mario blinks three times. The same error beep marks each flash.
BLINK_ON = 11 / 60
BLINK_CYCLE = 19 / 60
MISS_SOUNDS = tuple((i * BLINK_CYCLE, ERROR) for i in range(3))
MISS_END = 57 / 60
# Short tune before level 1. Same beep voice as the rest of the game.
INTRO = (
    (0.00, 392),
    (0.22, 523),
    (0.44, 659),
    (0.66, 523),
    (0.88, 784),
    (1.10, 880),
)
INTRO_SOUNDS = tuple((t, make_click(f, 0.2, 0.2)) for t, f in INTRO)
INTRO_END = 1.45

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SVG_PATH = os.path.join(SCRIPT_DIR, "gnw_smb.svg")
if not os.path.exists(SVG_PATH):
    print(f"Missing {SVG_PATH}")
    raise SystemExit(1)

print("Rendering sheet...")
full_png = cairosvg.svg2png(url=SVG_PATH, output_width=900, output_height=550)
full_surf = pygame.image.load(BytesIO(full_png)).convert_alpha()
ghost_surf = full_surf.copy()
ghost_surf.fill((170, 178, 160, 40), special_flags=pygame.BLEND_RGBA_MULT)

print("Extracting segments...")
tree = etree.parse(SVG_PATH)
ns = {"svg": "http://www.w3.org/2000/svg"}
SEG = {}
HEARTS = []
LOVE = None
RENDER_W, RENDER_H = 900, 550

def piece_from_paths(paths):
    body = "".join(f'<path d="{p.get("d")}" fill="#000000"/>' for p in paths)
    mini = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4017 2454" '
        f'width="{RENDER_W}" height="{RENDER_H}">{body}</svg>'
    )
    png = cairosvg.svg2png(bytestring=mini.encode(), output_width=RENDER_W, output_height=RENDER_H)
    surf = pygame.image.load(BytesIO(png)).convert_alpha()
    br = surf.get_bounding_rect()
    if br.width <= 3 or br.height <= 3:
        return None
    return (surf.subsurface(br).copy(), br)

for g in tree.xpath("//svg:g[svg:title]", namespaces=ns):
    title = g.find("svg:title", ns).text
    paths = g.findall("svg:path", ns)
    if not paths:
        continue
    try:
        piece = piece_from_paths(paths)
        if piece:
            SEG[title] = piece
        if title == "1.7.1" and len(paths) >= 3:
            hearts = []
            for p in paths[:2]:
                one = piece_from_paths([p])
                if one:
                    hearts.append(one)
            hearts.sort(key=lambda item: item[1].x)
            HEARTS = hearts
            LOVE = piece_from_paths([paths[2]])
    except Exception:
        pass
print(f"Loaded {len(SEG)} segments, {len(HEARTS)} hearts")


def blit_seg(surf, key):
    if key in SEG:
        s, br = SEG[key]
        surf.blit(s, (50 + br.x, 30 + br.y))


def blit_piece(surf, piece):
    if piece:
        s, br = piece
        surf.blit(s, (50 + br.x, 30 + br.y))


class Game:
    DIGIT_PAIRS = (("1.2", "0.3"), ("1.3", "0.4"), ("1.4", "0.5"), ("1.5", "0.6"))
    FONT = {
        "0": "abcdef",
        "1": "bc",
        "2": "abdeg",
        "3": "abcdg",
        "4": "bcfg",
        "5": "acdfg",
        "6": "acdefg",
        "7": "abc",
        "8": "abcdefg",
        "9": "abcdfg",
        "L": "def",
    }

    def __init__(self):
        self.reset()

    def reset(self):
        self.level = 0
        self.lives = 3
        self.score = 0
        self.begin_level(True)

    def begin_level(self, intro):
        spec = LEVELS[self.level]
        self.distance = spec["distance"]
        self.scroll = 0
        self.world_col, self.row = spec["start"]
        self.frame_t = 0.0
        self.interval = spec["interval"]
        self.cleared = False
        self.game_over = False
        self.phase = "intro" if intro else "play"
        self.fanfare_t = 0.0
        self.intro_t = 0.0
        self.notes_done = 0
        self.down_t = 0.0
        self.drown = None
        self.fanfare_loops = 1
        self.tune = FANFARE_SOUNDS
        self.tune_end = FANFARE_END
        self.heart_times = HEART_TIMES
        self.hang = 0.0
        self.hang_miss = False
        self.air = False

    def columns(self):
        return LEVELS[self.level]["cols"]

    def floors(self, col):
        cols = self.columns()
        if col < 0 or col >= len(cols):
            return 0
        return cols[col][0]

    def wall_ids(self, wall):
        if wall is None:
            return ()
        if isinstance(wall, tuple):
            return wall
        return (wall,)

    def walls_at(self, col):
        cols = self.columns()
        if col < 0 or col >= len(cols):
            return ()
        return self.wall_ids(cols[col][1])

    def row_blocked(self, left_col, row):
        """A low wall stops the ground. A high wall stops the middle.
        The piece above the top row stops the top."""
        walls = self.walls_at(left_col)
        if row == 2 and 1 in walls:
            return True
        if row == 1 and 0 in walls:
            return True
        if row == 0 and 2 in walls:
            return True
        return False

    def has(self, col, row):
        return bool(self.floors(col) & (1 << row))

    def screen_col(self):
        return self.world_col - self.scroll

    def drop_or_miss(self):
        if self.hang > 0:
            return
        if self.has(self.world_col, self.row):
            self.air = False
            return
        for row in range(self.row + 1, 3):
            if self.has(self.world_col, row):
                self.row = row
                self.air = False
                return
        self.air = False
        self.miss()

    def nearest_drown(self):
        s = self.screen_col()
        s = 0 if s < 0 else 5 if s > 5 else s
        anchor = MARIO[2][s]
        if anchor not in SEG:
            return DROWN[0]
        _, box = SEG[anchor]
        x = box.x + box.width / 2
        best = DROWN[0]
        best_d = 1e9
        for key in DROWN:
            if key not in SEG:
                continue
            _, b = SEG[key]
            d = abs((b.x + b.width / 2) - x)
            if d < best_d:
                best, best_d = key, d
        return best

    def miss(self):
        if self.phase != "play":
            return
        self.lives -= 1
        self.phase = "down"
        self.drown = self.nearest_drown()
        self.down_t = 0.0
        self.notes_done = 0

    def after_miss(self):
        if self.lives <= 0:
            self.phase = "over"
            self.game_over = True
            return
        score, lives = self.score, self.lives
        self.begin_level(False)
        self.score = score
        self.lives = lives
        self.phase = "play"

    def try_move(self, direction):
        if self.phase != "play" or self.game_over or self.hang > 0:
            return
        nxt = self.world_col + direction
        screen = nxt - self.scroll
        if screen < 0 or screen > 5:
            return
        left = self.world_col if direction > 0 else self.world_col - 1
        if self.row_blocked(left, self.row):
            MOVE.play()
            return
        airborne = self.air
        self.world_col = nxt
        if self.has(self.world_col, self.row):
            self.air = False
            MOVE.play()
            self.reach_peach()
            return
        below = any(self.has(self.world_col, row) for row in range(self.row + 1, 3))
        # A jump allows one sideways step, then he drops.
        # Walking off a ledge holds him in the air a little longer.
        self.air = False
        self.hang = 0.05 if airborne else 0.1
        self.hang_miss = not below
        MOVE.play()

    def try_jump(self):
        if self.phase != "play" or self.game_over or self.hang > 0 or self.air or self.row == 0:
            return
        # A floor in the slot directly above him blocks the jump.
        if self.has(self.world_col, self.row - 1):
            return
        self.row -= 1
        self.air = True
        JUMP.play()
        self.reach_peach()

    def peach_out(self):
        return self.distance <= PEACH_DISTANCE or self.phase in ("fanfare", "points")

    def reach_peach(self):
        if self.phase != "play" or self.game_over:
            return
        if self.distance <= PEACH_DISTANCE and self.row == 0 and self.screen_col() >= 5:
            self.phase = "fanfare"
            self.fanfare_t = 0.0
            self.notes_done = 0
            if self.level in (5, 11):
                self.fanfare_loops = 1
                self.tune = FINALE_SOUNDS
                self.tune_end = FINALE_END
                self.heart_times = FINALE_HEARTS
            else:
                self.fanfare_loops = 1
                self.tune = FANFARE_SOUNDS
                self.tune_end = FANFARE_END
                self.heart_times = HEART_TIMES

    def land(self):
        if self.hang <= 0 or self.phase != "play":
            return
        self.hang = 0.0
        self.drop_or_miss()
        self.reach_peach()

    def beat(self):
        if self.phase != "play" or self.game_over:
            return
        CLICK.play()
        # Peach is on screen. Hold the world so he can walk up to her.
        if self.distance <= PEACH_DISTANCE:
            self.drop_or_miss()
            self.reach_peach()
            return
        self.score += 1
        self.scroll += 1
        self.distance -= 1
        if self.screen_col() < 0:
            if self.row_blocked(self.world_col, self.row):
                self.miss()
                return
            self.world_col += 1
        self.drop_or_miss()
        self.reach_peach()

    def update(self, dt, just):
        if self.phase == "intro":
            self.intro_t += dt
            while (
                self.notes_done < len(INTRO_SOUNDS)
                and self.intro_t >= INTRO_SOUNDS[self.notes_done][0]
            ):
                INTRO_SOUNDS[self.notes_done][1].play()
                self.notes_done += 1
            if self.intro_t < INTRO_END:
                return
            if "jump" in just or "right" in just:
                self.phase = "play"
                self.notes_done = 0
                self.frame_t = 0.0
            return
        if self.phase == "fanfare":
            self.fanfare_t += dt
            total = len(self.tune) * self.fanfare_loops
            while self.notes_done < total:
                i = self.notes_done % len(self.tune)
                loop = self.notes_done // len(self.tune)
                when = self.tune[i][0] + loop * self.tune_end
                if self.fanfare_t < when:
                    break
                self.tune[i][1].play()
                self.notes_done += 1
            if self.fanfare_t >= self.tune_end * self.fanfare_loops:
                self.phase = "points"
                self.cleared = True
            return
        if self.phase == "down":
            self.down_t += dt
            while (
                self.notes_done < len(MISS_SOUNDS)
                and self.down_t >= MISS_SOUNDS[self.notes_done][0]
            ):
                MISS_SOUNDS[self.notes_done][1].play()
                self.notes_done += 1
            if self.down_t >= MISS_END:
                self.after_miss()
            return
        if self.game_over:
            return
        if self.phase == "points":
            if self.level + 1 < len(LEVELS) and ("jump" in just or "right" in just):
                self.level += 1
                score, lives = self.score, self.lives
                self.begin_level(True)
                self.score = score
                self.lives = lives
            return
        if self.hang > 0:
            self.hang -= dt
            self.frame_t += dt
            if self.frame_t >= self.interval:
                self.frame_t = 0
                self.beat()
            if self.hang <= 0 and self.phase == "play":
                self.land()
            return
        if "left" in just:
            self.try_move(-1)
        if "right" in just:
            self.try_move(1)
        if "jump" in just:
            self.try_jump()
        self.frame_t += dt
        if self.frame_t >= self.interval:
            self.frame_t = 0
            self.beat()

    def cheat_to(self, level_index):
        if self.phase != "intro":
            return
        if level_index < 0 or level_index >= len(LEVELS):
            return
        self.level = level_index
        self.score = 0
        self.lives = 3
        self.begin_level(False)

    def drown_on(self):
        if self.game_over:
            return True
        i = int(self.down_t / BLINK_CYCLE)
        if i >= 3:
            return False
        return (self.down_t - i * BLINK_CYCLE) < BLINK_ON

    def draw_slots(self, surf, slots):
        for i, ch in enumerate(slots):
            if ch not in self.FONT:
                continue
            left, right = self.DIGIT_PAIRS[i]
            role = {
                "a": f"{right}.2",
                "b": f"{right}.1",
                "c": f"{right}.0",
                "d": f"{left}.3",
                "e": f"{left}.0",
                "f": f"{left}.2",
                "g": f"{left}.1",
            }
            for part in self.FONT[ch]:
                blit_seg(surf, role[part])

    def draw_number(self, surf, number):
        text = str(max(0, int(number)))
        if len(text) > 4:
            text = text[-4:]
        slots = [" "] * (4 - len(text)) + list(text)
        self.draw_slots(surf, slots)

    def draw_playfield(self, surf):
        for s in range(6):
            col = self.scroll + s
            cols = self.columns()
            mask, wall = cols[col] if col < len(cols) else (0, None)
            for row in range(3):
                if mask & (1 << row):
                    blit_seg(surf, PLAT[row][s])
            if s < 5:
                for w in self.wall_ids(wall):
                    key = ABOVE[s] if w == 2 else WALL[w][s]
                    blit_seg(surf, key)
        if self.drown and ((self.phase == "down" and self.drown_on()) or self.game_over):
            blit_seg(surf, self.drown)
        elif self.phase == "play":
            s = self.screen_col()
            if 0 <= s <= 5 and not self.game_over:
                blit_seg(surf, MARIO[self.row][s])
        if self.peach_out():
            blit_seg(surf, PEACH)
        if self.phase in ("fanfare", "points"):
            blit_piece(surf, LOVE)
            if self.phase == "points":
                shown = len(HEARTS)
            else:
                mark = self.fanfare_t % self.tune_end
                shown = sum(1 for t in self.heart_times if mark >= t)
            for heart in HEARTS[:shown]:
                blit_piece(surf, heart)

    def draw(self, surf):
        surf.fill(BG)
        surf.blit(ghost_surf, (50, 30))
        for i, key in enumerate(LIVES):
            if self.lives > i:
                blit_seg(surf, key)
        if self.phase == "points":
            blit_seg(surf, "1.6.0")
            self.draw_number(surf, self.score)
        elif self.phase == "intro":
            n = self.level + 1
            if n < 10:
                slots = [" ", " ", "L", str(n)]
            else:
                slots = [" ", "L", str(n // 10), str(n % 10)]
            self.draw_slots(surf, slots)
        else:
            blit_seg(surf, "1.6.2")
            self.draw_number(surf, self.distance)
        self.draw_playfield(surf)
        hint = "Left / Right move    Space jumps    R restart"
        if self.phase == "intro":
            hint = "Space or Right starts"
        if self.game_over:
            hint = "Miss — R restart"
        surf.blit(font.render(hint, True, INK), (50, 598))


def main():
    g = Game()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        just = set()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                elif e.key == pygame.K_r:
                    g.reset()
                elif e.key in (pygame.K_2, pygame.K_KP2):
                    g.cheat_to(6)
                elif e.key in (pygame.K_3, pygame.K_KP3):
                    g.cheat_to(11)
                elif e.key in (pygame.K_LEFT, pygame.K_a):
                    just.add("left")
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    just.add("right")
                elif e.key in (pygame.K_SPACE, pygame.K_z):
                    just.add("jump")
        g.update(dt, just)
        g.draw(screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
