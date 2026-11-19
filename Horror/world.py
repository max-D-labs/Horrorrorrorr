# world.py
import random
import math

from settings import SETTINGS
from floor import Floor
from entities import Player, MONSTER_HUNTER, MONSTER_PATROL, MONSTER_BLIND, MONSTER_TELEPORT


BUILDING_W = 41
BUILDING_H = 31
STREET_W = 71
STREET_H = 27

FLOORS_COUNT = 3


class Camera:
    def __init__(self, world_w_px, world_h_px):
        self.x = 0.0
        self.y = 0.0
        self.view_w = 0
        self.view_h = 0
        self.world_w = world_w_px
        self.world_h = world_h_px

    def set_view(self, vw, vh):
        self.view_w = vw
        self.view_h = vh

    def follow(self, target_px_x, target_px_y, lerp=0.15):
        desired_x = target_px_x - self.view_w / 2
        desired_y = target_px_y - self.view_h / 2
        desired_x = max(0, min(self.world_w - self.view_w, desired_x))
        desired_y = max(0, min(self.world_h - self.view_h, desired_y))
        self.x += (desired_x - self.x) * lerp
        self.y += (desired_y - self.y) * lerp

    def world_to_screen(self, wx, wy):
        return int(wx - self.x), int(wy - self.y)

    def screen_to_world(self, sx, sy):
        return sx + self.x, sy + self.y


