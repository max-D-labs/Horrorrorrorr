# render.py
import pygame
import random
import math

from settings import (TILE_SIZE, SCREEN_W, SCREEN_H, HUD_H,
                      WALL_COLOR, FLOOR_COLOR, PLAYER_COLOR,
                      MONSTER_COLOR, EXIT_COLOR, HUD_COLOR,
                      KEY_COLOR, CANDLE_COLOR, SMOKE_COLOR, ADREN_COLOR,
                      screen, font, small_font, mid_font, big_font)
from entities import MONSTER_BLIND, MONSTER_TELEPORT, MONSTER_PATROL
from audio import AUDIO

# ---------- Палитра ----------
DARK_BG = (6, 6, 9)
HIDDEN_WALL = (13, 13, 17)
HIDDEN_FLOOR = (9, 9, 12)

# ---------- Тинты этажей ----------
FLOOR_TINTS = {
    "lobby":   (40, 30, 20),   # тёплый
    "offices": (25, 25, 30),   # нейтральный
    "utility": (15, 20, 35),   # холодный синеватый
    "street":  (20, 15, 30),   # фиолетово-ночной
}

# ---------- Стили этажей ----------
FLOOR_STYLE_VISUALS = {
    "lobby": {
        "floor": (62, 54, 46),
        "wall":  (78, 68, 58),
        "accent": (140, 110, 70),
        "pattern": "carpet",
    },
    "offices": {
        "floor": (48, 46, 54),
        "wall":  (66, 64, 76),
        "accent": (90, 120, 160),
        "pattern": "tile",
    },
    "utility": {
        "floor": (30, 34, 46),
        "wall":  (44, 50, 66),
        "accent": (70, 130, 180),
        "pattern": "metal",
    },
    "street": {
        "floor": (42, 40, 50),
        "wall":  (54, 52, 64),
        "accent": (120, 100, 160),
        "pattern": "asphalt",
    },
}   

# ---------- Кэш текстур ----------
_texture_cache = {}

