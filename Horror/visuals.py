# visuals.py
import pygame
import random
import math

from settings import SCREEN_W, SCREEN_H, HUD_H, SETTINGS, screen
from audio import AUDIO

CRT_PRESETS = ["VHS", "GREEN", "BROKEN"]


def build_scary_face(size, variant=0):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill((15, 10, 10))
    cx, cy = size // 2, size // 2
    skin = [
        (200, 190, 170),
        (180, 170, 150),
        (210, 200, 180),
        (190, 175, 165),
        (170, 170, 175),
    ][variant % 5]
    face_rect = pygame.Rect(0, 0, int(size * 0.7), int(size * 0.9))
    face_rect.center = (cx, cy + size // 20)
    pygame.draw.ellipse(surf, skin, face_rect)

    eye_w_ratio = [0.14, 0.18, 0.12, 0.16, 0.20][variant % 5]
    eye_h_ratio = [0.16, 0.22, 0.14, 0.20, 0.26][variant % 5]
    eye_off = [0.16, 0.18, 0.14, 0.15, 0.20][variant % 5]

    for sign in (-1, 1):
        ex = cx + sign * int(size * eye_off)
        ey = cy - int(size * 0.1)
        shadow = pygame.Rect(0, 0, int(size * 0.18), int(size * 0.22))
        shadow.center = (ex, ey + int(size * 0.04))
        pygame.draw.ellipse(surf, (60, 40, 40), shadow)
        eye_rect = pygame.Rect(0, 0, int(size * eye_w_ratio), int(size * eye_h_ratio))
        eye_rect.center = (ex, ey)
        pygame.draw.ellipse(surf, (5, 0, 0), eye_rect)
        pupil_r = max(3, int(size * (0.025 + 0.005 * (variant % 3))))
        pygame.draw.circle(surf, (220, 0, 0), (ex, ey), pupil_r)
        pygame.draw.circle(surf, (255, 200, 200), (ex, ey), max(1, pupil_r // 2))

    mouth_w = int(size * (0.3 + 0.03 * (variant % 4)))
    mouth_h = int(size * (0.32 + 0.02 * (variant % 3)))
    mouth_rect = pygame.Rect(0, 0, mouth_w, mouth_h)
    mouth_rect.center = (cx, cy + int(size * 0.25))
    pygame.draw.ellipse(surf, (10, 0, 0), mouth_rect)
    teeth_w = max(3, size // 30)
    teeth_h = max(5, size // 20)
    start_x = mouth_rect.left + 4
    for i in range(6):
        tx = start_x + i * (mouth_rect.width - 8) // 6
        pygame.draw.rect(surf, (230, 220, 200), (tx, mouth_rect.top, teeth_w, teeth_h))
        pygame.draw.rect(surf, (230, 220, 200), (tx, mouth_rect.bottom - teeth_h, teeth_w, teeth_h))
    for sign in (-1, 1):
        ex = cx + sign * int(size * eye_off)
        sy = cy + int(size * 0.02)
        for i in range(3):
            length = random.randint(size // 12, size // 7)
            pygame.draw.line(surf, (140, 0, 0), (ex + i * 3 - 3, sy), (ex + i * 3 - 3, sy + length), 2)
    for i in range(20):
        x = random.randint(face_rect.left, face_rect.right)
        y = random.randint(face_rect.top, face_rect.top + size // 6)
        pygame.draw.line(surf, (5, 0, 0), (x, y), (x + random.randint(-8, 8), y + random.randint(20, 60)), 2)
    return surf


FACE_SIZE = int(min(SCREEN_W, SCREEN_H - HUD_H) * 0.95)
SCARY_FACES = [build_scary_face(FACE_SIZE, i) for i in range(5)]


def make_scanlines():
    s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    for y in range(0, SCREEN_H, 3):
        pygame.draw.line(s, (0, 0, 0, 80), (0, y), (SCREEN_W, y))
    return s


SCANLINES = make_scanlines()

VIGNETTE = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
_cx, _cy = SCREEN_W // 2, SCREEN_H // 2
_maxd = math.hypot(_cx, _cy)
for r in range(0, int(_maxd), 4):
    a = int(min(255, (r / _maxd) ** 2 * 220))
    pygame.draw.circle(VIGNETTE, (0, 0, 0, a), (_cx, _cy), int(_maxd) - r, 4)

NOISE = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)


# ============================================================
#                    ПОСТ-ОБРАБОТКА (ГРАФОН)
# ============================================================
_chromatic_cache = {}

def apply_chromatic_aberration(surface, offset=2):
    """Сдвигает красный и синий каналы в стороны (VHS-эффект)."""
    w, h = surface.get_size()
    # Берем копию
    rgb = pygame.surfarray.array3d(surface)
    r = rgb[:, :, 0]
    g = rgb[:, :, 1]
    b = rgb[:, :, 2]
    
    # Сдвигаем R влево, B вправо
    r_shift = pygame.surfarray.make_surface(r)
    b_shift = pygame.surfarray.make_surface(b)
    
    # Создаем пустые каналы нужного размера
    empty = pygame.Surface((w, h), pygame.SRCALPHA)
    
    # Собираем обратно
    result = pygame.Surface((w, h), pygame.SRCALPHA)
    
    # Простой трюк через BLEND_ADD
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    out.fill((0,0,0,255))
    
    r_surf = pygame.Surface((w, h))
    r_surf.fill((0,0,0))
    r_surf.blit(pygame.surfarray.make_surface(pygame.surfarray.array3d(surface)[:,:,0]), (offset, 0))
    
    b_surf = pygame.Surface((w, h))
    b_surf.fill((0,0,0))
    b_surf.blit(pygame.surfarray.make_surface(pygame.surfarray.array3d(surface)[:,:,2]), (-offset, 0))
    
    # Модифицируем цвета на месте для скорости (без numpy, если его нет, используем блендинг)
    # Для производительности используем простой сдвиг целых прямоугольников
    pass 

def draw_crt(shake_offset, danger_level, preset="VHS"):
    if not SETTINGS.get("crt_on", True):
        return
        
    # 1. Хроматическая аберрация (RGB-сдвиг)
    # Чтобы не тормозило, сдвигаем только края экрана (создаем иллюзию)
    w, h = SCREEN_W, SCREEN_H
    offset = 2 + int(danger_level * 4)
    
    # Берем область экрана и копируем
    screen_copy = screen.copy()
    
    # Рисуем красный канал со сдвигом влево
    screen.fill((255, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
    screen.blit(screen_copy, (-offset, 0), special_flags=pygame.BLEND_RGB_ADD)
    
    # Рисуем синий канал со сдвигом вправо
    screen_copy.fill((0, 0, 255), special_flags=pygame.BLEND_RGB_MULT)
    screen.blit(screen_copy, (offset, 0), special_flags=pygame.BLEND_RGB_ADD)

    # 2. VHS-помехи (горизонтальные полосы)
    n_glitch = int(5 + danger_level * 30)
    for _ in range(n_glitch):
        gy = random.randint(0, h - 5)
        gh = random.randint(1, 6)
        strip = pygame.Surface((w, gh), pygame.SRCALPHA)
        # Белые или цветные полосы
        if random.random() < 0.3:
            strip.fill((255, 255, 255, random.randint(20, 60)))
        else:
            strip.fill((random.randint(100, 255), random.randint(50, 150), random.randint(100, 255), random.randint(10, 40)))
        screen.blit(strip, (random.randint(-5, 5), gy))

    # 3. Шум (Nоise)
    n_noise = 200 + int(danger_level * 600)
    for _ in range(n_noise):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        shade = random.randint(100, 255)
        screen.set_at((x, y), (shade, shade, shade))

    # 4. Scanlines (интерференция)
    screen.blit(SCANLINES, (0, 0))

    # 5. Виньетка + затемнение по краям
    screen.blit(VIGNETTE, (0, 0))
    
    # Случайное мерцание (яркость кадра)
    if random.random() < 0.1:
        flick = pygame.Surface((w, h), pygame.SRCALPHA)
        flick.fill((255, 255, 255, random.randint(10, 30)))
        screen.blit(flick, (0, 0))


class Scaremer:
    def __init__(self):
        self.active = False
        self.timer = 0.0
        self.duration = 1.4
        self.face = SCARY_FACES[0]

    def trigger(self, foreshadow=False):
        if self.active:
            return
        self.active = True
        self.timer = 0.0
        self.duration = 0.6 if foreshadow else 1.4
        self.face = random.choice(SCARY_FACES)
        AUDIO.play_screech()

    def update(self, dt):
        if self.active:
            self.timer += dt
            if self.timer >= self.duration:
                self.active = False

    def draw(self, shake_offset):
        if not self.active:
            return
        t = self.timer / self.duration
        scale = 1.0 + (1.0 - t) * 0.35
        wobble = math.sin(self.timer * 60) * 6
        off_x = shake_offset[0] + random.randint(-14, 14)
        off_y = shake_offset[1] + random.randint(-14, 14)
        w = int(self.face.get_width() * scale)
        h = int(self.face.get_height() * scale)
        scaled = pygame.transform.smoothscale(self.face, (w, h))
        px = (SCREEN_W - w) // 2 + off_x + int(wobble)
        py = (SCREEN_H - HUD_H - h) // 2 + off_y
        if t < 0.12:
            flash = pygame.Surface((SCREEN_W, SCREEN_H))
            flash.fill((255, 255, 255))
            screen.blit(flash, (0, 0))
        screen.blit(scaled, (px, py))
        pulse = pygame.Surface((SCREEN_W, SCREEN_H - HUD_H), pygame.SRCALPHA)
        pulse.fill((120, 0, 0, int(90 * (1 - t))))
        screen.blit(pulse, (0, 0))
        for _ in range(6):
            gy = random.randint(0, SCREEN_H - HUD_H - 20)
            gh = random.randint(4, 20)
            strip = pygame.Surface((SCREEN_W, gh), pygame.SRCALPHA)
            strip.fill((255, 0, 0, random.randint(30, 90)))
            screen.blit(strip, (random.randint(-20, 20), gy))


SCREAMER = Scaremer()