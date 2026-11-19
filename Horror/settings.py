# settings.py
import pygame
import json

# ---------------- Инициализация ----------------
pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
    pygame.mixer.set_num_channels(16)
    AUDIO_OK = True
except pygame.error:
    AUDIO_OK = False

# ---------------- Константы ----------------
TILE_SIZE = 40
BASE_MAZE_W = 41
BASE_MAZE_H = 31
HUD_H = 60
SR = 44100

SCREEN_W = 1000
SCREEN_H = 700

BLACK = (0, 0, 0)
WALL_COLOR = (40, 40, 50)
FLOOR_COLOR = (15, 15, 20)
PLAYER_COLOR = (100, 255, 150)
MONSTER_COLOR = (220, 30, 30)
EXIT_COLOR = (255, 220, 80)
HUD_COLOR = (180, 180, 180)
KEY_COLOR = (240, 200, 60)
CANDLE_COLOR = (255, 160, 40)
SMOKE_COLOR = (170, 170, 200)
ADREN_COLOR = (60, 200, 255)

SAVE_SCORES = "highscores.json"
SAVE_SETTINGS = "settings.json"

# ---------------- Экран ----------------
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("ЭХО ПУСТЫХ КОРИДОРОВ")
clock = pygame.time.Clock()

font = pygame.font.SysFont("couriernew", 18, bold=True)
small_font = pygame.font.SysFont("couriernew", 14)
mid_font = pygame.font.SysFont("couriernew", 24, bold=True)
big_font = pygame.font.SysFont("couriernew", 42, bold=True)

# ---------------- Настройки / рекорды ----------------
def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

SETTINGS = load_json(SAVE_SETTINGS, {
    "master_volume": 0.7,
    "music_on": True,
    "crt_on": True,
    "crt_preset": "VHS",
    "difficulty": "normal"
})
HIGHSCORES = load_json(SAVE_SCORES, {"best_time": None, "best_score": 0, "runs": 0})

def persist_settings():
    save_json(SAVE_SETTINGS, SETTINGS)

def persist_scores():
    save_json(SAVE_SCORES, HIGHSCORES)