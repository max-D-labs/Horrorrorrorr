# menu.py
import pygame
import random
import math

from settings import (SCREEN_W, SCREEN_H, SETTINGS, HIGHSCORES,
                      persist_settings, screen, font, small_font, mid_font, big_font)
from audio import AUDIO
from visuals import draw_crt, CRT_PRESETS

class Menu:
    def __init__(self):
        self.options = ["НАЧАТЬ ПОБЕГ", "НАСТРОЙКИ", "РЕКОРДЫ", "ВЫХОД"]
        self.idx = 0
        self.show_settings = False
        self.show_scores = False
        self.settings_idx = 0
        self.settings_options = [
            ("Громкость", "master_volume"),
            ("Музыка", "music_on"),
            ("CRT-эффект", "crt_on"),
            ("CRT-пресет", "crt_preset"),
            ("Сложность", "difficulty"),
            ("НАЗАД", None),
        ]
        self.glitch_timer = 0
        self.glitch_text = ""

    def handle(self, event):
        if self.show_settings:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.settings_idx = (self.settings_idx - 1) % len(self.settings_options)
                elif event.key == pygame.K_DOWN:
                    self.settings_idx = (self.settings_idx + 1) % len(self.settings_options)
                elif event.key == pygame.K_LEFT:
                    self._adjust_setting(-1)
                elif event.key == pygame.K_RIGHT:
                    self._adjust_setting(1)
                elif event.key == pygame.K_RETURN:
                    if self.settings_options[self.settings_idx][0] == "НАЗАД":
                        self.show_settings = False
                elif event.key == pygame.K_ESCAPE:
                    self.show_settings = False
            return None
        if self.show_scores:
            if event.type == pygame.KEYDOWN:
                self.show_scores = False
            return None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.idx = (self.idx - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.idx = (self.idx + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                opt = self.options[self.idx]
                if opt == "НАЧАТЬ ПОБЕГ":
                    return "play"
                elif opt == "НАСТРОЙКИ":
                    self.show_settings = True
                elif opt == "РЕКОРДЫ":
                    self.show_scores = True
                elif opt == "ВЫХОД":
                    return "quit"
            elif event.key == pygame.K_ESCAPE:
                return "quit"
        return None

    def _adjust_setting(self, delta):
        name, key = self.settings_options[self.settings_idx]
        if key is None:
            return
        if key == "master_volume":
            v = max(0.0, min(1.0, SETTINGS["master_volume"] + delta * 0.1))
            SETTINGS["master_volume"] = v
            AUDIO.set_master(v)
        elif key == "music_on":
            AUDIO.toggle_music()
        elif key == "crt_on":
            SETTINGS["crt_on"] = not SETTINGS["crt_on"]
            persist_settings()
        elif key == "crt_preset":
            i = CRT_PRESETS.index(SETTINGS["crt_preset"])
            SETTINGS["crt_preset"] = CRT_PRESETS[(i + delta) % len(CRT_PRESETS)]
            persist_settings()
        elif key == "difficulty":
            diffs = ["easy", "normal", "hard"]
            i = diffs.index(SETTINGS.get("difficulty", "normal"))
            SETTINGS["difficulty"] = diffs[(i + delta) % len(diffs)]
            persist_settings()

    def _draw_glitch_text(self, text, x, y, color, font_obj, glitch_intensity=2):
        """Рисует текст с эффектом сломанного ТВ."""
        # Основной текст
        surf = font_obj.render(text, True, color)
        
        # Если активен глитч, рисуем сдвинутые копии
        if random.random() < 0.1: 
            # Красный канал
            red_surf = font_obj.render(text, True, (255, 0, 0))
            screen.blit(red_surf, (x - glitch_intensity, y))
            # Синий канал
            blue_surf = font_obj.render(text, True, (0, 0, 255))
            screen.blit(blue_surf, (x + glitch_intensity, y))
        
        screen.blit(surf, (x, y))

    def draw(self):
        # Тёмный фон с легким шумом
        screen.fill((5, 5, 8))
        
        # Заголовок (эффект VHS)
        title_text = "ЭХО ПУСТЫХ КОРИДОРОВ"
        t_title = big_font.render(title_text, True, (200, 200, 200))
        tx = SCREEN_W // 2 - t_title.get_width() // 2
        
        # Глитч-эффект для заголовка
        if random.random() < 0.2:
            pygame.draw.rect(screen, (200, 0, 0), (tx - 10, 52, t_title.get_width() + 20, 4))
            self._draw_glitch_text(title_text, tx, 55, (220, 220, 220), big_font, glitch_intensity=4)
        else:
            screen.blit(t_title, (tx, 55))
            
        sub = font.render("СИСТЕМА ВИДЕОНАБЛЮДЕНИЯ // VHS", True, (100, 100, 100))
        screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 110))

        if self.show_settings:
            self._draw_settings()
        elif self.show_scores:
            self._draw_scores()
        else:
            for i, opt in enumerate(self.options):
                c = (255, 255, 255) if i == self.idx else (120, 120, 120)
                
                # Индикатор выбора (мигающий)
                if i == self.idx:
                    if int(pygame.time.get_ticks() / 300) % 2 == 0:
                        pygame.draw.polygon(screen, (200, 50, 50), [
                            (SCREEN_W // 2 - 150, 220 + i * 50 + 10),
                            (SCREEN_W // 2 - 140, 220 + i * 50 + 15),
                            (SCREEN_W // 2 - 150, 220 + i * 50 + 20),
                        ])
                
                t = mid_font.render(opt, True, c)
                screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 220 + i * 50))

        # Подсказка в самом низу
        hint = small_font.render("↑↓ — выбор  |  ENTER — подтвердить  |  ESC — выход", True, (70, 70, 80))
        screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 30))

        # Применяем наш новый графон
        draw_crt((0, 0), 0.1, preset=SETTINGS.get("crt_preset", "VHS"))

    def _draw_settings(self):
        for i, (name, key) in enumerate(self.settings_options):
            c = (255, 255, 255) if i == self.settings_idx else (120, 120, 120)
            if key is None: label = name
            elif key == "master_volume": label = f"{name}: {int(SETTINGS['master_volume'] * 100)}%"
            elif key == "music_on": label = f"{name}: {'ON' if SETTINGS['music_on'] else 'OFF'}"
            elif key == "crt_on": label = f"{name}: {'ON' if SETTINGS['crt_on'] else 'OFF'}"
            elif key == "crt_preset": label = f"{name}: {SETTINGS['crt_preset']}"
            elif key == "difficulty": label = f"{name}: {SETTINGS.get('difficulty', 'normal')}"
            else: label = name
            
            t = font.render(label, True, c)
            # Небольшой сдвиг для четных строк (эффект VHS-дрожания)
            offset_y = 0
            if random.random() < 0.1: offset_y = random.randint(-1, 1)
            screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 220 + i * 40 + offset_y))

    def _draw_scores(self):
        if HIGHSCORES.get("best_time"):
            t = font.render(f"Лучшее время: {HIGHSCORES['best_time']:.1f} с", True, (220, 220, 100))
        else:
            t = font.render("Рекордов пока нет", True, (150, 150, 150))
        screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 220))
        
        t2 = font.render(f"Пробегов: {HIGHSCORES.get('runs', 0)}", True, (180, 180, 180))
        screen.blit(t2, (SCREEN_W // 2 - t2.get_width() // 2, 260))
        
        best_score = HIGHSCORES.get("best_score", 0)
        t3 = font.render(f"Лучший счёт: {best_score}", True, (180, 180, 180))
        screen.blit(t3, (SCREEN_W // 2 - t3.get_width() // 2, 300))
        
        hint = small_font.render("Нажми любую клавишу", True, (100, 100, 100))
        screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 40))