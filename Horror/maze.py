# maze.py
import random


def generate_maze(width, height, corridor_bias=0.0):
    """
    Базовый лабиринт DFS.
    corridor_bias — 0..1, «пробивает» дополнительные проходы (0 = чистый DFS,
    1 = много петель и открытых мест). Влияет на «лабиринтность».
    """
    maze = [[1 for _ in range(width)] for _ in range(height)]
    stack = [(1, 1)]
    maze[1][1] = 0
    while stack:
        x, y = stack[-1]
        nbrs = []
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            nx, ny = x + dx, y + dy
            if 0 < nx < width - 1 and 0 < ny < height - 1 and maze[ny][nx] == 1:
                nbrs.append((nx, ny, dx // 2, dy // 2))
        if nbrs:
            nx, ny, mx, my = random.choice(nbrs)
            maze[y + my][x + mx] = 0
            maze[ny][nx] = 0
            stack.append((nx, ny))
        else:
            stack.pop()

    # «петли» — пробиваем часть стен, чтобы лабиринт не был древовидным
    if corridor_bias > 0:
        extra = int(width * height * corridor_bias * 0.08)
        for _ in range(extra):
            x = random.randint(1, width - 2)
            y = random.randint(1, height - 2)
            if maze[y][x] == 1:
                # пробиваем, если есть хотя бы 2 свободных соседа (не тупик)
                free_n = 0
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height and maze[ny][nx] == 0:
                        free_n += 1
                if free_n >= 2:
                    maze[y][x] = 0
    return maze


def _carve_rooms(maze, width, height, count, rmin, rmax):
    rooms = []
    attempts = 0
    max_attempts = count * 50
    while len(rooms) < count and attempts < max_attempts:
        attempts += 1
        w = random.randint(rmin, rmax)
        h = random.randint(rmin, rmax)
        x0 = random.randint(2, width - w - 3)
        y0 = random.randint(2, height - h - 3)
        x1 = x0 + w - 1
        y1 = y0 + h - 1
        overlap = False
        for (rx0, ry0, rx1, ry1) in rooms:
            if not (x1 + 1 < rx0 or x0 - 1 > rx1 or y1 + 1 < ry0 or y0 - 1 > ry1):
                overlap = True
                break
        if overlap:
            continue
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                maze[yy][xx] = 0
        _connect_room(maze, x0, y0, x1, y1, width, height)
        rooms.append((x0, y0, x1, y1))
    return rooms


def _connect_room(maze, x0, y0, x1, y1, width, height):
    perimeter = []
    for x in range(x0, x1 + 1):
        perimeter.append((x, y0))
        perimeter.append((x, y1))
    for y in range(y0, y1 + 1):
        perimeter.append((x0, y))
        perimeter.append((x1, y))
    random.shuffle(perimeter)
    n_passages = random.randint(1, 2)
    made = 0
    for (px, py) in perimeter:
        if made >= n_passages:
            break
        dirs = []
        if py == y0: dirs.append((0, -1))
        if py == y1: dirs.append((0, 1))
        if px == x0: dirs.append((-1, 0))
        if px == x1: dirs.append((1, 0))
        random.shuffle(dirs)
        for (dx, dy) in dirs:
            nx, ny = px + dx, py + dy
            if 1 <= nx < width - 1 and 1 <= ny < height - 1:
                maze[ny][nx] = 0
                made += 1
                break


def generate_floor(width, height, room_count=5, corridor_bias=0.2,
                   room_min=3, room_max=6):
    """Лабиринт + комнаты. Возвращает (maze, rooms)."""
    maze = generate_maze(width, height, corridor_bias=corridor_bias)
    rooms = _carve_rooms(maze, width, height, room_count, room_min, room_max)
    return maze, rooms


# ============================================================
#                       УЛИЦА
# ============================================================
def generate_street(width, height):
    """
    Полноценная улица:
      - дорога посередине (3 полосы) с разметкой
      - тротуары по обе стороны
      - здания сверху и снизу (блоки стен с проходами)
      - фонарные столбы (декор, отдельные точки)
      - машины (декор — блоки 2×1)
    Возвращает (maze, decor) — decor: dict с точками фонарей и машин.
    """
    maze = [[1 for _ in range(width)] for _ in range(height)]
    mid = height // 2

    road_top = mid - 1
    road_bot = mid + 1
    sidewalk_top = road_top - 1
    sidewalk_bot = road_bot + 1

    # тротуары
    for y in range(sidewalk_top, sidewalk_bot + 1):
        for x in range(1, width - 1):
            maze[y][x] = 0
    # дорога
    for y in range(road_top, road_bot + 1):
        for x in range(1, width - 1):
            maze[y][x] = 0

    # здания сверху
    y_build_top = 2
    y_build_top_end = sidewalk_top - 1
    # здания снизу
    y_build_bot = sidewalk_bot + 1
    y_build_bot_end = height - 3

    def make_building_block(x0, y0, x1, y1):
        """Здание — прямоугольник стен, с «дверью» (проходом 1 клетка) снизу/сверху."""
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                if 0 < xx < width - 1 and 0 < yy < height - 1:
                    maze[yy][xx] = 1
        # дверь — со стороны улицы
        if y0 > mid:
            door_x = random.randint(x0 + 1, x1 - 1)
            maze[y0][door_x] = 0  # дверь сверху
        else:
            door_x = random.randint(x0 + 1, x1 - 1)
            maze[y1][door_x] = 0  # дверь снизу
        # мини-коридор внутри здания — чтобы было куда зайти
        inner_y0 = y0 + 1
        inner_y1 = y1 - 1
        if inner_y0 < inner_y1:
            for yy in range(inner_y0, inner_y1 + 1):
                for xx in range(x0 + 1, x1):
                    maze[yy][xx] = 0

    # разбиваем длину улицы на блоки по 6–10 клеток
    x = 2
    while x < width - 4:
        bw = random.randint(5, 9)
        if x + bw > width - 2:
            bw = width - 2 - x
        if bw < 4:
            break
        # верхнее здание
        make_building_block(x, y_build_top, x + bw - 1, y_build_top_end)
        # нижнее здание
        make_building_block(x, y_build_bot, x + bw - 1, y_build_bot_end)
        x += bw + random.randint(1, 2)

    # декор — фонари и машины (не стены, просто точки для отрисовки)
    decor = {"lamps": [], "cars": []}
    for lx in range(3, width - 3, 8):
        decor["lamps"].append((lx, sidewalk_top))
        decor["lamps"].append((lx, sidewalk_bot))
    for cx in range(4, width - 4, 12):
        if random.random() < 0.6:
            cy = random.choice([road_top, road_bot])
            decor["cars"].append((cx, cy))
    return maze, decor


def maze_walls(maze):
    w = len(maze[0]); h = len(maze)
    return {(x, y) for y in range(h) for x in range(w) if maze[y][x] == 1}