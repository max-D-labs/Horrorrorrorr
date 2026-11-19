# floor.py
import random
from maze import generate_floor, generate_street
from entities import Monster, place_items


# Конфиги разных «типов» этажей
FLOOR_STYLES = {
    "lobby": {
        # вестибюль: много комнат, широкие коридоры, светло
        "rooms": (6, 9),
        "room_size": (4, 7),
        "corridor_bias": 0.35,
        "floor_color": (30, 26, 30),
        "wall_color": (45, 45, 55),
    },
    "offices": {
        # офисы: средние комнаты, обычные коридоры
        "rooms": (5, 7),
        "room_size": (3, 6),
        "corridor_bias": 0.2,
        "floor_color": (22, 18, 22),
        "wall_color": (40, 40, 50),
    },
    "utility": {
        # техэтаж: узкие коридоры, мало комнат, темнее
        "rooms": (3, 5),
        "room_size": (3, 5),
        "corridor_bias": 0.05,
        "floor_color": (14, 12, 15),
        "wall_color": (30, 30, 38),
    },
}


class Floor:
    def __init__(self, index, width, height, is_street=False,
                 style="offices", monsters_specs=None,
                 street_decor=None):
        self.index = index
        self.is_street = is_street
        self.mw = width
        self.mh = height
        self.style = style
        self.decor = street_decor or {}

        if is_street:
            self.maze, self.decor = generate_street(width, height)
            self.rooms = []
            self.floor_color = (24, 22, 26)
            self.wall_color = (50, 50, 60)
        else:
            cfg = FLOOR_STYLES.get(style, FLOOR_STYLES["offices"])
            room_count = random.randint(*cfg["rooms"])
            rmin, rmax = cfg["room_size"]
            self.maze, self.rooms = generate_floor(
                width, height,
                room_count=room_count,
                corridor_bias=cfg["corridor_bias"],
                room_min=rmin, room_max=rmax,
            )
            self.floor_color = cfg["floor_color"]
            self.wall_color = cfg["wall_color"]

        self.stairs_up = []
        self.stairs_down = []
        self.exit_to_street = None
        self.enter_from_street = None
        self.exit_to_win = None

        self.items = []
        self.monsters = []
        self.breakable = set()
        self.creak_cells = set()
        self.phantoms = []
        self.phantom_timer = random.uniform(4, 8)

        if monsters_specs and not is_street:
            self._spawn_monsters(monsters_specs)

    def _spawn_monsters(self, specs):
        spawns = [
            (self.mw - 3, self.mh - 3),
            (self.mw - 2, 2),
            (2, self.mh - 2),
        ]
        random.shuffle(spawns)
        for i, (mtype,) in enumerate(specs):
            use_room = self.rooms and random.random() < 0.5
            if use_room:
                far_rooms = [r for r in self.rooms
                             if (r[0] + r[2]) / 2 + (r[1] + r[3]) / 2 > 8]
                if far_rooms:
                    rx0, ry0, rx1, ry1 = random.choice(far_rooms)
                    sx = random.randint(rx0, rx1)
                    sy = random.randint(ry0, ry1)
                else:
                    sx, sy = spawns[i % len(spawns)]
            else:
                sx, sy = spawns[i % len(spawns)]
            if self.maze[sy][sx] == 1:
                sx, sy = self.mw - 2, self.mh - 3
                self.maze[sy][sx] = 0
            self.monsters.append(Monster(sx, sy, mtype))

    def all_free_cells(self):
        return [(x, y) for y in range(1, self.mh - 1)
                for x in range(1, self.mw - 1) if self.maze[y][x] == 0]

    def place_breakables(self, n):
        free_walls = []
        for y in range(1, self.mh - 1):
            for x in range(1, self.mw - 1):
                if self.maze[y][x] == 1:
                    free_walls.append((x, y))
        random.shuffle(free_walls)
        for i in range(n):
            if i < len(free_walls):
                self.breakable.add(free_walls[i])

    def place_creaks(self, n):
        free = self.all_free_cells()
        random.shuffle(free)
        for i in range(n):
            if i < len(free):
                self.creak_cells.add(free[i])

    def place_items(self, spec, rooms=None):
        self.items = place_items(self.maze,
                                 count_key=spec.get("key", 0),
                                 count_candle=spec.get("candle", 0),
                                 count_smoke=spec.get("smoke", 0),
                                 count_adren=spec.get("adren", 0),
                                 rooms=rooms or self.rooms)