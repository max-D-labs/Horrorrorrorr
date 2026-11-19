# main.py
import pygame
import random
import math
import time

from settings import (SCREEN_W, SCREEN_H, HUD_H, TILE_SIZE, SETTINGS,
                     HIGHSCORES, persist_scores, screen, clock,
                     small_font, AUDIO_OK)
from audio import AUDIO
from visuals import SCREAMER, draw_crt, SCARY_FACES, FACE_SIZE
from world import World, Camera
from render import draw_world, draw_hud, show_center_message
from menu import Menu

FIXED_DT = 1.0 / 60.0

def play_intro():
    """Длинная кинематографичная заставка."""
    intro_timer = 0.0
    intro_duration = 12.0
    running = True
    
    # Предзагружаем шрифты для заставки
    intro_font = pygame.font.SysFont("couriernew", 60, bold=True)
    sub_font = pygame.font.SysFont("couriernew", 24)
    
    while running:
        raw_dt = clock.tick(60) / 1000.0
        intro_timer += raw_dt
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                if intro_timer > 1.0: # Можно пропустить
                    running = False

        if intro_timer > intro_duration:
            running = False

        screen.fill((0, 0, 0))
        
        # --- ФАЗА 1: Включение кинескопа (0.0 - 2.0 сек) ---
        if intro_timer < 2.0:
            h = int(SCREEN_H * (intro_timer / 2.0))
            if h < 2: h = 2
            # Яркая вспышка с градиентом
            for i in range(5):
                alpha = int(255 * (1 - i/5))
                line = pygame.Surface((SCREEN_W, h), pygame.SRCALPHA)
                line.fill((255, 255, 255, alpha))
                screen.blit(line, (0, SCREEN_H//2 - h//2))
            
            # Звук включения (можно использовать короткий щелчок или просто оставить так)
            if intro_timer < 0.1 and not hasattr(play_intro, "_played"):
                play_intro._played = True
                AUDIO.play_creak()

        else:
            # --- ФАЗА 2: Логотип (2.0 - 5.0 сек) ---
            if 2.0 <= intro_timer < 5.0:
                fade_in = min(1.0, (intro_timer - 2.0) / 1.5)
                alpha = int(255 * fade_in)
                
                text = "MEGA"
                t = intro_font.render(text, True, (220, 220, 220))
                t.set_alpha(alpha)
                
                # Жуткий VHS-глитч для логотипа
                dx = random.randint(-3, 3) if random.random() < 0.3 else 0
                dy = random.randint(-2, 2) if random.random() < 0.3 else 0
                
                # Хроматическая аберрация
                red_surf = intro_font.render(text, True, (255, 0, 0))
                red_surf.set_alpha(alpha)
                blue_surf = intro_font.render(text, True, (0, 0, 255))
                blue_surf.set_alpha(alpha)
                
                cx = SCREEN_W // 2 - t.get_width() // 2
                cy = SCREEN_H // 2 - t.get_height() // 2
                
                screen.blit(red_surf, (cx - 4 + dx, cy + dy))
                screen.blit(blue_surf, (cx + 4 + dx, cy + dy))
                screen.blit(t, (cx + dx, cy + dy))
                
                if intro_timer > 2.5:
                    sub = sub_font.render("ENTERTAINMENT", True, (150, 150, 150))
                    sub.set_alpha(min(alpha, int(255 * (intro_timer - 2.5) / 1.0)))
                    screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, cy + 70))

            # --- ФАЗА 3: Нарастание тревоги (5.0 - 8.0 сек) ---
            elif 5.0 <= intro_timer < 8.0:
                pulse = math.sin((intro_timer - 5.0) * 10) * 0.5 + 0.5
                
                # Красная пульсация фона
                red_bg = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                red_bg.fill((int(100 * pulse), 0, 0, int(255 * pulse)))
                screen.blit(red_bg, (0, 0))
                
                # Текст начинает глючить
                text = "СИСТЕМА НЕИСПРАВНА"
                t = sub_font.render(text, True, (255, 255, 255))
                if random.random() < 0.5:
                    t = sub_font.render("СИСТЕМА НЕИСПРАВНА", True, (random.choice([255, 0]), 0, random.choice([255, 0])))
                screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 20))
                
                # Если монстр близко - играем скрип
                if intro_timer > 6.0 and random.random() < 0.05:
                    AUDIO.play_creak()

            # --- ФАЗА 4: Появление лица (8.0 - 11.0 сек) ---
            elif 8.0 <= intro_timer < 11.0:
                # Сначала белый шум
                if intro_timer < 8.5:
                    for _ in range(1000):
                        x = random.randint(0, SCREEN_W - 1)
                        y = random.randint(0, SCREEN_H - 1)
                        c = random.randint(0, 255)
                        screen.set_at((x, y), (c, c, c))
                
                # Лицо появляется и держится
                from visuals import SCARY_FACES
                face = SCARY_FACES[0] # Берем первое лицо
                
                # Наложение лица
                face_alpha = min(255, int((intro_timer - 8.0) * 255))
                face_surf = face.copy()
                face_surf.set_alpha(face_alpha)
                
                # Лицо трясется
                fx = random.randint(-5, 5) if random.random() < 0.5 else 0
                fy = random.randint(-5, 5) if random.random() < 0.5 else 0
                
                screen.blit(face_surf, (SCREEN_W//2 - FACE_SIZE//2 + fx, SCREEN_H//2 - FACE_SIZE//2 + fy))
                
                # Текст поверх лица
                if intro_timer > 9.0:
                    text = "ТЫ ТОТ, КТО ВОЙДЁТ?"
                    t = sub_font.render(text, True, (255, 0, 0))
                    screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H - 100))

            # --- ФАЗА 5: Затухание (11.0 - 12.0 сек) ---
            elif intro_timer >= 11.0:
                # Экран медленно гаснет
                fade_out = max(0.0, 1.0 - (intro_timer - 11.0))
                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, int(255 * (1 - fade_out))))
                screen.blit(overlay, (0, 0))

        # Применяем наш новый графон
        draw_crt((0, 0), 0.3, preset="VHS")
        pygame.display.flip()
        
    return "menu"


