# audio.py
import pygame
import random
import math
import array

from settings import AUDIO_OK, SR, SETTINGS, persist_settings

def _clip(v, lo=-32767, hi=32767):
    return int(max(lo, min(hi, v)))

def _mk_sound(buf, volume=0.7):
    if not AUDIO_OK:
        return None
    try:
        s = pygame.mixer.Sound(buffer=buf.tobytes())
        s.set_volume(volume)
        return s
    except Exception:
        return None

def make_screech(seed_shift=0.0):
    duration = 1.2
    n = int(duration * SR)
    buf = array.array('h')
    for i in range(n):
        t = i / SR
        p = i / n
        noise = random.randint(-32767, 32767) * (1.0 - p) ** 2
        freq = 880 + 600 * math.sin(t * 40 + seed_shift) + 200 * math.sin(t * 13 + seed_shift)
        tone = math.sin(2 * math.pi * freq * t) * 12000 * (1.0 - p)
        growl = math.sin(2 * math.pi * 60 * t) * 8000 * (1.0 - p)
        buf.append(_clip(noise * 0.4 + tone + growl))
    return _mk_sound(buf, 0.9)

def make_step(volume=0.25, quiet=False):
    duration = 0.09 if not quiet else 0.05
    n = int(duration * SR)
    buf = array.array('h')
    prev = 0.0
    vol = 0.35 if not quiet else 0.1
    for i in range(n):
        p = i / n
        noise = random.uniform(-1, 1)
        prev = prev * 0.85 + noise * 0.15
        env = (1 - p) ** 2
        tone = math.sin(2 * math.pi * 90 * (i / SR)) * (0.3 if not quiet else 0.05)
        sample = (prev * 2.5 + tone) * env
        buf.append(_clip(sample * 32767 * vol))
    return _mk_sound(buf, volume)

def make_growl():
    duration = 0.6
    n = int(duration * SR)
    buf = array.array('h')
    prev = 0.0
    for i in range(n):
        t = i / SR
        p = i / n
        env = math.sin(math.pi * p)
        f = 55 + 12 * math.sin(t * 30) + 4 * math.sin(t * 7)
        tone = math.sin(2 * math.pi * f * t) * 0.5
        noise = random.uniform(-1, 1)
        prev = prev * 0.9 + noise * 0.1
        sample = (tone + prev * 1.8) * env
        buf.append(_clip(sample * 32767))
    return _mk_sound(buf, 0.7)

def make_heartbeat():
    duration = 0.55
    n = int(duration * SR)
    buf = array.array('h')
    for i in range(n):
        t = i / SR
        s = 0.0
        for strike_t in (0.0, 0.18):
            local = t - strike_t
            if 0 <= local < 0.16:
                p = local / 0.16
                env = (1 - p) ** 2
                s += math.sin(2 * math.pi * (70 - 20 * p) * local) * env * 0.6
        buf.append(_clip(s * 32767))
    return _mk_sound(buf, 0.8)

def make_breath():
    duration = 1.6
    n = int(duration * SR)
    buf = array.array('h')
    prev = 0.0
    for i in range(n):
        p = i / n
        env = math.sin(math.pi * p) ** 2
        noise = random.uniform(-1, 1)
        prev = prev * 0.7 + noise * 0.3
        s = prev * env * 0.35 + math.sin(2 * math.pi * 160 * (i / SR)) * env * 0.02
        buf.append(_clip(s * 32767))
    return _mk_sound(buf, 0.25)

def make_creak():
    duration = 0.5
    n = int(duration * SR)
    buf = array.array('h')
    for i in range(n):
        t = i / SR
        p = i / n
        env = (1 - p) ** 1.5
        freq = 320 + 180 * math.sin(t * 55)
        s = math.sin(2 * math.pi * freq * t) * env
        s += random.uniform(-1, 1) * env * 0.15
        buf.append(_clip(s * 32767 * 0.4))
    return _mk_sound(buf, 0.6)

def make_whisper_short():
    duration = 0.45
    n = int(duration * SR)
    buf = array.array('h')
    for i in range(n):
        t = i / SR
        p = i / n
        env = math.sin(math.pi * p)
        w = (math.sin(2 * math.pi * 210 * t) * 0.4 +
             math.sin(2 * math.pi * 430 * t) * 0.25 +
             math.sin(2 * math.pi * 730 * t) * 0.15)
        s = (w + random.uniform(-1, 1) * 0.1) * env * 0.4
        buf.append(_clip(s * 32767))
    return _mk_sound(buf, 0.45)

def make_ambient(preset="dark", duration=12.0):
    n = int(duration * SR)
    buf = array.array('h')
    if preset == "dark":
        freqs = [55.0, 82.5, 110.0]
    elif preset == "tense":
        freqs = [65.0, 97.5, 130.0]
    else:
        freqs = [40.0, 60.0]
    phases = [random.random() * 2 * math.pi for _ in freqs]
    creaks = [(random.uniform(0, duration), random.uniform(0.4, 0.9))
              for _ in range(int(duration / 3))]
    whisper_period = 5.5 if preset != "empty" else 9.0
    for i in range(n):
        t = i / SR
        s = 0.0
        for k, f in enumerate(freqs):
            mod = 0.55 + 0.45 * math.sin(2 * math.pi * 0.07 * t + k * 1.3)
            s += math.sin(2 * math.pi * f * t + phases[k]) * 0.18 * mod
        s += random.uniform(-1, 1) * 0.015
        for ct, ca in creaks:
            dl = t - ct
            if 0 <= dl < 0.6:
                p = dl / 0.6
                env = (1 - p) * ca
                s += math.sin(2 * math.pi * (320 + 180 * math.sin(dl * 55)) * dl) * env * 0.08
        wc = t % whisper_period
        if 0.0 <= wc < 0.4:
            p = wc / 0.4
            env = math.sin(math.pi * p)
            w = (math.sin(2 * math.pi * 210 * t) * 0.4 +
                 math.sin(2 * math.pi * 430 * t) * 0.25 +
                 math.sin(2 * math.pi * 730 * t) * 0.15)
            s += w * env * 0.05
        buf.append(_clip(s * 32767))
    return _mk_sound(buf, 0.35)