class World:
    def __init__(self, level_idx=0):
        self.level_idx = level_idx

        # --- 3 этажа с разными стилями ---
        self.floors = []

        # 1-й: вестибюль, 1 монстр, выход на улицу
        f1 = Floor(0, BUILDING_W, BUILDING_H, is_street=False,
                   style="lobby",
                   monsters_specs=[(MONSTER_PATROL,)])
        self.floors.append(f1)

        # 2-й: офисы, 2 монстра
        f2 = Floor(1, BUILDING_W, BUILDING_H, is_street=False,
                   style="offices",
                   monsters_specs=[(MONSTER_HUNTER,), (MONSTER_PATROL,)])
        self.floors.append(f2)

        # 3-й: техэтаж, 3 монстра (телепорт + охотник + слепой)
        f3 = Floor(2, BUILDING_W, BUILDING_H, is_street=False,
                   style="utility",
                   monsters_specs=[(MONSTER_HUNTER,), (MONSTER_BLIND,), (MONSTER_TELEPORT,)])
        self.floors.append(f3)

        # --- Улица ---
        self.street = Floor(-1, STREET_W, STREET_H, is_street=True)

        # --- Лестницы между этажами ---
        # Этаж 0 ↔ Этаж 1
        low01 = self._pick_stair_cell(f1)
        up01 = self._pick_stair_cell(f2)
        f1.stairs_up.append((low01, 1))
        f2.stairs_down.append((up01, 0))
        # Этаж 1 ↔ Этаж 2
        low12 = self._pick_stair_cell(f2)
        up12 = self._pick_stair_cell(f3)
        f2.stairs_up.append((low12, 2))
        f3.stairs_down.append((up12, 1))

        # --- Выход на улицу (с 1-го этажа) и вход обратно ---
        f1.exit_to_street = self._pick_stair_cell(f1)
        # на улице: вход в здание — в левой части тротуара
        street_cells = self.street.all_free_cells()
        # выбираем клетку на тротуаре (поближе к левому краю)
        sidewalk_candidates = [
            (x, y) for (x, y) in street_cells
            if 2 <= x <= 8 and self.street.maze[y][x] == 0
        ]
        if sidewalk_candidates:
            self.street.enter_from_street = random.choice(sidewalk_candidates)
        else:
            self.street.enter_from_street = street_cells[0] if street_cells else (1, 1)

        # точка победы на улице — правый край
        right_candidates = [
            (x, y) for (x, y) in street_cells
            if x >= STREET_W - 6
        ]
        if right_candidates:
            self.street.exit_to_win = max(right_candidates, key=lambda p: p[0])
        else:
            self.street.exit_to_win = (STREET_W - 3, STREET_H // 2)

        # --- Игрок ---
        self.player = Player(1, 1)
        self.player_floor = 0
        self.player.on_street = False

        # --- Предметы / ломаемые / скрипы ---

        f1.place_items({"key": 0, "candle": 2, "smoke": 2, "adren": 1})
        f1.place_breakables(3)
        f1.place_creaks(3)

        f2.place_items({"key": 0, "candle": 2, "smoke": 2, "adren": 1})
        f2.place_breakables(4)
        f2.place_creaks(4)

        f3.place_items({"key": 1, "candle": 3, "smoke": 3, "adren": 2})
        f3.place_breakables(5)
        f3.place_creaks(5)

        # на улице — улица пустая по предметам (можно добавить, если надо)
        self.street.place_breakables(0)
        self.street.place_creaks(0)

        self.time_alive = 0.0
        self.danger_peak = 0.0
        self.foreshadowed = False
        self.exit_required_key = True

        # на улице видимость меньше (туман) — используется в render.py
        self.visibility_cone = 6.0
        self.street_visibility = 5.0

    def _pick_stair_cell(self, floor):
        if floor.rooms:
            r = random.choice(floor.rooms)
            x = random.randint(r[0], r[2])
            y = random.randint(r[1], r[3])
        else:
            free = floor.all_free_cells()
            x, y = random.choice(free)
        floor.maze[y][x] = 0
        return (x, y)

    @property
    def current(self):
        return self.street if self.player.on_street else self.floors[self.player_floor]

    @property
    def current_maze(self):
        return self.current.maze

    @property
    def current_rooms(self):
        return self.current.rooms

    @property
    def current_monsters(self):
        if self.player.on_street:
            return []
        return self.floors[self.player_floor].monsters

    @property
    def current_items(self):
        return self.current.items

    @property
    def current_visibility(self):
        return self.street_visibility if self.player.on_street else self.visibility_cone

    def change_floor(self, target_floor):
        if target_floor == -1:
            # на улицу — только с 1-го этажа и с ключом
            if self.player_floor != 0:
                return False
            if self.exit_required_key and not self.player.has_key:
                return False
            self.player.on_street = True
            cell = self.street.enter_from_street or (1, 1)
            self.player.x, self.player.y = cell
            return True
        else:
            if not (0 <= target_floor < FLOORS_COUNT):
                return False
            if self.player.on_street:
                if target_floor != 0:
                    return False
                self.player.on_street = False
                self.player_floor = 0
                cell = self.floors[0].exit_to_street
                if cell:
                    self.player.x, self.player.y = cell
                return True
            self.player_floor = target_floor
            return True

    def try_stairs(self):
        """Возвращает ('up'/'down'/'exit'/'enter', target) или None."""
        if self.player.on_street:
            # вход обратно в здание — если стоим на enter_from_street
            pos = (self.player.x, self.player.y)
            if pos == self.street.enter_from_street:
                return ("enter", 0)
            return None
        f = self.floors[self.player_floor]
        pos = (self.player.x, self.player.y)
        for (cell, target) in f.stairs_up:
            if cell == pos:
                return ("up", target)
        for (cell, target) in f.stairs_down:
            if cell == pos:
                return ("down", target)
        if f.exit_to_street == pos:
            return ("exit", -1)
        return None

    def player_break_wall(self, dx, dy):
        f = self.current
        nx, ny = self.player.x + dx, self.player.y + dy
        if (nx, ny) in f.breakable and 0 <= nx < f.mw and 0 <= ny < f.mh:
            f.maze[ny][nx] = 0
            f.breakable.discard((nx, ny))
            for m in self.current_monsters:
                m.last_known = (self.player.x, self.player.y)
            return True
        return False

    def update(self, dt, quiet, keys):
        from visuals import SCREAMER
        self.time_alive += dt

        if self.player.on_street:
            # на улице нет монстров, но проверяем победу
            if (self.player.x, self.player.y) == self.street.exit_to_win:
                return 9999, "win"
            return 9999, None

        f = self.floors[self.player_floor]
        smoke_active = self.player.smoke_timer > 0
        for m in f.monsters:
            m.update(dt, f.maze, self.player, quiet, smoke_active)

        for it in f.items:
            if it.collected:
                continue
            if (it.x, it.y) == (self.player.x, self.player.y):
                it.collected = True
                if it.kind == "key":
                    self.player.has_key = True
                elif it.kind == "candle":
                    self.player.candle_timer = 15.0
                elif it.kind == "smoke":
                    self.player.smoke_timer = 5.0
                elif it.kind == "adren":
                    self.player.adren_timer = 3.0

        self.player.candle_timer = max(0, self.player.candle_timer - dt)
        self.player.smoke_timer = max(0, self.player.smoke_timer - dt)
        self.player.adren_timer = max(0, self.player.adren_timer - dt)

        f.phantom_timer -= dt
        if f.phantom_timer <= 0:
            f.phantom_timer = random.uniform(6, 14)
            ang = random.uniform(0, math.tau)
            dist = random.uniform(3.5, 5.0)
            fx = int(self.player.x + math.cos(ang) * dist)
            fy = int(self.player.y + math.sin(ang) * dist)
            if 0 <= fx < f.mw and 0 <= fy < f.mh and f.maze[fy][fx] == 0:
                f.phantoms.append([fx, fy, 0.25])
        for ph in f.phantoms:
            ph[2] -= dt
        f.phantoms = [ph for ph in f.phantoms if ph[2] > 0]

        dist_min = min(math.hypot(m.x - self.player.x, m.y - self.player.y) for m in f.monsters)
        if dist_min < 1.8 and not self.foreshadowed and not SCREAMER.active:
            self.foreshadowed = True
            SCREAMER.trigger(foreshadow=True)
        if dist_min > 3:
            self.foreshadowed = False

        self.danger_peak = max(self.danger_peak, max(0, 1 - dist_min / 6))
        return dist_min, None