def _recenter_camera(world, camera):
    floor = world.current
    camera.world_w = floor.mw * TILE_SIZE
    camera.world_h = floor.mh * TILE_SIZE
    camera.set_view(SCREEN_W, SCREEN_H - HUD_H)
    px = world.player.x * TILE_SIZE + TILE_SIZE // 2
    py = world.player.y * TILE_SIZE + TILE_SIZE // 2
    camera.x = max(0, min(camera.world_w - SCREEN_W, px - SCREEN_W // 2))
    camera.y = max(0, min(camera.world_h - (SCREEN_H - HUD_H),
                          py - (SCREEN_H - HUD_H) // 2))


def game_loop(level_idx=0):
    world = World(level_idx)
    camera = Camera(world.current.mw * TILE_SIZE, world.current.mh * TILE_SIZE)
    _recenter_camera(world, camera)

    AUDIO.start_ambient("dark" if AUDIO.music_on else None)

    start_scare_triggered = False
    start_scare_timer = 1.5
    quiet = False
    paused = False
    last_move_time = 0.0
    elapsed = 0.0
    scare_cooldown = 0.0
    running = True
    result = None

    while running:
        raw_dt = clock.tick(60) / 1000.0
        dt = min(raw_dt, FIXED_DT * 2)
        elapsed += dt
        shake = (0, 0)
        dist_min = 9999
        if not world.player.on_street:
            f = world.floors[world.player_floor]
            if f.monsters:
                dist_min = min(math.hypot(m.x - world.player.x, m.y - world.player.y)
                               for m in f.monsters)
        danger = max(0.0, min(1.0, 1.0 - dist_min / 6.0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
                if event.key == pygame.K_p:
                    paused = not paused
                if event.key == pygame.K_m:
                    AUDIO.toggle_music()
                if event.key == pygame.K_f:
                    if not paused:
                        world.player_break_wall(*world.player.last_dir)
                if event.key == pygame.K_e:
                    if not paused:
                        transition = world.try_stairs()
                        if transition:
                            kind, target = transition
                            if world.change_floor(target):
                                _recenter_camera(world, camera)
                                AUDIO.play_creak()

        if not paused and not SCREAMER.active:
            if not start_scare_triggered:
                start_scare_timer -= dt
                if start_scare_timer <= 0:
                    start_scare_triggered = True
                    SCREAMER.trigger()

            keys = pygame.key.get_pressed()
            quiet = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            base_delay = 0.12
            if quiet:
                base_delay = 0.35
            if world.player.adren_timer > 0:
                base_delay = 0.06

            now = pygame.time.get_ticks() / 1000.0
            if now - last_move_time > base_delay:
                dx = dy = 0
                if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -1
                elif keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = 1
                elif keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -1
                elif keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = 1
                if dx or dy:
                    cur = world.current
                    key_required = cur.exit_to_street if (not world.player.on_street) else None
                    moved = world.player.try_move(dx, dy, cur.maze,
                                                  key_required_pos=key_required)
                    if moved:
                        last_move_time = now
                        AUDIO.play_step(quiet=quiet)
                        if not world.player.on_street:
                            f = world.floors[world.player_floor]
                            if (world.player.x, world.player.y) in f.creak_cells:
                                AUDIO.play_creak()
                                for m in f.monsters:
                                    m.last_known = (world.player.x, world.player.y)

            dist_min, win_flag = world.update(dt, quiet, keys)
            if win_flag == "win":
                AUDIO.stop_ambient()
                result = "win"
                running = False

            if dist_min < 4:
                intensity = int((4 - dist_min) * 2)
                shake = (random.randint(-intensity, intensity),
                         random.randint(-intensity, intensity))

            scare_cooldown = max(0, scare_cooldown - dt)
            if dist_min < 2.5 and scare_cooldown <= 0 and random.random() < 0.002:
                SCREAMER.trigger()
                scare_cooldown = 12.0

            if not world.player.on_street:
                f = world.floors[world.player_floor]
                caught = any((world.player.x, world.player.y) == (m.x, m.y) for m in f.monsters)
                if caught:
                    SCREAMER.trigger()
                    AUDIO.stop_ambient()
                    result = "lose"
                    running = False

        AUDIO.update(dt, dist_min, game_active=not paused and not SCREAMER.active)
        AUDIO.swap_ambient_if_needed(AUDIO.danger_level(dist_min))

        # направление фонарика
        mx, my = pygame.mouse.get_pos()
        if my >= SCREEN_H - HUD_H:
            my = SCREEN_H - HUD_H - 1
        player_sx, player_sy = camera.world_to_screen(
            world.player.x * TILE_SIZE + TILE_SIZE // 2,
            world.player.y * TILE_SIZE + TILE_SIZE // 2,
        )
        vdx = mx - player_sx
        vdy = my - player_sy
        vlen = math.hypot(vdx, vdy)
        if vlen < 1:
            view_dir = (0, 1)
        else:
            view_dir = (vdx / vlen, vdy / vlen)

        draw_world(world, dist_min, shake, danger, view_dir, camera)
        draw_hud(world, elapsed)
        if paused:
            show_center_message("ПАУЗА", "P — продолжить, ESC — меню")
        SCREAMER.update(dt)
        SCREAMER.draw(shake)
        
        # Применяем VHS-графон
        draw_crt(shake, danger, preset=SETTINGS.get("crt_preset", "VHS"))
        pygame.display.flip()

        camera.follow(
            world.player.x * TILE_SIZE + TILE_SIZE // 2,
            world.player.y * TILE_SIZE + TILE_SIZE // 2,
            lerp=0.2,
        )

    if result == "win":
        collected = sum(1 for it in world.current.items if it.collected)
        score = int(max(0, 200 - elapsed * 2) + collected * 10 + int(world.danger_peak * 50))
        HIGHSCORES["runs"] = HIGHSCORES.get("runs", 0) + 1
        if HIGHSCORES.get("best_time") is None or elapsed < HIGHSCORES["best_time"]:
            HIGHSCORES["best_time"] = elapsed
        if score > HIGHSCORES.get("best_score", 0):
            HIGHSCORES["best_score"] = score
        persist_scores()

        waiting = True
        while waiting:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        waiting = False
            screen.fill((0, 0, 0))
            show_center_message("ПОБЕГ УДАЛСЯ!",
                                f"Время: {elapsed:.1f}с  Счёт: {score}",
                                (100, 255, 150))
            hint = small_font.render("ENTER — в меню", True, (160, 160, 160))
            screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 80))
            draw_crt((0, 0), 0.0)
            pygame.display.flip()
        return "menu"

    if result == "lose":
        waiting = True
        while waiting:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_r):
                        return ("retry", level_idx)
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
            SCREAMER.draw((0, 0))
            show_center_message("ТЕБЯ СЪЕЛИ...", "ENTER — заново, ESC — меню", (255, 50, 50))
            draw_crt((0, 0), 0.5)
            pygame.display.flip()
    return "menu"

def main():
    state = "intro"  # Начинаем с заставки!
    menu = Menu()
    current_level = 0
    AUDIO.set_master(SETTINGS.get("master_volume", 0.7))

    while state != "quit":
        if state == "intro":
            res = play_intro()
            if res == "quit":
                return
            state = "menu"
            
        elif state == "menu":
            running = True
            while running:
                clock.tick(60)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                    res = menu.handle(event)
                    if res == "play":
                        state = "game"
                        current_level = 0
                        running = False
                    elif res == "quit":
                        return
                menu.draw() # Внутри menu.draw уже вызывается draw_crt!
                pygame.display.flip()
                
        elif state == "game":
            res = game_loop(current_level)
            if res == "quit":
                return
            elif res == "menu":
                state = "menu"
            elif isinstance(res, tuple):
                if res[0] == "retry":
                    current_level = res[1]
                elif res[0] == "next_level":
                    current_level = res[1]
                state = "game"

    pygame.quit()

if __name__ == "__main__":
    main()