def _get_floor_texture(base_color, in_room, seed):
    """Предгенерированная текстура тайла пола. Кэш по (base_color, in_room)."""
    key = (base_color, in_room)
    if key in _texture_cache:
        return _texture_cache[key]
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    rng = random.Random(seed)
    # базовый фон
    surf.fill((*base_color, 255))
    if in_room:
        # плитка — сетка
        grid_color = tuple(min(255, c + 8) for c in base_color)
        pygame.draw.line(surf, (*grid_color, 200), (0, 0), (TILE_SIZE, 0), 1)
        pygame.draw.line(surf, (*grid_color, 200), (0, 0), (0, TILE_SIZE), 1)
        pygame.draw.line(surf, (*grid_color, 140), (TILE_SIZE // 2, 0), (TILE_SIZE // 2, TILE_SIZE), 1)
    else:
        # бетон — редкие пятна
        for _ in range(4):
            px = rng.randint(0, TILE_SIZE - 1)
            py = rng.randint(0, TILE_SIZE - 1)
            r = rng.randint(1, 3)
            shade = rng.randint(-6, 6)
            col = tuple(max(0, min(255, c + shade)) for c in base_color)
            pygame.draw.circle(surf, (*col, 180), (px, py), r)
    _texture_cache[key] = surf
    return surf


def _get_wall_texture(base_color, seed):
    key = ("wall", base_color)
    if key in _texture_cache:
        return _texture_cache[key]
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    rng = random.Random(seed)
    surf.fill((*base_color, 255))
    # кирпичная кладка — намёк
    brick_color = tuple(max(0, c - 8) for c in base_color)
    for row in range(2):
        y = row * (TILE_SIZE // 2)
        pygame.draw.line(surf, (*brick_color, 255), (0, y), (TILE_SIZE, y), 1)
        offset = (TILE_SIZE // 2) if row % 2 else 0
        for x in range(offset, TILE_SIZE, TILE_SIZE // 2):
            pygame.draw.line(surf, (*brick_color, 255), (x, y), (x, y + TILE_SIZE // 2), 1)
    # крапинки
    for _ in range(5):
        px = rng.randint(0, TILE_SIZE - 1)
        py = rng.randint(0, TILE_SIZE - 1)
        shade = rng.randint(-10, 10)
        col = tuple(max(0, min(255, c + shade)) for c in base_color)
        surf.set_at((px, py), (*col, 255))
    _texture_cache[key] = surf
    return surf


def visible_tiles(maze, player, view_dir, radius_cone=4.5, radius_around=1.5):
    """Видимые клетки: конус по направлению + ближний радиус."""
    W, H = len(maze[0]), len(maze)
    vis = set()
    for y in range(max(0, player.y - int(radius_around)),
                   min(H, player.y + int(radius_around) + 1)):
        for x in range(max(0, player.x - int(radius_around)),
                       min(W, player.x + int(radius_around) + 1)):
            if math.hypot(x - player.x, y - player.y) <= radius_around:
                vis.add((x, y))
    if view_dir is None:
        return vis
    half_angle = math.radians(55)
    cos_half = math.cos(half_angle)
    r = int(math.ceil(radius_cone))
    x0 = max(0, player.x - r)
    x1 = min(W, player.x + r + 1)
    y0 = max(0, player.y - r)
    y1 = min(H, player.y + r + 1)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if (x, y) in vis:
                continue
            dx = x - player.x
            dy = y - player.y
            dist = math.hypot(dx, dy)
            if dist > radius_cone or dist < 0.001:
                continue
            dot = (dx * view_dir[0] + dy * view_dir[1]) / dist
            if dot < cos_half:
                continue
            vis.add((x, y))
    return vis


def _draw_street_decor(floor, camera, offx, offy, vis, world):
    """Улица: разметка, фонари со светом на земле, машины, светящиеся окна."""
    # --- разметка дороги ---
    mid = floor.mh // 2
    for x in range(1, floor.mw - 1):
        if x % 4 < 2 and floor.maze[mid][x] == 0:
            if (x, mid) in vis:
                sx, sy = camera.world_to_screen(x * TILE_SIZE, mid * TILE_SIZE)
                r = pygame.Rect(sx + offx + 4, sy + offy + TILE_SIZE // 2 - 2,
                                TILE_SIZE - 8, 4)
                pygame.draw.rect(screen, (200, 180, 60), r)

    # --- СВЕТ ОТ ФОНАРЕЙ (на земле) ---
    # Рисуем до самих фонарей, чтобы столбы были поверх света.
    for (lx, ly) in floor.decor.get("lamps", []):
        # свет виден даже если клетка не в конусе (это уличное освещение)
        sx, sy = camera.world_to_screen(lx * TILE_SIZE, ly * TILE_SIZE)
        cx = sx + offx + TILE_SIZE // 2
        cy = sy + offy + TILE_SIZE // 2
        # круг света на земле — большой тёплый ореол
        light_r = TILE_SIZE * 3
        light = pygame.Surface((light_r * 2, light_r * 2), pygame.SRCALPHA)
        # слои: от яркого центра к прозрачному краю
        for i in range(6, 0, -1):
            r = int(light_r * i / 6)
            a = int(26 + 30 * (1 - i / 6))
            pygame.draw.circle(light, (255, 220, 140, a),
                               (light_r, light_r), r)
        screen.blit(light, (cx - light_r, cy - light_r))

        # --- сам фонарь (столб + лампа) ---
        pygame.draw.rect(screen, (80, 80, 90),
                         (cx - 2, cy - TILE_SIZE // 2, 4, TILE_SIZE // 2))
        # яркая лампа
        pygame.draw.circle(screen, (255, 245, 200), (cx, cy - TILE_SIZE // 2), 5)
        # маленький «блик» вокруг лампы
        halo = pygame.Surface((TILE_SIZE * 2, TILE_SIZE * 2), pygame.SRCALPHA)
        pygame.draw.circle(halo, (255, 240, 180, 70),
                           (TILE_SIZE, TILE_SIZE), TILE_SIZE // 2)
        screen.blit(halo, (cx - TILE_SIZE, cy - TILE_SIZE // 2 - TILE_SIZE))

    # --- СВЕТЯЩИЕСЯ ОКНА НА ЗДАНИЯХ ---
    # Проходим по всем стенам в поле экрана и с шансом рисуем окно,
    # если рядом (снизу/сверху) есть пол — то есть это фасад здания.
    # Соседство кэшируется в floor, чтобы окна не мигали.
    if not hasattr(floor, "_window_cache"):
        rng = random.Random(floor.index * 999 + 42)
        windows = {}
        for y in range(1, floor.mh - 1):
            for x in range(1, floor.mw - 1):
                if floor.maze[y][x] != 1:
                    continue
                # фасад: стена, у которой снизу или сверху пол
                is_facade = (floor.maze[y + 1][x] == 0) or (floor.maze[y - 1][x] == 0)
                if not is_facade:
                    continue
                if rng.random() < 0.18:  # 18% стен — с окнами
                    windows[(x, y)] = rng.random()
        floor._window_cache = windows

    for (wx, wy), seed in floor._window_cache.items():
        # окна видны издалека — не привязываем к конусу
        if abs(wx - world.player.x) > 20 or abs(wy - world.player.y) > 15:
            continue
        sx, sy = camera.world_to_screen(wx * TILE_SIZE, wy * TILE_SIZE)
        # мерцание
        flicker = 0.85 + 0.15 * math.sin(world.time_alive * 2 + seed * 10)
        base_col = (255, 220, 120) if seed > 0.3 else (120, 180, 255)
        col = tuple(int(c * flicker) for c in base_col)
        win = pygame.Rect(sx + offx + TILE_SIZE // 2 - 6,
                          sy + offy + TILE_SIZE // 2 - 5, 12, 10)
        # само окно
        pygame.draw.rect(screen, col, win, border_radius=1)
        # крестовина
        pygame.draw.line(screen, (40, 40, 50),
                         (win.centerx, win.top), (win.centerx, win.bottom), 1)
        pygame.draw.line(screen, (40, 40, 50),
                         (win.left, win.centery), (win.right, win.centery), 1)
        # лёгкий ореол окна
        glow = pygame.Surface((24, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (*col, 50), (0, 0, 24, 20))
        screen.blit(glow, (win.x - 6, win.y - 5))

    # --- МАШИНЫ ---
    for (cxk, cyk) in floor.decor.get("cars", []):
        if (cxk, cyk) not in vis:
            continue
        sx, sy = camera.world_to_screen(cxk * TILE_SIZE, cyk * TILE_SIZE)
        r = pygame.Rect(sx + offx + 2, sy + offy + 8, TILE_SIZE - 4, TILE_SIZE - 16)
        pygame.draw.rect(screen, (110, 40, 40), r, border_radius=4)
        win = pygame.Rect(r.x + 4, r.y + 2, r.w - 8, r.h // 3)
        pygame.draw.rect(screen, (70, 90, 110), win, border_radius=2)
        # фары — светятся вперёд
        pygame.draw.circle(screen, (255, 240, 180), (r.right - 4, r.centery), 2)
        # свет от фар — маленький конус справа
        head = pygame.Surface((TILE_SIZE, TILE_SIZE // 2), pygame.SRCALPHA)
        pygame.draw.polygon(head, (255, 240, 180, 50), [
            (0, TILE_SIZE // 4), (TILE_SIZE, 0), (TILE_SIZE, TILE_SIZE // 2),
        ])
        screen.blit(head, (r.right, r.y + r.h // 4))

def _draw_floor_decor(floor, camera, offx, offy, vis, world):
    """Декор для разных этажей: колонны / столы / трубы."""
    style = getattr(floor, "style", "offices")
    if style == "lobby":
        # колонны — в комнатах, по углам
        for (rx0, ry0, rx1, ry1) in floor.rooms:
            for (cx, cy) in [(rx0, ry0), (rx1, ry0), (rx0, ry1), (rx1, ry1)]:
                if (cx, cy) not in vis:
                    continue
                sx, sy = camera.world_to_screen(cx * TILE_SIZE, cy * TILE_SIZE)
                r = pygame.Rect(sx + offx + 10, sy + offy + 10, TILE_SIZE - 20, TILE_SIZE - 20)
                pygame.draw.ellipse(screen, (90, 80, 70), r)
                pygame.draw.ellipse(screen, (140, 120, 100), r, 2)
    elif style == "offices":
        # «столы» — маленькие блоки внутри комнат
        rng = random.Random(floor.index * 1000 + 7)
        for (rx0, ry0, rx1, ry1) in floor.rooms:
            for _ in range(2):
                if rx1 - rx0 < 3 or ry1 - ry0 < 3:
                    continue
                cx = rng.randint(rx0 + 1, rx1 - 1)
                cy = rng.randint(ry0 + 1, ry1 - 1)
                if (cx, cy) not in vis:
                    continue
                sx, sy = camera.world_to_screen(cx * TILE_SIZE, cy * TILE_SIZE)
                r = pygame.Rect(sx + offx + 8, sy + offy + 8, TILE_SIZE - 16, TILE_SIZE - 16)
                pygame.draw.rect(screen, (60, 45, 35), r, border_radius=2)
                pygame.draw.rect(screen, (100, 80, 60), r, 1, border_radius=2)
    elif style == "utility":
        # трубы вдоль верхней/нижней границы стен
        rng = random.Random(floor.index * 1000 + 13)
        for x in range(1, floor.mw - 1, 3):
            for y in (1, floor.mh - 2):
                if (x, y) in vis and floor.maze[y][x] == 1:
                    sx, sy = camera.world_to_screen(x * TILE_SIZE, y * TILE_SIZE)
                    pygame.draw.line(screen, (80, 60, 40),
                                     (sx + offx, sy + offy + 4),
                                     (sx + offx + TILE_SIZE * 2, sy + offy + 4), 2)


def _draw_glow(target_px, target_py, color, base_radius, world_time, pulse=0.0):
    """Мягкое свечение — несколько кругов с нарастающей прозрачностью."""
    layers = 4
    for i in range(layers):
        r = int(base_radius * (1 + i * 0.6 + pulse * math.sin(world_time * 4 + i)))
        a = int(60 * (1 - i / layers))
        if r <= 0 or a <= 0:
            continue
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, a), (r, r), r)
        screen.blit(glow, (target_px - r, target_py - r))


def draw_world(world, dist_min, shake, danger, view_dir, camera):
    screen.fill(DARK_BG)
    offx, offy = shake

    floor = world.current
    maze = floor.maze
    mw, mh = floor.mw, floor.mh
        # Стиль этажа
    style_key = "street" if floor.is_street else getattr(floor, "style", "offices")
    style_info = FLOOR_STYLE_VISUALS.get(style_key, FLOOR_STYLE_VISUALS["offices"])
    base_floor = style_info["floor"]
    base_wall = style_info["wall"]
    pattern = style_info["pattern"]
    base_floor = getattr(floor, "floor_color", FLOOR_COLOR)
    base_wall = getattr(floor, "wall_color", WALL_COLOR)

    radius_cone = world.current_visibility + (1.5 if world.player.candle_timer > 0 else 0)
    vis = visible_tiles(maze, world.player, view_dir,
                        radius_cone=radius_cone, radius_around=1.5)

    cam_left = camera.x
    cam_top = camera.y
    cam_right = camera.x + SCREEN_W
    cam_bot = camera.y + SCREEN_H - HUD_H
    start_x = max(0, int(cam_left // TILE_SIZE) - 1)
    end_x = min(mw, int(cam_right // TILE_SIZE) + 2)
    start_y = max(0, int(cam_top // TILE_SIZE) - 1)
    end_y = min(mh, int(cam_bot // TILE_SIZE) + 2)

    in_room = set()
    for (rx0, ry0, rx1, ry1) in floor.rooms:
        for y in range(ry0, ry1 + 1):
            for x in range(rx0, rx1 + 1):
                in_room.add((x, y))

    # ---------- Пол и стены ----------
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            sx, sy = camera.world_to_screen(x * TILE_SIZE, y * TILE_SIZE)
            rect = pygame.Rect(sx + offx, sy + offy, TILE_SIZE, TILE_SIZE)
            is_wall = maze[y][x] == 1
            visible = (x, y) in vis
            if visible:
                d = math.hypot(x - world.player.x, y - world.player.y)
                min_alpha = 0.6 if floor.is_street else 0.45
                alpha = max(min_alpha, 1 - d / (radius_cone + 3))
                if is_wall:
                    tex = _get_wall_texture(base_wall, x * 1000 + y)
                    # стены — ярче
                    c = tuple(int(255 * (0.7 + alpha * 0.3)) for _ in range(3))
                    tex_mod = tex.copy()
                    tex_mod.fill((*c, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    wob = 0
                    if danger > 0.5:
                        wob = int(math.sin(world.time_alive * 4 + x + y) * (danger - 0.5) * 3)
                    rect.y += wob
                    screen.blit(tex_mod, rect.topleft)

                    # светлая кромка сверху — «верх стены»
                    pygame.draw.line(screen, (150, 145, 160),
                                     (rect.left, rect.top), (rect.right, rect.top), 2)
                    # тёмная кромка снизу — «тень стены»
                    pygame.draw.line(screen, (15, 15, 20),
                                     (rect.left, rect.bottom - 1),
                                     (rect.right, rect.bottom - 1), 2)

                    if (x, y) in floor.breakable:
                        overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        overlay.fill((200, 120, 80, 60))
                        screen.blit(overlay, rect.topleft)
                else:
                    tex = _get_floor_texture(base_floor, pattern, x * 1000 + y)
                    # пол — темнее
                    c = tuple(int(255 * (0.4 + alpha * 0.35)) for _ in range(3))
                    tex_mod = tex.copy()
                    tex_mod.fill((*c, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    screen.blit(tex_mod, rect.topleft)
            else:
                if is_wall:
                    pygame.draw.rect(screen, HIDDEN_WALL, rect)
                else:
                    pygame.draw.rect(screen, HIDDEN_FLOOR, rect)

    # ---------- Тени от стен (fake) ----------
    # маленькая тёмная полоска со стороны, противоположной игроку
    shadow = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            if (x, y) not in vis:
                continue
            if maze[y][x] != 1:
                continue
            sx, sy = camera.world_to_screen(x * TILE_SIZE, y * TILE_SIZE)
            dx = x - world.player.x
            dy = y - world.player.y
            if dx > 0:
                pygame.draw.rect(shadow, (0, 0, 0, 80),
                                 (sx + offx - 4, sy + offy, 4, TILE_SIZE))
            elif dx < 0:
                pygame.draw.rect(shadow, (0, 0, 0, 80),
                                 (sx + offx + TILE_SIZE, sy + offy, 4, TILE_SIZE))
            if dy > 0:
                pygame.draw.rect(shadow, (0, 0, 0, 80),
                                 (sx + offx, sy + offy - 4, TILE_SIZE, 4))
            elif dy < 0:
                pygame.draw.rect(shadow, (0, 0, 0, 80),
                                 (sx + offx, sy + offy + TILE_SIZE, TILE_SIZE, 4))
    screen.blit(shadow, (0, 0))

    # ---------- Декор этажа / улицы ----------
    if floor.is_street:
        _draw_street_decor(floor, camera, offx, offy, vis, world)
    else:
        _draw_floor_decor(floor, camera, offx, offy, vis, world)

    # ---------- Конус фонарика — мягкий градиент ----------
    psx, psy = camera.world_to_screen(
        world.player.x * TILE_SIZE + TILE_SIZE // 2,
        world.player.y * TILE_SIZE + TILE_SIZE // 2,
    )
    # тёмная маска по всему экрану
    mask = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    mask.fill((0, 0, 0, 200))
    # вырезаем «дырку» конусом: несколько слоёв кругов с уменьшением альфы
    outer_r = int((radius_cone + 1) * TILE_SIZE)
    inner_r = int((radius_cone - 1.5) * TILE_SIZE)
    steps = 10
    for i in range(steps):
        t = i / steps
        r = int(inner_r + (outer_r - inner_r) * t)
        alpha = int(200 * (1 - t) ** 0.7)
        if r > 0 and alpha > 0:
            pygame.draw.circle(mask, (0, 0, 0, max(0, 200 - alpha)), (psx, psy), r)
    screen.blit(mask, (0, 0))

    # ---------- Лестницы / выходы ----------
    def draw_marker(cell, color, kind="stair"):
        sx, sy = camera.world_to_screen(cell[0] * TILE_SIZE, cell[1] * TILE_SIZE)
        r = pygame.Rect(sx + 4, sy + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        # пульсация
        pulse = 0.5 + 0.5 * math.sin(world.time_alive * 4)
        glow_alpha = int(60 * pulse)
        halo = pygame.Surface((r.w + 16, r.h + 16), pygame.SRCALPHA)
        pygame.draw.rect(halo, (*color, glow_alpha), (0, 0, r.w + 16, r.h + 16),
                         border_radius=8)
        screen.blit(halo, (r.x - 8, r.y - 8))
        pygame.draw.rect(screen, color, r, 2, border_radius=4)
        # символ
        if kind == "up":
            pygame.draw.polygon(screen, color, [
                (r.centerx, r.top + 6), (r.left + 6, r.bottom - 6), (r.right - 6, r.bottom - 6)
            ])
        elif kind == "down":
            pygame.draw.polygon(screen, color, [
                (r.centerx, r.bottom - 6), (r.left + 6, r.top + 6), (r.right - 6, r.top + 6)
            ])
        elif kind == "exit":
            pygame.draw.rect(screen, color, (r.left + 8, r.centery - 6, r.w - 16, 12))
        elif kind == "enter":
            pygame.draw.circle(screen, color, r.center, r.w // 3, 2)
        elif kind == "win":
            # звезда
            cx, cy = r.center
            pts = []
            for i in range(10):
                ang = -math.pi / 2 + i * math.pi / 5
                rad = r.w // 3 if i % 2 == 0 else r.w // 6
                pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
            pygame.draw.polygon(screen, (255, 255, 255), pts)

    for (cell, target) in floor.stairs_up:
        draw_marker(cell, (80, 240, 120), "up")
    for (cell, target) in floor.stairs_down:
        draw_marker(cell, (240, 180, 80), "down")
    if floor.exit_to_street:
        draw_marker(floor.exit_to_street, (100, 200, 255), "exit")
    if floor.is_street and floor.enter_from_street:
        draw_marker(floor.enter_from_street, (220, 220, 120), "enter")
    if floor.is_street and floor.exit_to_win:
        draw_marker(floor.exit_to_win, (255, 255, 255), "win")

    # ---------- Предметы со свечением ----------
    item_glow_colors = {
        "key": KEY_COLOR, "candle": CANDLE_COLOR,
        "smoke": SMOKE_COLOR, "adren": ADREN_COLOR,
    }
    for it in floor.items:
        if it.collected or (it.x, it.y) not in vis:
            continue
        sx, sy = camera.world_to_screen(it.x * TILE_SIZE, it.y * TILE_SIZE)
        cx = sx + offx + TILE_SIZE // 2
        cy = sy + offy + TILE_SIZE // 2
        _draw_glow(cx, cy, item_glow_colors[it.kind], TILE_SIZE // 2, world.time_alive, 0.1)
        r = pygame.Rect(cx - (TILE_SIZE - 20) // 2, cy - (TILE_SIZE - 20) // 2,
                        TILE_SIZE - 20, TILE_SIZE - 20)
        pygame.draw.rect(screen, item_glow_colors[it.kind], r, border_radius=6)
        pygame.draw.rect(screen, (255, 255, 255), r, 1, border_radius=6)

    # ---------- Монстры (жуткие) ----------
    for m in floor.monsters:
        d = math.hypot(m.x - world.player.x, m.y - world.player.y)
        if d > radius_cone + 2:
            continue
        if (m.x, m.y) not in vis and d > 2.0:
            continue
        alpha = max(0.35, 1 - d / (radius_cone + 3))
        sx, sy = camera.world_to_screen(m.x * TILE_SIZE, m.y * TILE_SIZE)
        cx = sx + offx + TILE_SIZE // 2
        cy = sy + offy + TILE_SIZE // 2
        proximity = max(0.0, 1.0 - d / 6.0)

        # 1) пульсирующая красная аура — чем ближе, тем ярче и толще
        aura_color = (200, 10, 10) if proximity < 0.5 else (255, 30, 30)
        _draw_glow(cx, cy, aura_color,
                   int(TILE_SIZE * 0.7 + proximity * 26),
                   world.time_alive, 0.5 + proximity * 0.8)

        # 2) тело — рваная тёмная фигура (несколько перекрывающихся кругов/эллипсов)
        body_col = tuple(int(c * alpha) for c in (30, 5, 10))
        body_outline = tuple(int(c * alpha) for c in (120, 10, 20))
        # «плащ» — эллипс, чуть шире клетки
        body_rect = pygame.Rect(cx - TILE_SIZE // 2 + 2, cy - TILE_SIZE // 2 + 4,
                                TILE_SIZE - 4, TILE_SIZE - 6)
        # неровные края: 3 смещённых эллипса
        for dx, dy, w, h in [(-2, 2, TILE_SIZE - 6, TILE_SIZE - 8),
                             (2, 4, TILE_SIZE - 4, TILE_SIZE - 10),
                             (0, 8, TILE_SIZE - 10, TILE_SIZE - 12)]:
            rr = pygame.Rect(cx - w // 2 + dx, cy - h // 2 + dy, w, h)
            pygame.draw.ellipse(screen, body_col, rr)
        # лёгкая красная кромка (без явной обводки, но силуэт читается)
        pygame.draw.ellipse(screen, body_outline, body_rect, 1)

        # 3) светящиеся глаза — следят за игроком
        dx_dir = world.player.x - m.x
        dy_dir = world.player.y - m.y
        dl = math.hypot(dx_dir, dy_dir) or 1
        look_x = dx_dir / dl
        look_y = dy_dir / dl
        eye_y = cy - 4
        for sign in (-1, 1):
            ex = cx + sign * 7
            ey = eye_y
            # белок/жёлтый глаз
            eye_col = (255, 240, 120)
            pygame.draw.circle(screen, eye_col, (int(ex), int(ey)), 4)
            # зрачок — смещается к игроку
            px = int(ex + look_x * 1.6)
            py = int(ey + look_y * 1.6)
            pygame.draw.circle(screen, (0, 0, 0), (px, py), 2)

        # 4) пасть — тёмный овал с зубами
        mouth = pygame.Rect(cx - 8, cy + 6, 16, 8)
        pygame.draw.ellipse(screen, (5, 0, 0), mouth)
        # зубы — 4 мелких треугольника
        for i in range(4):
            tx = mouth.left + 2 + i * 3
            pygame.draw.polygon(screen, (230, 220, 200), [
                (tx, mouth.top), (tx + 2, mouth.top), (tx + 1, mouth.top + 4)
            ])

        # 5) «дымка» вокруг — для атмосферы
        if proximity > 0.35:
            smoke = pygame.Surface((TILE_SIZE * 2, TILE_SIZE * 2), pygame.SRCALPHA)
            smoke_col = (120, 0, 0, int(30 * proximity))
            pygame.draw.circle(smoke, smoke_col, (TILE_SIZE, TILE_SIZE), TILE_SIZE)
            screen.blit(smoke, (cx - TILE_SIZE, cy - TILE_SIZE))

        # 6) маркер типа — маленький значок под фигурой (вместо обводки)
        if m.type == MONSTER_BLIND:
            pygame.draw.circle(screen, (160, 160, 160), (cx, cy + TILE_SIZE // 2 - 6), 2)
        elif m.type == MONSTER_TELEPORT:
            pygame.draw.circle(screen, (190, 130, 255), (cx, cy + TILE_SIZE // 2 - 6), 2)
        elif m.type == MONSTER_PATROL:
            pygame.draw.circle(screen, (120, 180, 255), (cx, cy + TILE_SIZE // 2 - 6), 2)

    # ---------- Фантомы ----------
    for ph in floor.phantoms:
        fx, fy, tleft = ph
        if (fx, fy) not in vis:
            continue
        sx, sy = camera.world_to_screen(fx * TILE_SIZE, fy * TILE_SIZE)
        r = pygame.Rect(sx + offx + 8, sy + offy + 8, TILE_SIZE - 16, TILE_SIZE - 16)
        s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        s.fill((200, 200, 255, int(120 * tleft / 0.25)))
        screen.blit(s, (r.x, r.y))

    # ---------- Игрок со свечением ----------
    sx, sy = camera.world_to_screen(world.player.x * TILE_SIZE, world.player.y * TILE_SIZE)
    cx = sx + offx + TILE_SIZE // 2
    cy = sy + offy + TILE_SIZE // 2
    _draw_glow(cx, cy, (80, 200, 120), TILE_SIZE, world.time_alive, 0.1)
    r = pygame.Rect(sx + offx + 6, sy + offy + 6, TILE_SIZE - 12, TILE_SIZE - 12)
    pygame.draw.rect(screen, PLAYER_COLOR, r, border_radius=4)
    pygame.draw.rect(screen, (255, 255, 255), r, 2, border_radius=4)

    # ---------- Курсор ----------
    mx, my = pygame.mouse.get_pos()
    if my < SCREEN_H - HUD_H:
        pulse_r = 4 + int(1.5 * math.sin(world.time_alive * 6))
        pygame.draw.circle(screen, (255, 255, 200), (mx, my), pulse_r, 1)
        pygame.draw.circle(screen, (255, 255, 200), (mx, my), 1)

    # ---------- Кровь по краям ----------
    if danger > 0.3:
        n_drops = int(danger * 14)
        blood_layer = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for _ in range(n_drops):
            side = random.choice(["t", "b", "l", "r"])
            if side == "t":
                x = random.randint(0, SCREEN_W); y0 = 0; y1 = random.randint(20, 100)
                pygame.draw.line(blood_layer, (110, 0, 0, int(danger * 180)),
                                 (x, y0), (x + random.randint(-12, 12), y1), 4)
            elif side == "b":
                x = random.randint(0, SCREEN_W); y0 = SCREEN_H - HUD_H; y1 = y0 - random.randint(20, 100)
                pygame.draw.line(blood_layer, (110, 0, 0, int(danger * 180)),
                                 (x, y0), (x + random.randint(-12, 12), y1), 4)
            elif side == "l":
                y = random.randint(0, SCREEN_H - HUD_H); x0 = 0; x1 = random.randint(20, 100)
                pygame.draw.line(blood_layer, (110, 0, 0, int(danger * 180)),
                                 (x0, y), (x1, y + random.randint(-12, 12)), 4)
            else:
                y = random.randint(0, SCREEN_H - HUD_H); x0 = SCREEN_W; x1 = x0 - random.randint(20, 100)
                pygame.draw.line(blood_layer, (110, 0, 0, int(danger * 180)),
                                 (x0, y), (x1, y + random.randint(-12, 12)), 4)
        screen.blit(blood_layer, (0, 0))

    # ---------- Цветовой тинт этажа ----------
    _tint_key = "street" if floor.is_street else getattr(floor, "style", "offices")
    tint = FLOOR_TINTS.get(_tint_key, (20, 20, 25))
    tint_alpha = 10 if floor.is_street else 18
    tint_layer = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    tint_layer.fill((*tint, tint_alpha))
    screen.blit(tint_layer, (0, 0))


def draw_hud(world, elapsed):
    # Панель
    hud = pygame.Rect(0, SCREEN_H - HUD_H, SCREEN_W, HUD_H)
    pygame.draw.rect(screen, (10, 10, 14), hud)
    pygame.draw.line(screen, (60, 60, 70),
                     (0, SCREEN_H - HUD_H), (SCREEN_W, SCREEN_H - HUD_H), 1)

    # Иконки предметов — цветные квадратики с подписями
    def draw_icon(x, y, color, label):
        pygame.draw.rect(screen, color, (x, y, 16, 16), border_radius=3)
        pygame.draw.rect(screen, (255, 255, 255), (x, y, 16, 16), 1, border_radius=3)
        t = small_font.render(label, True, (200, 200, 200))
        screen.blit(t, (x + 22, y))

    x = 12
    y = SCREEN_H - HUD_H + 8
    if world.player.has_key:
        draw_icon(x, y, KEY_COLOR, "")
        x += 44
    if world.player.candle_timer > 0:
        draw_icon(x, y, CANDLE_COLOR, f"{int(world.player.candle_timer)}")
        x += 60
    if world.player.smoke_timer > 0:
        draw_icon(x, y, SMOKE_COLOR, f"{int(world.player.smoke_timer)}")
        x += 60
    if world.player.adren_timer > 0:
        draw_icon(x, y, ADREN_COLOR, f"{int(world.player.adren_timer)}")
        x += 60

    # Время
    t_time = font.render(f"⏱ {elapsed:0.1f}s", True, HUD_COLOR)
    screen.blit(t_time, (12, SCREEN_H - HUD_H + 30))

    # Управление
    t2 = small_font.render("WASD  Shift  F  E  M  P  ESC", True, (120, 120, 130))
    screen.blit(t2, (SCREEN_W // 2 - t2.get_width() // 2, SCREEN_H - HUD_H + 36))

    # Название этажа
    if world.player.on_street:
        floor_label = "УЛИЦА"
        floor_color = (200, 180, 240)
    else:
        names = ["ВЕСТИБЮЛЬ", "ОФИСЫ", "ТЕХЭТАЖ"]
        floor_label = f"{names[world.player_floor]}  {world.player_floor + 1}/{len(world.floors)}"
        floor_color = (200, 200, 120)
    t_floor = font.render(floor_label, True, floor_color)
    screen.blit(t_floor, (SCREEN_W - t_floor.get_width() - 12, SCREEN_H - HUD_H + 8))

    # Полоска «опасности»
    if not world.player.on_street:
        danger = max(0.0, min(1.0, 1.0 - (min(
            (math.hypot(m.x - world.player.x, m.y - world.player.y)
             for m in world.floors[world.player_floor].monsters), default=9999) / 6.0)))
        if danger > 0.05:
            bar_w = 80
            bar_x = SCREEN_W - bar_w - 12
            bar_y = SCREEN_H - HUD_H + 30
            pygame.draw.rect(screen, (40, 10, 10), (bar_x, bar_y, bar_w, 8), border_radius=3)
            fill_w = int(bar_w * danger)
            col = (int(255 * danger), int(80 * (1 - danger)), 0)
            pygame.draw.rect(screen, col, (bar_x, bar_y, fill_w, 8), border_radius=3)
            lbl = small_font.render("!", True, col)
            screen.blit(lbl, (bar_x - 12, bar_y - 4))

    # Подсказка E
    transition = world.try_stairs()
    if transition:
        kind, target = transition
        labels = {
            "up": "E — подняться выше",
            "down": "E — спуститься ниже",
            "exit": "E — выйти на улицу",
            "enter": "E — вернуться в здание",
        }
        hint_text = labels.get(kind, "E")
        hint = small_font.render(hint_text, True, (120, 240, 140))
        hint_bg = pygame.Rect(SCREEN_W // 2 - hint.get_width() // 2 - 8,
                              SCREEN_H - HUD_H + 4,
                              hint.get_width() + 16, 22)
        pygame.draw.rect(screen, (0, 40, 0), hint_bg, border_radius=4)
        pygame.draw.rect(screen, (80, 200, 100), hint_bg, 1, border_radius=4)
        screen.blit(hint, (hint_bg.x + 8, hint_bg.y + 3))

    # ---------- Миникарта ----------
    mm_size = 140
    mm_x = SCREEN_W - mm_size - 10
    mm_y = 10
    mm = pygame.Surface((mm_size, mm_size), pygame.SRCALPHA)
    mm.fill((0, 0, 0, 170))
    view_range = 14
    scale = mm_size / (view_range * 2 + 1)
    cx_mm = mm_size / 2
    cy_mm = mm_size / 2
    cur = world.current
    for dy in range(-view_range, view_range + 1):
        for dx in range(-view_range, view_range + 1):
            tx = world.player.x + dx
            ty = world.player.y + dy
            if 0 <= tx < cur.mw and 0 <= ty < cur.mh:
                px = cx_mm + dx * scale
                py = cy_mm + dy * scale
                if cur.maze[ty][tx] == 1:
                    color = (60, 60, 75, 200)
                else:
                    color = (22, 22, 28, 200)
                pygame.draw.rect(mm, color, (px, py, scale, scale))
    if not world.player.on_street:
        floor = world.floors[world.player_floor]
        for (cell, _) in floor.stairs_up:
            rel_x = cell[0] - world.player.x
            rel_y = cell[1] - world.player.y
            if abs(rel_x) <= view_range and abs(rel_y) <= view_range:
                pygame.draw.rect(mm, (80, 240, 120, 240),
                                 (cx_mm + rel_x * scale, cy_mm + rel_y * scale, scale, scale))
        for (cell, _) in floor.stairs_down:
            rel_x = cell[0] - world.player.x
            rel_y = cell[1] - world.player.y
            if abs(rel_x) <= view_range and abs(rel_y) <= view_range:
                pygame.draw.rect(mm, (240, 180, 80, 240),
                                 (cx_mm + rel_x * scale, cy_mm + rel_y * scale, scale, scale))
        if floor.exit_to_street:
            ex_rel = floor.exit_to_street[0] - world.player.x
            ey_rel = floor.exit_to_street[1] - world.player.y
            if abs(ex_rel) <= view_range and abs(ey_rel) <= view_range:
                pygame.draw.rect(mm, (100, 200, 255, 240),
                                 (cx_mm + ex_rel * scale, cy_mm + ey_rel * scale, scale, scale))
    else:
        if cur.enter_from_street:
            ex_rel = cur.enter_from_street[0] - world.player.x
            ey_rel = cur.enter_from_street[1] - world.player.y
            if abs(ex_rel) <= view_range and abs(ey_rel) <= view_range:
                pygame.draw.rect(mm, (220, 220, 120, 240),
                                 (cx_mm + ex_rel * scale, cy_mm + ey_rel * scale, scale, scale))
        if cur.exit_to_win:
            ex_rel = cur.exit_to_win[0] - world.player.x
            ey_rel = cur.exit_to_win[1] - world.player.y
            if abs(ex_rel) <= view_range and abs(ey_rel) <= view_range:
                pygame.draw.rect(mm, (255, 255, 255, 240),
                                 (cx_mm + ex_rel * scale, cy_mm + ey_rel * scale, scale, scale))
    # игрок
    pygame.draw.rect(mm, (120, 255, 150, 255),
                     (cx_mm - scale, cy_mm - scale, scale * 2, scale * 2))
    screen.blit(mm, (mm_x, mm_y))
    pygame.draw.rect(screen, (80, 80, 100), (mm_x, mm_y, mm_size, mm_size), 1, border_radius=4)


def show_center_message(title, sub, color=(255, 255, 255)):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H - HUD_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    screen.blit(overlay, (0, 0))
    # тень + текст
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        t = big_font.render(title, True, (0, 0, 0))
        screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2 + dx, SCREEN_H // 2 - 80 + dy))
    t = big_font.render(title, True, color)
    screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 80))
    if sub:
        s = mid_font.render(sub, True, (220, 220, 220))
        screen.blit(s, (SCREEN_W // 2 - s.get_width() // 2, SCREEN_H // 2 - 20))