class AudioManager:
    def __init__(self):
        self.screeches = [make_screech(s) for s in (0.0, 1.7, 3.1, 4.9, 6.2)]
        self.step_loud = make_step(0.25, quiet=False)
        self.step_quiet = make_step(0.08, quiet=True)
        self.growl = make_growl()
        self.heartbeat = make_heartbeat()
        self.breath = make_breath()
        self.creak = make_creak()
        self.whisper = make_whisper_short()
        self.ambients = {
            "dark": make_ambient("dark"),
            "tense": make_ambient("tense"),
            "empty": make_ambient("empty"),
        }
        self.ambient_channel = None
        self.current_ambient_key = None
        self.music_on = SETTINGS.get("music_on", True)
        self.master = SETTINGS.get("master_volume", 0.7)
        self.growl_timer = 0.0
        self.heart_timer = 0.0
        self.breath_timer = 0.0
        self.whisper_timer = random.uniform(12, 25)
        self.creak_timer = random.uniform(20, 35)

    def set_master(self, v):
        self.master = v
        SETTINGS["master_volume"] = v
        persist_settings()
        if self.ambient_channel:
            self.ambient_channel.set_volume(0.35 * v)

    def toggle_music(self):
        self.music_on = not self.music_on
        SETTINGS["music_on"] = self.music_on
        persist_settings()
        if self.music_on:
            self.start_ambient(self.current_ambient_key or "dark")
        else:
            self.stop_ambient()

    def start_ambient(self, key="dark"):
        if not AUDIO_OK:
            return
        if key not in self.ambients:
            key = "dark"
        snd = self.ambients[key]
        if not snd:
            return
        self.stop_ambient()
        self.ambient_channel = pygame.mixer.Channel(0)
        self.ambient_channel.set_volume(0.35 * self.master)
        self.ambient_channel.play(snd, loops=-1)
        self.current_ambient_key = key

    def stop_ambient(self):
        if self.ambient_channel:
            self.ambient_channel.stop()
            self.ambient_channel = None

    def swap_ambient_if_needed(self, danger_level):
        if not AUDIO_OK or not self.music_on:
            return
        target = "tense" if danger_level > 0.6 else "dark"
        if target != self.current_ambient_key:
            self.start_ambient(target)

    def play_step(self, quiet=False):
        if not AUDIO_OK:
            return
        snd = self.step_quiet if quiet else self.step_loud
        if snd:
            ch = pygame.mixer.find_channel(True)
            if ch:
                ch.set_volume((0.10 if quiet else 0.25) * self.master)
                ch.play(snd)

    def play_creak(self):
        if AUDIO_OK and self.creak:
            ch = pygame.mixer.find_channel(True)
            if ch:
                ch.set_volume(0.6 * self.master)
                ch.play(self.creak)

    def play_whisper(self):
        if AUDIO_OK and self.whisper:
            ch = pygame.mixer.find_channel(True)
            if ch:
                ch.set_volume(0.45 * self.master)
                ch.play(self.whisper)

    def play_breath(self):
        if AUDIO_OK and self.breath:
            ch = pygame.mixer.find_channel(True)
            if ch:
                ch.set_volume(0.22 * self.master)
                ch.play(self.breath)

    def play_screech(self):
        if not AUDIO_OK:
            return
        snd = random.choice([s for s in self.screeches if s] or [None])
        if snd:
            ch = pygame.mixer.find_channel(True)
            if ch:
                ch.set_volume(self.master)
                ch.play(snd)

    def update(self, dt, dist_min, game_active=True):
        if not AUDIO_OK:
            return
        if game_active and dist_min < 4.0:
            self.heart_timer -= dt
            if self.heart_timer <= 0:
                self.heart_timer = 0.9 if dist_min > 2 else 0.5
                if self.heartbeat:
                    ch = pygame.mixer.find_channel(True)
                    if ch:
                        ch.set_volume(min(1.0, (4 - dist_min) / 4 + 0.3) * self.master)
                        ch.play(self.heartbeat)
        if game_active and dist_min < 3.0:
            self.growl_timer -= dt
            if self.growl_timer <= 0:
                self.growl_timer = 1.2 + random.uniform(0, 1.0)
                prox = max(0.0, 1.0 - dist_min / 3.0)
                if self.growl:
                    ch = pygame.mixer.find_channel(True)
                    if ch:
                        ch.set_volume(0.55 * prox * self.master)
                        ch.play(self.growl)
        if game_active:
            self.breath_timer -= dt
            if self.breath_timer <= 0:
                self.breath_timer = random.uniform(8, 18)
                self.play_breath()
            self.whisper_timer -= dt
            if self.whisper_timer <= 0:
                self.whisper_timer = random.uniform(20, 40)
                self.play_whisper()
            self.creak_timer -= dt
            if self.creak_timer <= 0:
                self.creak_timer = random.uniform(25, 45)
                self.play_creak()

    def danger_level(self, dist_min):
        if dist_min >= 6:
            return 0.0
        return max(0.0, min(1.0, 1.0 - dist_min / 6.0))


AUDIO = AudioManager()