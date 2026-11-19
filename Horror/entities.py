# entities.py
import random
from collections import deque

MONSTER_HUNTER = "hunter"
MONSTER_PATROL = "patrol"
MONSTER_BLIND = "blind"
MONSTER_TELEPORT = "teleport"


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.last_dir = (0, 1)
        self.stamina = 1.0
        self.has_key = False
        self.has_candle = False
        self.candle_timer = 0.0
        self.smoke_timer = 0.0
        self.adren_timer = 0.0
        self.on_street = False

    def try_move(self, dx, dy, maze, key_required_pos=None):
        nx, ny = self.x + dx, self.y + dy
        if not (0 <= nx < len(maze[0]) and 0 <= ny < len(maze)):
            return False
        if maze[ny][nx] != 0:
            return False
        if key_required_pos and (nx, ny) == key_required_pos and not self.has_key:
            return False
        self.x, self.y = nx, ny
        self.last_dir = (dx, dy)
        return True


class Monster:
    def __init__(self, x, y, mtype=MONSTER_HUNTER):
        self.x = x
        self.y = y
        self.type = mtype
        self.move_timer = 0
        self.base_speed = 0.45
        self.last_known = None
        self.patrol_target = None
        self.teleport_timer = 0.0
        self.memory = {}
        self.ambush_point = None
        self.stage = 0
        self.age = 0.0

    def speed(self):
        s = self.base_speed
        if self.stage == 2:
            s *= 0.6
        if self.type == MONSTER_BLIND:
            s *= 0.9
        return s

    def can_see(self, maze, px, py):
        if self.type == MONSTER_BLIND:
            return False
        if max(abs(px - self.x), abs(py - self.y)) > 6:
            return False
        dx = px - self.x; dy = py - self.y
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            return True
        for i in range(1, steps):
            tx = self.x + int(round(dx * i / steps))
            ty = self.y + int(round(dy * i / steps))
            if maze[ty][tx] == 1:
                return False
        return True

    def hears(self, px, py, quiet):
        r = 3 if quiet else 7
        return abs(px - self.x) + abs(py - self.y) <= r

    def find_path(self, maze, target):
        start = (self.x, self.y)
        if target == start:
            return []
        q = deque([start])
        prev = {start: None}
        W = len(maze[0]); H = len(maze)
        while q:
            cx, cy = q.popleft()
            if (cx, cy) == target:
                break
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < W and 0 <= ny < H and maze[ny][nx] == 0 and (nx, ny) not in prev:
                    prev[(nx, ny)] = (cx, cy)
                    q.append((nx, ny))
        path = []
        node = target
        while node != start and node in prev:
            path.append(node)
            node = prev[node]
        path.reverse()
        return path

    def update(self, dt, maze, player, quiet, smoke_active):
        self.age += dt
        if self.age > 60:
            self.stage = 2
        elif self.age > 30:
            self.stage = 1
        self.move_timer += dt
        if self.move_timer < self.speed():
            return
        self.move_timer = 0

        target = None
        if smoke_active:
            target = self.last_known
        else:
            sees = self.can_see(maze, player.x, player.y)
            hears = self.hears(player.x, player.y, quiet)
            if sees or hears:
                self.last_known = (player.x, player.y)
                target = (player.x, player.y)
                self.memory[(player.x, player.y)] = self.memory.get((player.x, player.y), 0) + 1
            else:
                target = self.last_known or self.ambush_point

        if self.type == MONSTER_TELEPORT:
            self.teleport_timer += self.speed()
            if self.teleport_timer > 5.0:
                self.teleport_timer = 0.0
                for _ in range(20):
                    tx = random.randint(1, len(maze[0]) - 2)
                    ty = random.randint(1, len(maze) - 2)
                    if maze[ty][tx] == 0 and abs(tx - player.x) + abs(ty - player.y) in range(5, 12):
                        self.x, self.y = tx, ty
                        break
                return

        if target:
            path = self.find_path(maze, target)
            if path:
                self.x, self.y = path[0]

        if self.memory and not self.last_known and self.type in (MONSTER_PATROL, MONSTER_HUNTER):
            self.ambush_point = max(self.memory.items(), key=lambda kv: kv[1])[0]


class Item:
    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.kind = kind
        self.collected = False


def place_items(maze, count_key=1, count_candle=2, count_smoke=2, count_adren=1, rooms=None):
    items = []
    free = [(x, y) for y in range(1, len(maze) - 1)
            for x in range(1, len(maze[0]) - 1) if maze[y][x] == 0]
    random.shuffle(free)

    room_cells = []
    if rooms:
        for (x0, y0, x1, y1) in rooms:
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    if maze[yy][xx] == 0:
                        room_cells.append((xx, yy))
        random.shuffle(room_cells)

    def pick_pos(min_dist_from_start=0):
        if room_cells and random.random() < 0.6:
            for pos in room_cells:
                if abs(pos[0] - 1) + abs(pos[1] - 1) >= min_dist_from_start:
                    room_cells.remove(pos)
                    if pos in free:
                        free.remove(pos)
                    return pos
        for pos in free:
            if abs(pos[0] - 1) + abs(pos[1] - 1) >= min_dist_from_start:
                free.remove(pos)
                return pos
        return None

    for _ in range(count_key):
        pos = pick_pos(min_dist_from_start=6)
        if pos:
            items.append(Item(pos[0], pos[1], "key"))

    for kind, n in [("candle", count_candle), ("smoke", count_smoke), ("adren", count_adren)]:
        for _ in range(n):
            pos = pick_pos()
            if pos:
                items.append(Item(pos[0], pos[1], kind))
    return items