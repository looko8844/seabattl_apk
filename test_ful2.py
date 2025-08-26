# -*- coding: utf-8 -*-
"""
Seabattle — повна версія з 1p та 2p, налаштуваннями ніків/аватарів, звуками та музикою.
Інтерфейс українською.
Звук: використовує генератор тонів (якщо mixer не ініціалізовано чи файлів немає — програма продовжує працювати).
Файли музики: шукає 'music.mp3' в тій же папці (не обов'язково).
"""
import os, sys, math, random, json, time
from collections import deque
import numpy as np
from PIL import ImageFont, ImageDraw, Image
import pygame
from pygame.locals import *
# Імпорт аватарок з обробкою помилок
try:
    from avatars import ALL_AVATARS, BOT_AVATARS, get_avatar_by_rank, get_random_avatar
except ImportError:
    # Якщо файл avatars.py недоступний, використовуємо вбудовані аватарки
    NAVAL_AVATARS = [
        "⚓", "🚢", "⛵", "🛥️", "🚤", "🛳️", "🏴‍☠️", "🧭",
        "🌊", "🐙", "🦈", "🐋", "🐠", "🦀", "⭐", "🌟"
    ]
    MILITARY_AVATARS = [
        "⚔️", "🛡️", "🎖️", "🏆", "👑", "💎", "🔱", "⚡",
        "🔥", "💥", "🎯", "🚀", "✈️", "🛩️", "🎪", "🎭"
    ]
    CLASSIC_AVATARS = [
        "♠", "♣", "♦", "♥", "♀", "♂", "♪", "♫",
        "☺", "☻", "☀", "☽", "★", "☆", "♨", "♩"
    ]
    UKRAINIAN_AVATARS = [
        "🇺🇦", "🌻", "🌾", "🏛️", "🕊️", "💙", "💛", "🔱"
    ]
    ALL_AVATARS = NAVAL_AVATARS + MILITARY_AVATARS + CLASSIC_AVATARS + UKRAINIAN_AVATARS
    BOT_AVATARS = [
        "🤖", "👾", "🎮", "💻", "⚙️", "🔧", "⚡", "🧠",
        "👹", "👺", "💀", "☠️", "🎭", "🃏", "🎪", "🎨"
    ]
    def get_avatar_by_rank(rank):
        rank_avatars = {0: "🔰", 1: "⚓", 2: "🎖️", 3: "🏅", 4: "🎗️", 
                       5: "🏆", 6: "👑", 7: "⭐", 8: "🌟", 9: "💎"}
        return rank_avatars.get(rank, "🔰")
    def get_random_avatar(category="all"):
        import random
        return random.choice(ALL_AVATARS)


# ---------- Конфіг ----------
WIN_W, WIN_H = 1200, 840
FPS = 60

GRID_SIZE = 10
CELL = 44
MARGIN = 4
TOP_UI_H = 104

FLEET_COUNTS = {4:1, 3:2, 2:3, 1:4}
FLEET_LAYOUT = tuple(sum(([L]*c for L,c in FLEET_COUNTS.items()), []))

# Покращена кольорова палітра
WHITE=(255,255,255); BLACK=(12,12,14); BLUE=(50,100,200); DARK_BLUE=(18,35,85)
GRAY=(140,140,150); LIGHT_GRAY=(210,210,215); YELLOW=(250,230,130)
RED=(220,50,50); GREEN=(60,190,120); ORANGE=(240,170,60); DIM=(8,8,10)

# Морська тематика
SEA_BLUE=(30,90,150); DEEP_BLUE=(15,45,85); WAVE_BLUE=(45,120,180)
SHIP_GRAY=(120,130,140); SHIP_DARK=(80,85,90); WATER_FOAM=(200,220,240)
EXPLOSION_ORANGE=(255,140,0); FIRE_RED=(255,80,40); SMOKE_GRAY=(100,100,110)

# Кольори для різних типів кораблів
SUBMARINE_COLOR=(60,80,100)  # 1-палубний
DESTROYER_COLOR=(100,120,140)  # 2-палубний  
CRUISER_COLOR=(140,160,180)  # 3-палубний
BATTLESHIP_COLOR=(180,200,220)  # 4-палубний

# AVATARS тепер імпортується з файлу avatars.py

# 10 rank names for rating system
RANKS = [
    "Новачок", "Матрос", "Старшина", "Боцман", "Лейтенант", 
    "Капітан-лейтенант", "Капітан", "Контр-адмірал", "Віце-адмірал", "Адмірал"
]

SETTINGS_FILE = "settings.json"
SCORE_FILE = "score.json"

# ---------- Збереження налаштувань та рахунку ----------
def load_settings():
    base = {
        "player1_name": "Зеленський",
        "player2_name": "Трам",
        "player1_avatar": ALL_AVATARS[0],
        "player2_avatar": ALL_AVATARS[1],
        "bot_name": "Пуйло",
        "bot_avatar": "◊",
        "music_volume": 0.5,
        "sound_volume": 0.6,
        "music": True,
        "sound": True,
        "graphics_3d": True,
        "turn_delay_ms": 650
    }
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k in base:
                if k in data:
                    base[k] = data[k]
    except Exception:
        pass
    return base

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_score():
    base = {"wins":0,"losses":0,"stars":0,"rank":0,"consecutive_losses":0}
    try:
        if os.path.exists(SCORE_FILE):
            with open(SCORE_FILE,"r",encoding="utf-8") as f:
                data = json.load(f)
            for k in base: base[k] = int(data.get(k, base[k]))
    except Exception:
        pass
    return base

def save_score(score):
    try:
        with open(SCORE_FILE,"w",encoding="utf-8") as f:
            json.dump({k:int(score.get(k,0)) for k in ("wins","losses","stars","rank","consecutive_losses")}, f)
    except Exception:
        pass

def update_rating(won, score):
    """Update player rating based on game result"""
    if won:
        score["wins"] += 1
        score["stars"] += 1
        score["consecutive_losses"] = 0  # Reset consecutive losses
        
        # Check for rank promotion (5 stars = rank up)
        if score["stars"] >= 5:
            if score["rank"] < len(RANKS) - 1:
                score["rank"] += 1
                score["stars"] = 0
    else:
        score["losses"] += 1
        score["consecutive_losses"] = score.get("consecutive_losses", 0) + 1
        
        # Lose star only after 2 consecutive losses
        if score["consecutive_losses"] >= 2:
            score["stars"] -= 1
            score["consecutive_losses"] = 0  # Reset counter
            
            # Check for rank demotion (0 stars = rank down)
            if score["stars"] < 0:
                if score["rank"] > 0:
                    score["rank"] -= 1
                    score["stars"] = 4  # Start with 4 stars in lower rank
                else:
                    score["stars"] = 0  # Can't go below 0 stars at lowest rank
    
    # Ensure stars don't go below 0
    score["stars"] = max(0, score["stars"])
    save_score(score)

settings = load_settings()

# ---------- Pygame / Fonts / Utilities ----------
pygame.init()
pygame.font.init()

def _font(size, bold=False):
    try:
        # Шрифти для Android/Pydroid3 з підтримкою емодзі
        fonts_to_try = [
            "NotoColorEmoji", "AndroidEmoji", "DroidSansFallback", 
            "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", 
            "Arial Unicode MS", "DejaVu Sans", "Arial", "sans-serif"
        ]
        for font_name in fonts_to_try:
            try:
                font = pygame.font.SysFont(font_name, size, bold=bold)
                if font:
                    # Тестуємо чи може відобразити емодзі
                    test_surf = font.render("⚓", True, (255,255,255))
                    if test_surf.get_width() > 0:
                        return font
            except Exception:
                continue
        # Резервний варіант
        return pygame.font.Font(None, size)
    except Exception:
        f = pygame.font.Font(None, size)
        try: f.set_bold(bold)
        except Exception: pass
        return f

FONT = _font(22, True)
FONT_L = _font(32, True)
FONT_XL = _font(42, True)
FONT_XXL = _font(72, True)

def draw_text_centered(surface, text, cx, cy, font, color=WHITE):
    surf = font.render(str(text), True, color)
    rect = surf.get_rect(center=(cx,cy))
    surface.blit(surf, rect)

def draw_3d_button(surface, rect, text, pressed=False, font=None, pulse_time=0):
    x,y,w,h = rect
    base=(232,232,240); light=(255,255,255); dark=(110,110,130)
    if pressed: light,dark = dark,light
    
    # Add pulsating effect
    pulse_offset = int(3 * math.sin(pulse_time * 0.01))
    pulse_color = tuple(min(255, max(0, c + pulse_offset)) for c in base)
    
    pygame.draw.rect(surface, pulse_color, (x,y,w,h), border_radius=14)
    pygame.draw.line(surface, light,(x+6,y+6),(x+w-6,y+6),3)
    pygame.draw.line(surface, light,(x+6,y+6),(x+6,y+h-6),3)
    pygame.draw.line(surface, dark, (x+w-6,y+6),(x+w-6,y+h-6),3)
    pygame.draw.line(surface, dark, (x+6,y+h-6),(x+w-6,y+h-6),3)
    if text:
        draw_text_centered(surface, text, x+w//2, y+h//2, font or FONT_L, BLACK)

def draw_panel(surface, rect, title=None):
    x,y,w,h = rect
    pygame.draw.rect(surface, (36,36,48), (x,y,w,h), border_radius=12)
    pygame.draw.line(surface, (255,255,255), (x+6,y+6),(x+w-6,y+6), 2)
    pygame.draw.line(surface, (100,100,120), (x+w-6,y+6),(x+w-6,y+h-6), 2)
    if title:
        draw_text_centered(surface, title, x+w//2, y+20, FONT, YELLOW)

def draw_cell(surface, ox, oy, size, color, bevel=True, highlight=None):
    pygame.draw.rect(surface, color, (ox,oy,size,size), border_radius=6)
    if bevel:
        pygame.draw.line(surface, (255,255,255),(ox,oy),(ox+size,oy),2)
        pygame.draw.line(surface, (255,255,255),(ox,oy),(ox,oy+size),2)
        pygame.draw.line(surface, (140,140,148),(ox+size,oy),(ox+size,oy+size),2)
        pygame.draw.line(surface, (140,140,148),(ox+size,oy+size),(ox,oy+size),2)
    if highlight:
        pygame.draw.rect(surface, highlight, (ox+2,oy+2,size-4,size-4), 3, border_radius=6)

def grid_pixel_size():
    gw = GRID_SIZE*(CELL+MARGIN)-MARGIN
    gh = GRID_SIZE*(CELL+MARGIN)-MARGIN
    return gw, gh

def compute_layout(w, h):
    gw,gh = grid_pixel_size()
    spacing = 40
    if h >= w:
        # portrait: stacked
        px = (w - gw)//2
        py1 = TOP_UI_H + 20
        py2 = py1 + gh + spacing
        return (px,py1), (px,py2), "portrait", spacing
    else:
        # landscape: side by side
        total_w = gw + spacing + gw
        x_start = (w - total_w)//2
        px1 = x_start; px2 = x_start + gw + spacing
        py = TOP_UI_H + 20 + (h - TOP_UI_H - 40 - gh)//2
        return (px1,py), (px2,py), "landscape", spacing

# ---------- Game model ----------
class Ship:
    def __init__(self, coords):
        self.cells = set(coords)
        self.hits = set()
    def length(self): return len(self.cells)
    def orientation(self):
        ys = {y for x,y in self.cells}
        return 'H' if len(ys)==1 else 'V'
    def anchor(self):
        return min(self.cells)
    def moved(self, dx, dy):
        s = Ship({(x+dx, y+dy) for x,y in self.cells}); s.hits = set(self.hits); return s
    def rotated_about_anchor(self):
        ax,ay = self.anchor(); L = self.length()
        if self.orientation() == 'H':
            new = {(ax, ay+i) for i in range(L)}
        else:
            new = {(ax+i, ay) for i in range(L)}
        s = Ship(new); s.hits = set(self.hits); return s
    def surrounds(self):
        s = set()
        for x,y in self.cells:
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    nx,ny = x+dx, y+dy
                    if 0<=nx<GRID_SIZE and 0<=ny<GRID_SIZE: s.add((nx,ny))
        return s - self.cells
    def hit(self,pos):
        if pos in self.cells:
            self.hits.add(pos); return True
        return False
    def sunk(self): return self.cells == self.hits

class Board:
    def __init__(self):
        self.grid = [["empty"]*GRID_SIZE for _ in range(GRID_SIZE)]
        self.ships = []
    def clear(self):
        self.grid = [["empty"]*GRID_SIZE for _ in range(GRID_SIZE)]
        self.ships = []
    def rebuild_grid(self):
        self.grid = [["empty"]*GRID_SIZE for _ in range(GRID_SIZE)]
        for s in self.ships:
            for x,y in s.cells:
                self.grid[y][x] = "ship"
    def in_bounds(self,cells):
        return all(0<=x<GRID_SIZE and 0<=y<GRID_SIZE for x,y in cells)
    def cells_free_with_margin(self,cells, ignore=None):
        occ=set()
        for s in self.ships:
            if s is ignore: continue
            occ |= (s.cells | s.surrounds())
        return all(c not in occ for c in cells)
    def can_place(self,cells,ignore=None):
        return self.in_bounds(cells) and self.cells_free_with_margin(cells, ignore)
    def place_ship(self, coords):
        self.ships.append(Ship(coords))
        self.rebuild_grid()
    def remove_ship(self, ship):
        if ship in self.ships:
            self.ships.remove(ship); self.rebuild_grid()
    def random_fleet(self, layout=FLEET_LAYOUT):
        self.clear(); tries=0
        for L in layout:
            placed=False
            while not placed:
                tries+=1
                if tries>30000:
                    raise RuntimeError("Cannot place fleet")
                orient = random.choice(('H','V'))
                x = random.randrange(GRID_SIZE); y = random.randrange(GRID_SIZE)
                if orient=='H':
                    if x+L>GRID_SIZE: continue
                    coords=[(x+i,y) for i in range(L)]
                else:
                    if y+L>GRID_SIZE: continue
                    coords=[(x,y+i) for i in range(L)]
                if self.can_place(coords):
                    self.place_ship(coords); placed=True
    def shoot(self,x,y):
        cur=self.grid[y][x]
        if cur in ("hit","miss"): return None, None
        if cur=="ship":
            self.grid[y][x]="hit"
            for s in self.ships:
                if (x,y) in s.cells:
                    s.hit((x,y))
                    if s.sunk():
                        # mark surrounding as miss
                        for sx,sy in s.surrounds():
                            if self.grid[sy][sx] == "empty": self.grid[sy][sx] = "miss"
                        return "sunk", s
                    return "hit", s
        else:
            self.grid[y][x] = "miss"
            return "miss", None

    def all_sunk(self):
        return all(s.sunk() for s in self.ships)

# ---------- Bot AI (поліпшений) ----------
class BotAI:
    def __init__(self, difficulty="hard"):
        self.diff = difficulty
        self.reset()
    def reset(self):
        self.moves = set()
        self.queue = deque()
        # parity pattern for efficiency
        self.parity = [(x,y) for y in range(GRID_SIZE) for x in range(GRID_SIZE) if (x+y)%2==0]
        random.shuffle(self.parity)
    def pick_move(self):
        # prefer targets from queue (neighbors after hit)
        while self.queue:
            c = self.queue.popleft()
            if c not in self.moves: 
                self.moves.add(c); return c
        # parity heuristic if hard
        if self.diff == "hard":
            while self.parity:
                c = self.parity.pop()
                if c not in self.moves:
                    self.moves.add(c); return c
        # fallback random
        while True:
            c = (random.randrange(GRID_SIZE), random.randrange(GRID_SIZE))
            if c not in self.moves:
                self.moves.add(c); return c
    def feedback(self, x, y, res):
        if res in ("hit","sunk"):
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx,ny = x+dx, y+dy
                if 0<=nx<GRID_SIZE and 0<=ny<GRID_SIZE and (nx,ny) not in self.moves:
                    self.queue.append((nx,ny))
        if res=="sunk":
            # clear queue if needed
            self.queue.clear()


# ---------- Sound / Music manager (generates tones if no files) ----------
def make_tone(freq, dur, vol=0.5, sweep=None, sr=44100):
    t = np.linspace(0, dur, int(sr*dur), False)
    if sweep:
        f0,f1 = sweep; k = (f1-f0)/dur
        phase = 2*np.pi*(f0*t + 0.5*k*t*t)
        wave = np.sin(phase)
    else:
        wave = np.sin(2*np.pi*freq*t)
    env = np.exp(-5*t)
    audio = (wave * env * vol * 32767).astype(np.int16)
    try:
        mi = pygame.mixer.get_init()
        channels = mi[2] if mi else 1
    except Exception:
        channels = 1
    if channels == 2:
        audio = np.column_stack((audio, audio))
    try:
        return pygame.sndarray.make_sound(audio)
    except Exception:
        return None

class SoundManager:
    def __init__(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(44100, -16, 2, 256)
                pygame.mixer.init()
        except Exception:
            pass
        self.sounds = {}
        self.music = None
        self.music_playing = False
        
        # try to load wav files if present, else generate tones
        try:
            # if user provided wav files in 'sounds/' prefer them
            base_dir = "sounds"
            if os.path.isdir(base_dir):
                def load_opt(name, fname):
                    p = os.path.join(base_dir, fname)
                    if os.path.exists(p):
                        try: self.sounds[name] = pygame.mixer.Sound(p); return
                        except Exception: pass
                    self.sounds[name] = None
                load_opt('click','click.wav'); load_opt('miss','miss.wav')
                load_opt('hit','hit.wav'); load_opt('sunk','sunk.wav')
            # if not present generate tones
            if not self.sounds.get('click'):
                self.sounds['click'] = make_tone(900, 0.03, vol=0.16)
            if not self.sounds.get('miss'):
                self.sounds['miss'] = make_tone(200, 0.4, vol=0.2)
            if not self.sounds.get('hit'):
                self.sounds['hit'] = make_tone(800, 0.15, vol=0.3, sweep=(800,1200))
            if not self.sounds.get('sunk'):
                self.sounds['sunk'] = make_tone(600, 0.6, vol=0.25, sweep=(600,300))
        except Exception:
            pass
        
        # try to load background music
        try:
            if os.path.exists("music.mp3"):
                self.music = "music.mp3"
        except Exception:
            pass
    
    def play(self, name, volume=None):
        if not settings.get("sound", True): return
        s = self.sounds.get(name)
        if s:
            try:
                if volume is not None:
                    s.set_volume(volume * settings.get("sound_volume", 0.6))
                else:
                    s.set_volume(settings.get("sound_volume", 0.6))
                s.play()
            except Exception: pass
    
    def start_music(self):
        if not settings.get("music", True) or not self.music: return
        try:
            if not self.music_playing:
                pygame.mixer.music.load(self.music)
                pygame.mixer.music.set_volume(settings.get("music_volume", 0.5))
                pygame.mixer.music.play(-1)
                self.music_playing = True
        except Exception: pass
    
    def stop_music(self):
        try:
            if self.music_playing:
                pygame.mixer.music.stop()
                self.music_playing = False
        except Exception: pass
    
    def update_music_volume(self):
        if self.music_playing:
            try:
                pygame.mixer.music.set_volume(settings.get("music_volume", 0.5))
            except Exception: pass
    
    def set_music_volume(self, volume):
        settings["music_volume"] = volume
        self.update_music_volume()

sound_mgr = SoundManager()

# ---------- Visual helpers ----------
def get_ship_color(ship_length):
    """Повертає колір корабля залежно від його довжини"""
    colors = {
        1: SUBMARINE_COLOR,
        2: DESTROYER_COLOR, 
        3: CRUISER_COLOR,
        4: BATTLESHIP_COLOR
    }
    return colors.get(ship_length, SHIP_GRAY)

def draw_enhanced_ship_cell(surface, x, y, ship_length, is_horizontal, cell_index, total_cells, is_hit=False, is_sunk=False):
    """Малює покращену клітинку корабля з урахуванням орієнтації та типу"""
    base_color = get_ship_color(ship_length)
    
    if is_sunk:
        base_color = tuple(c//3 for c in base_color)  # затемнюємо потоплений корабель
    elif is_hit:
        base_color = tuple(min(255, c + 50) for c in base_color)  # підсвічуємо поранений
    
    # Основна форма корабля
    if ship_length == 1:
        # Підводний човен - круглий
        pygame.draw.circle(surface, base_color, (x + CELL//2, y + CELL//2), CELL//2 - 2)
        pygame.draw.circle(surface, SHIP_DARK, (x + CELL//2, y + CELL//2), CELL//2 - 2, 2)
    else:
        # Більші кораблі - прямокутні з округленими кінцями
        if is_horizontal:
            if cell_index == 0:  # ніс корабля
                pygame.draw.rect(surface, base_color, (x, y+4, CELL-2, CELL-8), border_radius=8)
                pygame.draw.circle(surface, base_color, (x + CELL//2, y + CELL//2), CELL//2 - 4)
            elif cell_index == total_cells - 1:  # корма
                pygame.draw.rect(surface, base_color, (x+2, y+4, CELL-2, CELL-8), border_radius=8)
                pygame.draw.rect(surface, base_color, (x, y+8, 6, CELL-16))
            else:  # середина
                pygame.draw.rect(surface, base_color, (x, y+4, CELL, CELL-8), border_radius=3)
        else:  # вертикальний
            if cell_index == 0:  # ніс корабля
                pygame.draw.rect(surface, base_color, (x+4, y, CELL-8, CELL-2), border_radius=8)
                pygame.draw.circle(surface, base_color, (x + CELL//2, y + CELL//2), CELL//2 - 4)
            elif cell_index == total_cells - 1:  # корма
                pygame.draw.rect(surface, base_color, (x+4, y+2, CELL-8, CELL-2), border_radius=8)
                pygame.draw.rect(surface, base_color, (x+8, y, CELL-16, 6))
            else:  # середина
                pygame.draw.rect(surface, base_color, (x+4, y, CELL-8, CELL), border_radius=3)
    
    # Додаємо деталі
    if not is_sunk:
        # Іллюмінатори або деталі
        if ship_length > 1:
            detail_color = tuple(min(255, c + 30) for c in base_color)
            if is_horizontal:
                pygame.draw.circle(surface, detail_color, (x + CELL//2, y + CELL//2), 3)
            else:
                pygame.draw.circle(surface, detail_color, (x + CELL//2, y + CELL//2), 3)
    
    # Ефект влучання
    if is_hit and not is_sunk:
        pygame.draw.circle(surface, FIRE_RED, (x + CELL//2, y + CELL//2), 8)
        pygame.draw.circle(surface, YELLOW, (x + CELL//2, y + CELL//2), 4)

def draw_grid_with_board(surface, topleft, board, reveal=False, flashes=None):
    x0,y0 = topleft
    
    # Фон з морською текстурою
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            x = x0 + i*(CELL+MARGIN)
            y = y0 + j*(CELL+MARGIN)
            # Базовий морський фон
            wave_offset = int(5 * math.sin((i + j + pygame.time.get_ticks()/500) * 0.5))
            water_color = (SEA_BLUE[0] + wave_offset, SEA_BLUE[1] + wave_offset//2, SEA_BLUE[2] + wave_offset//3)
            water_color = tuple(max(0, min(255, c)) for c in water_color)
            pygame.draw.rect(surface, water_color, (x,y,CELL,CELL), border_radius=5)
    
    # grid lines
    for i in range(GRID_SIZE+1):
        x = x0 + i*(CELL+MARGIN)
        pygame.draw.line(surface, WAVE_BLUE, (x,y0), (x, y0+GRID_SIZE*(CELL+MARGIN)))
        y = y0 + i*(CELL+MARGIN)
        pygame.draw.line(surface, WAVE_BLUE, (x0,y), (x0+GRID_SIZE*(CELL+MARGIN), y))
    
    # Малюємо кораблі з покращеною графікою
    if reveal and board.ships:
        for ship in board.ships:
            ship_length = len(ship.cells)
            is_horizontal = len(set(cell[1] for cell in ship.cells)) == 1
            is_sunk = ship.sunk()
            
            for idx, (sx, sy) in enumerate(ship.cells):
                x = x0 + sx*(CELL+MARGIN)
                y = y0 + sy*(CELL+MARGIN)
                is_hit = board.grid[sy][sx] == 'hit'
                draw_enhanced_ship_cell(surface, x, y, ship_length, is_horizontal, idx, ship_length, is_hit, is_sunk)
    
    # cells (стани клітинок)
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            x = x0 + i*(CELL+MARGIN)
            y = y0 + j*(CELL+MARGIN)
            cell_state = board.grid[j][i]
            
            if cell_state == 'ship' and reveal:
                pass  # вже намальовано вище
            elif cell_state == 'hit':
                if not reveal:  # якщо не показуємо кораблі, малюємо просто червоний квадрат
                    pygame.draw.rect(surface, FIRE_RED, (x,y,CELL,CELL), border_radius=5)
                    pygame.draw.circle(surface, YELLOW, (x+CELL//2, y+CELL//2), 8)
            elif cell_state == 'miss':
                # Покращений ефект промаху
                pygame.draw.circle(surface, WATER_FOAM, (x+CELL//2, y+CELL//2), 12)
                pygame.draw.circle(surface, WHITE, (x+CELL//2, y+CELL//2), 8)
                pygame.draw.circle(surface, SEA_BLUE, (x+CELL//2, y+CELL//2), 4)
    
    # labels
    for i in range(GRID_SIZE):
        draw_text_centered(surface, str(i+1), x0 + i*(CELL+MARGIN)+CELL//2, y0-14, FONT, WHITE)
        draw_text_centered(surface, chr(ord('A')+i), x0-14, y0 + i*(CELL+MARGIN)+CELL//2, FONT, WHITE)
    
    # flashes
    if flashes:
        for f in list(flashes):
            if f.update(): 
                f.draw(surface)
            else:
                try: flashes.remove(f)
                except Exception: pass

class ShotAnimation:
    def __init__(self, start_x, start_y, end_x, end_y):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.progress = 0.0
        self.speed = 0.15
        self.trail = []
        
    def update(self):
        self.progress += self.speed
        # Add trail points
        current_x = self.start_x + (self.end_x - self.start_x) * self.progress
        current_y = self.start_y + (self.end_y - self.start_y) * self.progress
        self.trail.append((current_x, current_y))
        # Keep trail short
        if len(self.trail) > 8:
            self.trail.pop(0)
        return self.progress < 1.0
    
    def draw(self, surface):
        # Draw projectile trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail)
            size = int(4 * alpha)
            if size > 0:
                color = (255, 255, 0, int(255 * alpha))
                temp = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                pygame.draw.circle(temp, color, (size, size), size)
                surface.blit(temp, (int(tx - size), int(ty - size)))

class HitFlash:
    def __init__(self, x, y, flash_type="hit"):
        self.x = x
        self.y = y
        self.timer = 30
        self.max_timer = 30
        self.flash_type = flash_type
        self.particles = []
        # Створюємо частинки для ефекту
        particle_count = 12 if flash_type == "sunk" else 8
        for _ in range(particle_count):
            angle = random.uniform(0, 2*math.pi)
            speed = random.uniform(3, 8) if flash_type == "sunk" else random.uniform(2, 6)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 25 if flash_type == "sunk" else 20,
                'max_life': 25 if flash_type == "sunk" else 20
            })
    
    def update(self):
        self.timer -= 1
        # Оновлюємо частинки
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.2  # гравітація
            p['life'] -= 1
        self.particles = [p for p in self.particles if p['life'] > 0]
        return self.timer > 0 or len(self.particles) > 0
    
    def draw(self, surface):
        if self.timer <= 0 and not self.particles: return
        
        # Основний вибух з покращеними ефектами
        if self.timer > 0:
            alpha = self.timer / self.max_timer
            rad = int(30 * (1 - alpha)) if self.flash_type == "sunk" else int(25 * (1 - alpha))
            
            if self.flash_type == "sunk":
                color = EXPLOSION_ORANGE
                # Додаткові кільця для потоплення
                for i in range(3):
                    ring_rad = rad + i * 8
                    ring_alpha = max(0, alpha - i * 0.2)
                    if ring_rad > 0 and ring_alpha > 0:
                        temp = pygame.Surface((2*ring_rad, 2*ring_rad), pygame.SRCALPHA)
                        pygame.draw.circle(temp, (*color, int(60*ring_alpha)), (ring_rad, ring_rad), ring_rad, 3)
                        surface.blit(temp, (self.x-ring_rad, self.y-ring_rad))
            elif self.flash_type == "hit":
                color = FIRE_RED
            else:
                color = (100, 150, 255)  # промах
            
            if rad > 0:
                temp = pygame.Surface((2*rad, 2*rad), pygame.SRCALPHA)
                pygame.draw.circle(temp, (*color, int(200*alpha)), (rad, rad), rad)
                pygame.draw.circle(temp, (*WHITE, int(120*alpha)), (rad, rad), rad//2)
                if self.flash_type == "sunk":
                    pygame.draw.circle(temp, (*YELLOW, int(80*alpha)), (rad, rad), rad//3)
                surface.blit(temp, (self.x-rad, self.y-rad))
        
        # Покращені частинки
        for p in self.particles:
            alpha = p['life'] / p['max_life']
            size = max(1, int(4 * alpha)) if self.flash_type == "sunk" else max(1, int(3 * alpha))
            
            if self.flash_type == "sunk":
                # Різнокольорові частинки для потоплення
                colors = [EXPLOSION_ORANGE, FIRE_RED, YELLOW]
                color = random.choice(colors)
            else:
                color = EXPLOSION_ORANGE if self.flash_type == "sunk" else FIRE_RED
            
            # Додаємо ефект згасання
            fade_color = (*color, int(255 * alpha))
            temp = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(temp, fade_color, (size, size), size)
            surface.blit(temp, (int(p['x'] - size), int(p['y'] - size)))

class SinkAnimation:
    def __init__(self, ship_cells):
        self.cells = ship_cells
        self.timer = 60
        self.max_timer = 60
        self.bubbles = []
        # Створюємо бульбашки
        for cell in ship_cells:
            cx = cell[0] * (CELL + MARGIN) + CELL//2
            cy = cell[1] * (CELL + MARGIN) + CELL//2
            for _ in range(3):
                self.bubbles.append({
                    'x': cx + random.randint(-10, 10),
                    'y': cy + random.randint(-10, 10),
                    'vy': random.uniform(-1, -3),
                    'size': random.randint(2, 6),
                    'life': random.randint(40, 80)
                })
    
    def update(self):
        self.timer -= 1
        for b in self.bubbles:
            b['y'] += b['vy']
            b['life'] -= 1
        self.bubbles = [b for b in self.bubbles if b['life'] > 0]
        return self.timer > 0 or len(self.bubbles) > 0
    
    def draw(self, surface, grid_offset):
        gx, gy = grid_offset
        alpha = max(0, self.timer / self.max_timer)
        
        # Затемнюємо корабель
        for cell in self.cells:
            x = gx + cell[0] * (CELL + MARGIN)
            y = gy + cell[1] * (CELL + MARGIN)
            dark_color = (int(SHIP_GRAY[0] * alpha), int(SHIP_GRAY[1] * alpha), int(SHIP_GRAY[2] * alpha))
            pygame.draw.rect(surface, dark_color, (x, y, CELL, CELL), border_radius=5)
        
        # Малюємо бульбашки
        for b in self.bubbles:
            bubble_alpha = b['life'] / 80
            color = (*WATER_FOAM, int(150 * bubble_alpha))
            temp = pygame.Surface((b['size']*2, b['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (b['size'], b['size']), b['size'])
            surface.blit(temp, (gx + b['x'] - b['size'], gy + b['y'] - b['size']))

class Particle:
    def __init__(self, x, y, vx, vy, color, life):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # гравітація
        self.life -= 1
        return self.life > 0
    
    def draw(self, surface):
        alpha = self.life / self.max_life
        size = max(1, int(3 * alpha))
        color = (*self.color, int(255 * alpha))
        temp = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.circle(temp, color, (size, size), size)
        surface.blit(temp, (int(self.x - size), int(self.y - size)))

# ---------- Placement controller ----------
class PlacementControllerPanel:
    def __init__(self, board:Board):
        self.board = board
        self.remaining = dict(FLEET_COUNTS)
        self.held_len = None
        self.top_left_grid = (0,0)
        self.panel_rect = (0,0,0,0)
        self.drag_ship = None
        self.drag_anchor = None
        
    def reset(self):
        self.remaining = dict(FLEET_COUNTS)
        self.held_len = None
        self.board.clear()
    def set_layout_refs(self, top_left, panel_rect):
        self.top_left_grid = top_left
        self.panel_rect = panel_rect
    def _ship_icon_rects(self):
        px,py,pw,ph = self.panel_rect
        items = sorted(FLEET_COUNTS.keys(), reverse=True)
        gap = 18
        icon_w = (pw - gap*(len(items)-1))//len(items)
        rects=[]
        cx = px
        for L in items:
            rects.append(((cx, py, icon_w, ph), L))
            cx += icon_w + gap
        return rects
    def draw_panel(self, surface, font):
        px,py,pw,ph = self.panel_rect
        draw_panel(surface, (px,py,pw,ph), title="Розстановка")
        for (rx,ry,rw,rh), L in self._ship_icon_rects():
            pad = 8
            cell = min((rw - 2*pad)//L - 2, rh - 20)
            cell = max(12, min(cell, 30))
            start_x = rx + (rw - (L*cell + (L-1)*2))//2
            start_y = ry + (rh - cell)//2 - 6
            for i in range(L):
                pygame.draw.rect(surface, (200,170,40), (start_x + i*(cell+2), start_y, cell, cell), border_radius=5)
                pygame.draw.rect(surface, (90,70,20), (start_x + i*(cell+2), start_y, cell, cell), 2, border_radius=5)
            if self.held_len == L:
                pygame.draw.rect(surface, YELLOW, (rx+3, ry+3, rw-6, rh-6), 2, border_radius=8)
            # Remove the text showing ship counts
            # cnt = self.remaining.get(L, 0)
            # draw_text_centered(surface, f"x{cnt}", rx+rw-18, ry+16, font, WHITE)
        # drag preview if dragging ship
        if self.drag_ship and self.drag_anchor:
            mx,my = pygame.mouse.get_pos()
            x0,y0 = self.top_left_grid
            gx = (mx - x0) // (CELL+MARGIN)
            gy = (my - y0) // (CELL+MARGIN)
            dx = gx - self.drag_anchor[0]; dy = gy - self.drag_anchor[1]
            for sx,sy in self.drag_ship.cells:
                nx,ny = sx + dx, sy + dy
                if 0<=nx<GRID_SIZE and 0<=ny<GRID_SIZE:
                    px = x0 + nx*(CELL+MARGIN)
                    py = y0 + ny*(CELL+MARGIN)
                    draw_cell(surface, px, py, CELL, ORANGE)

    def handle_icon_click(self, pos):
        for (r, L) in self._ship_icon_rects():
            x,y,w,h = r
            if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
                if self.remaining.get(L,0) > 0:
                    self.held_len = L
                return True
        # maybe click on existing ship to drag
        cell = self._cell_at(pos)
        if cell:
            for s in self.board.ships:
                if cell in s.cells:
                    self.drag_ship = s
                    self.drag_anchor = min(s.cells)
                    return True
        return False

    def _cell_at(self, pos):
        x0,y0 = self.top_left_grid; mx,my = pos
        if mx < x0 or my < y0: return None
        gx = (mx - x0) // (CELL+MARGIN); gy = (my - y0) // (CELL+MARGIN)
        if 0<=gx<GRID_SIZE and 0<=gy<GRID_SIZE:
            cx = x0 + gx*(CELL+MARGIN); cy = y0 + gy*(CELL+MARGIN)
            if cx<=mx<cx+CELL and cy<=my<cy+CELL:
                return (int(gx), int(gy))
        return None

    def try_place(self, pos):
        if not self.held_len: return False
        cell = self._cell_at(pos)
        if not cell: return False
        ax, ay = cell; L = self.held_len
        cand = [(ax+i, ay) for i in range(L)]
        if not self.board.can_place(cand):
            cand = [(ax, ay+i) for i in range(L)]
            if not self.board.can_place(cand): return False
        self.board.place_ship(cand)
        self.remaining[L] = max(0, self.remaining.get(L,0)-1)
        if self.remaining[L] == 0:
            self.held_len = None
        return True

    def handle_mouse_up(self, pos):
        if self.drag_ship:
            cell = self._cell_at(pos)
            if cell:
                dx = cell[0] - self.drag_anchor[0]
                dy = cell[1] - self.drag_anchor[1]
                new_cells = set((x+dx, y+dy) for x,y in self.drag_ship.cells)
                if self.board.can_place(new_cells, ignore=self.drag_ship):
                    self.drag_ship.cells = new_cells
                    self.board.rebuild_grid()
            self.drag_ship = None
            self.drag_anchor = None

    def handle_double_click(self, pos):
        cell = self._cell_at(pos)
        if not cell: return
        for s in self.board.ships:
            if cell in s.cells:
                rotated = s.rotated_about_anchor()
                if self.board.can_place(rotated.cells, ignore=s):
                    s.cells = rotated.cells
                    self.board.rebuild_grid()
                break

    def auto_fix_after_random(self):
        # compute how many ships placed and reduce counts
        counts = {L:0 for L in FLEET_COUNTS}
        for s in self.board.ships:
            counts[len(s.cells)] = counts.get(len(s.cells),0) + 1
        for L, total in FLEET_COUNTS.items():
            self.remaining[L] = max(0, total - counts.get(L,0))


# ---------- UI helpers ----------
def draw_stars_row(surface, cx, y, filled, total, font):
    texts = []
    for i in range(total):
        texts.append("*" if i<filled else "-")
    text = " ".join(texts)
    draw_text_centered(surface, text, cx, y, font, YELLOW)

def draw_counters(screen, cx, cy, font, nick1, nick2):
    """Draw ship counters for both players"""
    # This function will be called from the game states that have access to ship counts
    pass

def draw_player_rank(surface, x, y, score, font):
    """Draw player rank and stars"""
    rank_name = RANKS[min(score.get('rank', 0), len(RANKS)-1)]
    stars = score.get('stars', 0)
    
    # Draw rank with larger font
    draw_text_centered(surface, f"Ранг: {rank_name}", x, y, FONT_L, YELLOW)
    
    # Draw stars with spacing and larger font
    star_text = " ".join(["*" if i < stars else "-" for i in range(5)])
    draw_text_centered(surface, star_text, x, y + 35, FONT_L, YELLOW)

# ---------- Game manager (включно з 2p логікою) ----------
class GameFull:
    def __init__(self, screen):
        self.screen = screen
        self.state = "menu"  # menu, new_game_menu, placement_1p, difficulty, play_1p, placement_2p_p1, wait_p2, placement_2p_p2, wait_p1b, play_2p, 2p_miss, 2p_victory, settings, victory, rating
        self.clock = pygame.time.Clock()
        self.running = True

        # boards
        self.player = Board(); self.enemy = Board(); self.player2 = Board()
        self.placement = PlacementControllerPanel(self.player)
        self.placement2 = PlacementControllerPanel(self.player2)

        # bot
        self.bot = BotAI("hard")

        # sound
        self.sounds = SoundManager()
        if settings.get("music", True):
            self.sounds.start_music()  # tries to play music.mp3 if present

        # score
        self.score = load_score()

        # UI rects
        self.menu_buttons = []
        self.new_game_buttons = []

        # placement buttons
        self.placement1p_btns = []
        self.placement2p_btns = []

        # game state
        self.turn = "player"  # for 1p
        self.turn2p = "p1"    # for 2p
        self._2p_winner = None
        self.game_in_progress = False
        self.paused_state = None

        # for flashes/effects and animations
        self.flashes = []
        self.sink_animations = []
        self.particles = []
        self.transition_alpha = 0
        self.transition_target = 0
        self.shot_animations = []
        self.button_pulse_time = 0
        self.screen_shake = {'x': 0, 'y': 0, 'intensity': 0, 'duration': 0}

        # settings editing
        self.input_active = None
        self.input_text1 = settings.get("player1_name", "Зеленський")
        self.input_text2 = settings.get("player2_name", "Трам")
        self.nick1 = settings.get("player1_name", "Зеленський")
        self.nick2 = settings.get("player2_name", "Трам")
        self.avatar1 = settings.get("player1_avatar", ALL_AVATARS[0])
        self.avatar2 = settings.get("player2_avatar", ALL_AVATARS[1])

        # double click detection
        self.last_click_time = 0
        self.DOUBLE_CLICK_MS = 340

        # buttons references
        self._btn_wait = None
        self._btn_battle = None
        self._btn_victory = None

    # --- draw functions ---
    def draw_main_menu(self):
        self.screen.fill(DARK_BLUE)
        w,h = self.screen.get_size()
        
        # Apply screen shake if active
        shake_x, shake_y = self.apply_screen_shake()
        
        # Title with gradient effect
        title_y = h//2 - 160 + shake_y
        draw_text_centered(self.screen, "МОРСЬКИЙ БІЙ", w//2 + shake_x, title_y, FONT_XXL, YELLOW)
        
        bw,bh = 320,64; cx=w//2; start_y = h//2 - 40
        
        # Add "Return to Game" button if game is in progress
        labels = []
        if self.game_in_progress:
            labels.append(("Повернутись до гри","resume_game"))
        labels.extend([("Нова гра","new_game"), ("Рейтинг","rating"), ("Налаштування","settings"), ("Вихід","exit")])
        
        self.menu_buttons = []
        gap = 18
        for i,(lab,tag) in enumerate(labels):
            r = (cx - bw//2 + shake_x, start_y + i*(bh+gap) + shake_y, bw, bh)
            draw_3d_button(self.screen, r, lab, font=FONT_L, pulse_time=self.button_pulse_time)
            self.menu_buttons.append((r, tag))
        
        # Draw current player rank at top center
        draw_player_rank(self.screen, w//2 + shake_x, 60 + shake_y, self.score, FONT)

    def draw_new_game_menu(self):
        self.screen.fill(DARK_BLUE)
        w,h = self.screen.get_size()
        
        shake_x, shake_y = self.apply_screen_shake()
        
        draw_text_centered(self.screen, "НОВА ГРА", w//2 + shake_x, h//2 - 200 + shake_y, FONT_XL, YELLOW)
        bw,bh = 320,64; cx=w//2; start_y = h//2 - 40
        labels = [("Один гравець","one"), ("Два гравці","two"), ("Назад","back")]
        self.new_game_buttons = []
        gap=18
        for i,(lab,tag) in enumerate(labels):
            r = (cx - bw//2 + shake_x, start_y + i*(bh+gap) + shake_y, bw, bh)
            draw_3d_button(self.screen, r, lab, font=FONT_L, pulse_time=self.button_pulse_time)
            self.new_game_buttons.append((r, tag))

    def draw_placement_1p(self):
        self.screen.fill(DARK_BLUE)
        w,h = self.screen.get_size()
        draw_text_centered(self.screen, f"Розставте кораблі ({self.nick1})", w//2, 40, FONT_XL, YELLOW)
        gw,gh = grid_pixel_size()
        # Center the grid properly
        px = w//2 - gw//2
        py = h//2 - gh//2 + 40
        # player grid
        draw_text_centered(self.screen, f"{self.nick1} {self.avatar1}", px + gw//2, py - 36, FONT_L, WHITE)
        draw_grid_with_board(self.screen, (px,py), self.player, reveal=True)
        
        # panel - adjust position based on layout
        (p1,p2,orient,spacing) = compute_layout(w,h)
        if orient == "portrait":
            # Place panel below the grid in portrait mode
            panel_w = gw
            panel_h = 100
            panel_x = px
            panel_y = py + gh + 20
        else:
            # Keep panel to the right in landscape mode
            panel_w = min(w - (px + gw) - 60, gw)
            panel_h = 100
            panel_x = px + gw + 40
            panel_y = py + gh - panel_h
        self.placement.set_layout_refs((px,py), (panel_x,panel_y,panel_w,panel_h))
        self.placement.draw_panel(self.screen, FONT)
        # bottom buttons
        bw,bh = 160,52; cx=w//2; y=h - 90
        btns = [("Назад","back"), ("Авто","auto"), ("Грати","play")]
        self.placement1p_btns = []
        for i,(lab,tag) in enumerate(btns):
            r = (cx - (len(btns)*(bw+12))//2 + i*(bw+12), y, bw, bh)
            draw_3d_button(self.screen, r, lab, font=FONT_L, pulse_time=self.button_pulse_time)
            self.placement1p_btns.append((r, tag))
        # counters
        curx = 80
        for L in sorted(FLEET_COUNTS.keys(), reverse=True):
            cnt = self.placement.remaining.get(L,0)
            draw_text_centered(self.screen, f"{L}-пал: x{cnt}", curx, h - 150, FONT, WHITE)
            curx += 140

    def draw_difficulty_menu(self):
        self.screen.fill(DARK_BLUE)
        w,h = self.screen.get_size()
        draw_text_centered(self.screen, "Виберіть складність", w//2, h//2 - 200, FONT_XL, YELLOW)
        bw,bh = 220,62; cx=w//2; start_y=h//2-40
        options=[("Легко","easy"),("Середній","medium"),("Профі","hard")]
        self.difficulty_buttons = []
        for i,(lab,tag) in enumerate(options):
            r = (cx - bw//2, start_y + i*(bh+18), bw, bh)
            draw_3d_button(self.screen, r, lab, font=FONT_L, pulse_time=self.button_pulse_time)
            self.difficulty_buttons.append((r, tag))

    def draw_play_1p(self):
        self.screen.fill(DARK_BLUE)
        w,h = self.screen.get_size()
        (p1,p2,orient,spacing) = compute_layout(w,h)
        
        # Draw rank and stars at top center
        draw_player_rank(self.screen, w//2, 20, self.score, FONT)
        
        # Current player with more spacing
        current_player = self.nick1 if self.turn=="player" else settings.get('bot_name', 'Пуйло')
        draw_text_centered(self.screen, f"Хід: {current_player}", w//2, 100, FONT_XL, YELLOW)
        
        # Ship counters with more spacing
        player_sunk = sum(1 for s in self.player.ships if s.sunk())
        enemy_sunk = sum(1 for s in self.enemy.ships if s.sunk())
        bot_name = settings.get('bot_name', 'Пуйло')
        draw_text_centered(self.screen, f"{self.nick1}: {player_sunk}/10", w//2 - 100, 130, FONT_L, WHITE)
        draw_text_centered(self.screen, f"{bot_name}: {enemy_sunk}/10", w//2 + 100, 130, FONT_L, WHITE)
        
        # Adjust grid positions to be lower
        p1 = (p1[0], p1[1] + 60)
        p2 = (p2[0], p2[1] + 60)
        
        draw_grid_with_board(self.screen, p1, self.player, reveal=True, flashes=self.flashes)
        draw_grid_with_board(self.screen, p2, self.enemy, reveal=False, flashes=None)
        
        # Menu button at bottom center
        menu_btn = (w//2 - 80, h - 60, 160, 40)
        draw_3d_button(self.screen, menu_btn, "Меню", font=FONT_L, pulse_time=self.button_pulse_time)
        self._menu_btn = menu_btn
        
        # Music toggle button at bottom right
        music_btn = (w - 60, h - 60, 50, 50)
        music_icon = "♪" if settings.get("music", True) else "♫"
        draw_3d_button(self.screen, music_btn, music_icon, font=FONT_L, pulse_time=self.button_pulse_time)
        self._music_btn = music_btn

    def draw_placement_2p(self, player_num):
        self.screen.fill(DARK_BLUE)
        w,h = self.screen.get_size()
        player_name = self.nick1 if player_num == 1 else self.nick2
        draw_text_centered(self.screen, f"Розстановка — {player_name}", w//2, 40, FONT_XL, YELLOW)
        (p1,p2,orient,spacing) = compute_layout(w,h)
        if player_num == 1:
            draw_text_centered(self.screen, f"{self.nick1} {self.avatar1}", p1[0] + grid_pixel_size()[0]//2, p1[1] - 36, FONT_L, WHITE)
            draw_grid_with_board(self.screen, p1, self.player, reveal=True)
            # Adjust panel position based on layout
            if orient == "portrait":
                panel_w = grid_pixel_size()[0]
                panel_h = 100
                panel_x = p1[0]
                panel_y = p1[1] + grid_pixel_size()[1] + 20
            else:
                panel_w = min(w - (p1[0] + grid_pixel_size()[0]) - 60, grid_pixel_size()[0])
                panel_h = 100
                panel_x = p1[0] + grid_pixel_size()[0] + 40
                panel_y = p1[1] + grid_pixel_size()[1] - panel_h
            self.placement.set_layout_refs(p1, (panel_x,panel_y,panel_w,panel_h))
            self.placement.draw_panel(self.screen, FONT)
            bw,bh = 160,52; cx=w//2; y=h-90
            btns = [("Назад","back"), ("Авто","auto1"), ("Готово","play1")]
            self.placement2p_btns = []
            for i,(lab,tag) in enumerate(btns):
                r = (cx - (len(btns)*(bw+12))//2 + i*(bw+12), y, bw, bh)
                draw_3d_button(self.screen, r, lab, font=FONT_L, pulse_time=self.button_pulse_time)
                self.placement2p_btns.append((r, tag))
        else:
            draw_text_centered(self.screen, f"{self.nick2} {self.avatar2}", p2[0] + grid_pixel_size()[0]//2, p2[1] - 36, FONT_L, WHITE)
            draw_grid_with_board(self.screen, p2, self.player2, reveal=True)
            # Adjust panel position based on layout
            if orient == "portrait":
                panel_w = grid_pixel_size()[0]
                panel_h = 100
                panel_x = p2[0]
                panel_y = p2[1] + grid_pixel_size()[1] + 20
            else:
                panel_w = min(p2[0]-60, grid_pixel_size()[0])
                panel_h = 100
                panel_x = max(30, p2[0]-panel_w-20)
                panel_y = p2[1] + grid_pixel_size()[1] - panel_h
            self.placement2.set_layout_refs(p2, (panel_x,panel_y,panel_w,panel_h))
            self.placement2.draw_panel(self.screen, FONT)
            bw,bh = 160,52; cx=w//2; y=h-90
            btns = [("Назад","back"), ("Авто","auto2"), ("Готово","play2")]
            self.placement2p_btns = []
            for i,(lab,tag) in enumerate(btns):
                r = (cx - (len(btns)*(bw+12))//2 + i*(bw+12), y, bw, bh)
                draw_3d_button(self.screen, r, lab, font=FONT_L, pulse_time=self.button_pulse_time)
                self.placement2p_btns.append((r, tag))

    def draw_wait_screen(self, text, button_label="Готово"):
        self.screen.fill(DIM)
        w,h = self.screen.get_size()
        draw_text_centered(self.screen, text, w//2, h//2 - 40, FONT_XXL, YELLOW)
        bw,bh = 240,64
        r = (w//2 - bw//2, h//2 + 40, bw, bh)
        draw_3d_button(self.screen, r, button_label, font=FONT_L, pulse_time=self.button_pulse_time)
        self._btn_wait = r

    def draw_play_2p(self):
        self.screen.fill(DARK_BLUE)
        w,h = self.screen.get_size()
        p1,p2,orient,spacing = compute_layout(w,h)
        
        # Current player with more spacing
        current_player = self.nick1 if self.turn2p=='p1' else self.nick2
        draw_text_centered(self.screen, f"Хід: {current_player}", w//2, 50, FONT_XL, YELLOW)
        
        # Ship counters
        p1_sunk = sum(1 for s in self.player.ships if s.sunk())
        p2_sunk = sum(1 for s in self.player2.ships if s.sunk())
        draw_text_centered(self.screen, f"{self.nick1}: {p1_sunk}/10", w//2 - 100, 80, FONT_L, WHITE)
        draw_text_centered(self.screen, f"{self.nick2}: {p2_sunk}/10", w//2 + 100, 80, FONT_L, WHITE)
        
        # Adjust grid positions to be lower
        p1 = (p1[0], p1[1] + 60)
        p2 = (p2[0], p2[1] + 60)
        
        # If it's p1's turn, show p1's ships and p2's closed board to shoot on, and vice versa.
        if self.turn2p == "p1":
            draw_grid_with_board(self.screen, p1, self.player, reveal=True)
            draw_grid_with_board(self.screen, p2, self.player2, reveal=False)
        else:
            draw_grid_with_board(self.screen, p1, self.player, reveal=False)
            draw_grid_with_board(self.screen, p2, self.player2, reveal=True)
        
        # Menu button at bottom center
        menu_btn = (w//2 - 80, h - 60, 160, 40)
        draw_3d_button(self.screen, menu_btn, "Меню", font=FONT_L, pulse_time=self.button_pulse_time)
        self._menu_btn = menu_btn
        
        # Music toggle button at bottom right
        music_btn = (w - 60, h - 60, 50, 50)
        music_icon = "♪" if settings.get("music", True) else "♫"
        draw_3d_button(self.screen, music_btn, music_icon, font=FONT_L, pulse_time=self.button_pulse_time)
        self._music_btn = music_btn

    def draw_2p_miss(self, shooter_nick):
        self.screen.fill(DIM)
        w,h = self.screen.get_size()
        draw_text_centered(self.screen, "Промах", w//2, h//2 - 120, FONT_XXL, YELLOW)
        next_player = self.nick2 if shooter_nick == self.nick1 else self.nick1
        draw_text_centered(self.screen, f"Хід переходить до: {next_player}", w//2, h//2 - 40, FONT_XL, WHITE)
        bw,bh = 240,64
        r = (w//2 - bw//2, h//2 + 40, bw, bh)
        draw_3d_button(self.screen, r, "В бій", font=FONT_L, pulse_time=self.button_pulse_time)
        self._btn_battle = r

    def draw_victory(self, winner_name):
        self.screen.fill(DARK_BLUE)
        w,h = self.screen.get_size()
        
        # Draw game boards first (in background)
        p1,p2,orient,spacing = compute_layout(w,h)
        draw_grid_with_board(self.screen, p1, self.player, reveal=True)
        draw_grid_with_board(self.screen, p2, self.enemy if self.state=="victory" else self.player2, reveal=True)
        
        # Draw victory text over the game boards
        # Create semi-transparent overlay for better text visibility
        overlay = pygame.Surface((w, h))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Draw victory text on top
        draw_text_centered(self.screen, "ПЕРЕМОГА!", w//2, h//2 - 120, FONT_XXL, YELLOW)
        draw_text_centered(self.screen, f"Переміг: {winner_name}", w//2, h//2 - 40, FONT_XL, WHITE)
        
        # Draw button
        bw,bh = 260,64
        r = (w//2 - bw//2, h//2 + 160, bw, bh)
        draw_3d_button(self.screen, r, "В меню", font=FONT_L, pulse_time=self.button_pulse_time)
        self._btn_victory = r

    def draw_settings(self):
        self.screen.fill(DARK_BLUE)
        w,h = self.screen.get_size()
        draw_text_centered(self.screen, "НАЛАШТУВАННЯ", w//2, 60, FONT_XL, YELLOW)
        # toggles
        bx = w//2 - 180; by = 120; bw=360; bh=50; gap=14
        opts = [("sound","Звук"), ("music","Музика"), ("graphics_3d","3D графіка")]
        for i,(k,label) in enumerate(opts):
            r = (bx, by + i*(bh+gap), bw, bh)
            draw_3d_button(self.screen, r, f"{label}: {'ON' if settings.get(k) else 'OFF'}", font=FONT, pulse_time=self.button_pulse_time)
            if k=="sound": self._r_sound = r
            if k=="music": self._r_music = r
            if k=="graphics_3d": self._r_g3d = r
        # sliders
        sx = w//2 - 240; sw = 480; sh = 24
        if not hasattr(self, "slider_music") or self.slider_music is None:
            self.slider_music = Slider((sx, by+3*(bh+gap)+40, sw, sh), settings.get("music_volume",0.5))
        if not hasattr(self, "slider_sound") or self.slider_sound is None:
            self.slider_sound = Slider((sx, by+3*(bh+gap)+100, sw, sh), settings.get("sound_volume",0.6))
        
        # Update slider values from settings
        self.slider_music.value = settings.get("music_volume", 0.5)
        self.slider_sound.value = settings.get("sound_volume", 0.6)
        
        self.slider_music.draw(self.screen, "Гучність музики", FONT)
        self.slider_sound.draw(self.screen, "Гучність звуків", FONT)
        # nickname inputs with labels
        nx = bx; ny = by + 3*(bh+gap) + 160; nbw=400; nbh=56
        
        # Player 1 label and input
        draw_text_centered(self.screen, "Гравець 1:", nx + nbw//2, ny - 20, FONT, WHITE)
        self._input1 = pygame.Rect(nx, ny, nbw, nbh)
        input_color = (80,80,100) if self.input_active == "p1" else (48,48,64)
        pygame.draw.rect(self.screen, input_color, self._input1, border_radius=8)
        # Render avatar and text separately for better control
        avatar1_surf = _font(28, False).render(self.avatar1, True, WHITE)
        text1_surf = FONT_L.render(self.input_text1, True, WHITE)
        # Position avatar and text
        avatar1_x = nx + 20
        text1_x = avatar1_x + 40
        self.screen.blit(avatar1_surf, (avatar1_x, ny + nbh//2 - avatar1_surf.get_height()//2))
        self.screen.blit(text1_surf, (text1_x, ny + nbh//2 - text1_surf.get_height()//2))
        
        # Player 2 label and input
        draw_text_centered(self.screen, "Гравець 2:", nx + nbw//2, ny + 72 - 20, FONT, WHITE)
        self._input2 = pygame.Rect(nx, ny + 72, nbw, nbh)
        input_color2 = (80,80,100) if self.input_active == "p2" else (48,48,64)
        pygame.draw.rect(self.screen, input_color2, self._input2, border_radius=8)
        
        # Render avatar and text for player 2
        avatar2_surf = _font(28, False).render(self.avatar2, True, WHITE)
        text2_surf = FONT_L.render(self.input_text2, True, WHITE)
        avatar2_x = nx + 20
        text2_x = avatar2_x + 40
        self.screen.blit(avatar2_surf, (avatar2_x, ny + 72 + nbh//2 - avatar2_surf.get_height()//2))
        self.screen.blit(text2_surf, (text2_x, ny + 72 + nbh//2 - text2_surf.get_height()//2))
        # avatars
        ax = nx; ay = ny + 72 + 72 + 16
        self._avatar_rect = getattr(self, "_avatar_rect", {})
        if "avatars" not in self._avatar_rect:
            self._avatar_rect["avatars"] = []
        else:
            self._avatar_rect["avatars"].clear()  # Clear previous avatars
        
        for i,a in enumerate(ALL_AVATARS):
            r = (ax + i*60, ay, 56, 56)
            # Highlight selected avatars
            if a == self.avatar1 or a == self.avatar2:
                pygame.draw.rect(self.screen, YELLOW, (r[0]-2, r[1]-2, r[2]+4, r[3]+4), border_radius=10)
            pygame.draw.rect(self.screen, (40,40,50), r, border_radius=8)
            
            # Try to render emoji with better font handling
            try:
                # Use a larger font for better emoji rendering
                emoji_font = _font(40, False)
                emoji_surf = emoji_font.render(a, True, WHITE)
                emoji_rect = emoji_surf.get_rect(center=(r[0]+r[2]//2, r[1]+r[3]//2))
                self.screen.blit(emoji_surf, emoji_rect)
            except Exception:
                # Fallback to regular text rendering
                draw_text_centered(self.screen, a, r[0]+r[2]//2, r[1]+r[3]//2, FONT_L, WHITE)
            
            self._avatar_rect["avatars"].append((r,a))
        # back/save
        back = (w - 240 - 40, h - 90, 240, 56)
        draw_3d_button(self.screen, back, "ЗБЕРЕГТИ ТА НАЗАД", font=FONT_L, pulse_time=self.button_pulse_time)
        self._r_back = back

    def draw_rating(self):
        self.screen.fill(DARK_BLUE)
        w,h = self.screen.get_size()
        draw_text_centered(self.screen, "РЕЙТИНГ", w//2, 60, FONT_XL, YELLOW)
        
        # Player stats panel
        panel_w, panel_h = 600, 400
        panel_x = (w - panel_w) // 2
        panel_y = 120
        draw_panel(self.screen, (panel_x, panel_y, panel_w, panel_h), "Ваша статистика")
        
        # Current player info
        cy = panel_y + 60
        player_name = settings.get("player1_name", "Гравець")
        avatar = settings.get("player1_avatar", ALL_AVATARS[0])
        
        # Player name and avatar
        draw_text_centered(self.screen, f"{avatar} {player_name}", w//2, cy, FONT_XL, WHITE)
        
        # Rank and stars
        cy += 60
        rank_name = RANKS[min(self.score.get('rank', 0), len(RANKS)-1)]
        draw_text_centered(self.screen, f"Ранг: {rank_name}", w//2, cy, FONT_L, YELLOW)
        
        cy += 40
        stars = self.score.get('stars', 0)
        star_text = "*" * stars + "-" * (5 - stars)
        draw_text_centered(self.screen, star_text, w//2, cy, FONT_L, YELLOW)
        draw_text_centered(self.screen, f"{stars}/5 зірок до наступного рангу", w//2, cy + 25, FONT, WHITE)
        
        # Statistics
        cy += 80
        wins = self.score.get('wins', 0)
        losses = self.score.get('losses', 0)
        total_games = wins + losses
        win_rate = (wins / total_games * 100) if total_games > 0 else 0
        
        draw_text_centered(self.screen, f"Перемог: {wins}", w//2 - 100, cy, FONT, GREEN)
        draw_text_centered(self.screen, f"Програшів: {losses}", w//2 + 100, cy, FONT, RED)
        
        cy += 30
        draw_text_centered(self.screen, f"Відсоток перемог: {win_rate:.1f}%", w//2, cy, FONT, WHITE)
        
        # Rank progression info
        cy += 60
        if self.score.get('rank', 0) < len(RANKS) - 1:
            next_rank = RANKS[self.score.get('rank', 0) + 1]
            draw_text_centered(self.screen, f"Наступний ранг: {next_rank}", w//2, cy, FONT, LIGHT_GRAY)
        else:
            draw_text_centered(self.screen, "Максимальний ранг досягнуто!", w//2, cy, FONT, YELLOW)
        
        # Back button
        back_btn = (w//2 - 100, h - 80, 200, 50)
        draw_3d_button(self.screen, back_btn, "НАЗАД", font=FONT_L, pulse_time=self.button_pulse_time)
        self._rating_back = back_btn

    # --- event handlers ---
    def handle_main_menu_click(self, pos):
        for r, tag in self.menu_buttons:
            x,y,w,h = r
            if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
                if tag=="new_game":
                    self.state = "new_game_menu"; self.sounds.play('click')
                elif tag=="settings":
                    self.state = "settings"; self.sounds.play('click')
                elif tag=="rating":
                    self.state = "rating"; self.sounds.play('click')
                elif tag=="resume_game":
                    if self.paused_state:
                        self.state = self.paused_state; self.sounds.play('click')
                elif tag=="exit":
                    pygame.event.post(pygame.event.Event(QUIT))

    def handle_new_game_click(self, pos):
        for r, tag in self.new_game_buttons:
            x,y,w,h = r
            if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
                if tag=="one":
                    # reset boards and placement
                    self.player = Board(); self.enemy = Board()
                    self.placement = PlacementControllerPanel(self.player)
                    self.game_in_progress = False
                    self.paused_state = None
                    self.state = "placement_1p"
                    self.sounds.play('click')
                elif tag=="two":
                    self.player = Board(); self.player2 = Board()
                    self.placement = PlacementControllerPanel(self.player)
                    self.placement2 = PlacementControllerPanel(self.player2)
                    self.game_in_progress = False
                    self.paused_state = None
                    self.state = "placement_2p_p1"
                    self.sounds.play('click')
                elif tag=="back":
                    self.state = "menu"; self.sounds.play('click')
        return

    def handle_placement_1p_click(self, pos):
        now = pygame.time.get_ticks()
        if now - self.last_click_time < self.DOUBLE_CLICK_MS:
            self.placement.handle_double_click(pos)
        else:
            if self.placement.handle_icon_click(pos):
                self.sounds.play('click'); pass
            elif self.placement.try_place(pos):
                self.sounds.play('click')
            else:
                for r, tag in self.placement1p_btns:
                    x,y,w,h = r
                    if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
                        if tag=="back":
                            self.state = "new_game_menu"; self.sounds.play('click')
                        elif tag=="auto":
                            self.player.random_fleet(FLEET_LAYOUT)
                            self.placement = PlacementControllerPanel(self.player)
                            self.placement.auto_fix_after_random()
                            self.sounds.play('click')
                        elif tag=="play":
                            if sum(self.placement.remaining.values()) == 0:
                                # go to difficulty menu
                                self.state = "difficulty"; self.sounds.play('click')
                            else:
                                self.sounds.play('miss')
                        return
        self.last_click_time = now

    def handle_difficulty_click(self, pos):
        for r, tag in self.difficulty_buttons:
            x,y,w,h = r
            if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
                if tag=="easy": self.bot = BotAI("easy")
                elif tag=="medium": self.bot = BotAI("medium")
                else: self.bot = BotAI("hard")
                # ensure enemy fleet
                if not self.enemy.ships:
                    self.enemy.random_fleet(FLEET_LAYOUT)
                self.turn = "player"
                self.game_in_progress = True
                self.state = "play_1p"
                self.sounds.play('click')
                return

    def handle_play_1p_click(self, pos):
        # clicking enemy board to shoot
        w,h = self.screen.get_size()
        p1,p2,orient,spacing = compute_layout(w,h)
        now = pygame.time.get_ticks()
        if now - getattr(self, "last_turn_change_time", 0) < settings.get("turn_delay_ms", 650): return
        if self.turn != "player": return
        cell = self._cell_at(pos, p2)
        if cell:
            x,y = cell
            res, ship = self.enemy.shoot(x,y)
            if not res: return
            if res=="miss":
                self.sounds.play('miss'); self.turn = "bot"; self.last_turn_change_time = pygame.time.get_ticks()
            elif res=="hit":
                self.sounds.play('hit')
                cx = p2[0] + x*(CELL+MARGIN) + CELL//2; cy = p2[1] + y*(CELL+MARGIN) + CELL//2
                self.flashes.append(HitFlash(cx,cy))
                # Add screen shake for hits
                self.add_screen_shake(3, 10)
            elif res=="sunk":
                self.sounds.play('sunk')
                cx = p2[0] + x*(CELL+MARGIN) + CELL//2; cy = p2[1] + y*(CELL+MARGIN) + CELL//2
                self.flashes.append(HitFlash(cx,cy, "sunk"))
                # Add stronger screen shake for sunk ships
                self.add_screen_shake(8, 20)
            if all(s.sunk() for s in self.enemy.ships):
                # victory
                update_rating(True, self.score)
                self.game_in_progress = False
                self.paused_state = None
                self.state = "victory"; self.win_name = self.nick1
            return

    def handle_bot_turn(self):
        # called by main loop
        x,y = self.bot.pick_move()
        res, ship = self.player.shoot(x,y)
        self.bot.feedback(x,y,res)
        if res == "miss":
            self.sounds.play('miss'); self.turn = "player"; self.last_turn_change_time = pygame.time.get_ticks()
        elif res == "hit":
            self.sounds.play('hit')
            p1 = compute_layout(*self.screen.get_size())[0]
            cx = p1[0] + x*(CELL+MARGIN) + CELL//2; cy = p1[1] + y*(CELL+MARGIN) + CELL//2
            self.flashes.append(HitFlash(cx,cy))
            # Add screen shake for bot hits
            self.add_screen_shake(3, 10)
        elif res == "sunk":
            self.sounds.play('sunk')
            p1 = compute_layout(*self.screen.get_size())[0]
            cx = p1[0] + x*(CELL+MARGIN) + CELL//2; cy = p1[1] + y*(CELL+MARGIN) + CELL//2
            self.flashes.append(HitFlash(cx,cy, "sunk"))
            # Add stronger screen shake for bot sinking ships
            self.add_screen_shake(8, 20)
        if all(s.sunk() for s in self.player.ships):
            update_rating(False, self.score)
            self.game_in_progress = False
            self.paused_state = None
            self.state = "victory"; self.win_name = settings.get('bot_name', 'Пуйло')

    def handle_placement_2p_click(self, pos, player_num):
        now = pygame.time.get_ticks()
        ctrl = self.placement if player_num==1 else self.placement2
        if now - self.last_click_time < self.DOUBLE_CLICK_MS:
            ctrl.handle_double_click(pos)
        else:
            if ctrl.handle_icon_click(pos):
                self.sounds.play('click'); pass
            elif ctrl.try_place(pos):
                self.sounds.play('click')
            else:
                for r, tag in self.placement2p_btns:
                    x,y,w,h = r
                    if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
                        if tag=="back":
                            self.state = "new_game_menu"; self.sounds.play('click')
                        elif tag=="auto1" and player_num==1:
                            self.player.random_fleet(FLEET_LAYOUT)
                            self.placement = PlacementControllerPanel(self.player)
                            self.placement.auto_fix_after_random()
                            self.sounds.play('click')
                        elif tag=="play1":
                            if sum(self.placement.remaining.values())==0:
                                self.state = "wait_p2"; self.sounds.play('click')
                            else:
                                self.sounds.play('miss')
                        elif tag=="auto2" and player_num==2:
                            self.player2.random_fleet(FLEET_LAYOUT)
                            self.placement2 = PlacementControllerPanel(self.player2)
                            self.placement2.auto_fix_after_random()
                            self.sounds.play('click')
                        elif tag=="play2":
                            if sum(self.placement2.remaining.values())==0:
                                # both ready -> go to wait->play
                                self.state = "wait_p1b"; self.sounds.play('click')
                            else:
                                self.sounds.play('miss')
                        return
        self.last_click_time = now

    def handle_wait_click(self, pos, next_state):
        x,y,w,h = self._btn_wait
        if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
            self.state = next_state; self.sounds.play('click')

    def handle_2p_play_click(self, pos):
        # clicking on opponent closed board
        w,h = self.screen.get_size()
        p1,p2,orient,spacing = compute_layout(w,h)
        if self.turn2p == "p1":
            ox,oy = p2; board = self.player2
        else:
            ox,oy = p1; board = self.player
        cell = self._cell_at(pos, (ox,oy))
        if cell:
            x,y = cell
            res, ship = board.shoot(x,y)
            if not res: return
            if res=="miss":
                self.sounds.play('miss'); self.state = "2p_miss"
            elif res=="hit":
                self.sounds.play('hit')
                # flash at center of target cell
                cx = ox + x*(CELL+MARGIN) + CELL//2; cy = oy + y*(CELL+MARGIN) + CELL//2
                self.flashes.append(HitFlash(cx,cy))
                self.add_screen_shake(3, 10)
                if board.all_sunk():
                    # set winner
                    if board is self.player2:
                        self._2p_winner = "p1"
                    else:
                        self._2p_winner = "p2"
                    self.state = "2p_victory"
            elif res=="sunk":
                self.sounds.play('sunk')
                cx = ox + x*(CELL+MARGIN) + CELL//2; cy = oy + y*(CELL+MARGIN) + CELL//2
                self.flashes.append(HitFlash(cx,cy, "sunk"))
                self.add_screen_shake(8, 20)
                if board.all_sunk():
                    if board is self.player2:
                        self._2p_winner = "p1"
                    else:
                        self._2p_winner = "p2"
                    self.state = "2p_victory"
            return

    def handle_2p_miss_click(self, pos):
        x,y,w,h = self._btn_battle
        if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
            # swap turn and resume play
            self.turn2p = "p2" if self.turn2p=="p1" else "p1"
            self.state = "play_2p"
            self.sounds.play('click')

    def handle_2p_victory_click(self, pos):
        x,y,w,h = self._btn_victory
        if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
            self.state = "menu"; self.sounds.play('click')

    def handle_settings_event(self, event):
        # sliders
        if hasattr(self, "slider_music") and self.slider_music:
            self.slider_music.handle(event)
        if hasattr(self, "slider_sound") and self.slider_sound:
            self.slider_sound.handle(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
            mx,my = event.pos
            # toggles
            if hasattr(self,"_r_sound"):
                x,y,w,h = self._r_sound
                if x<=mx<=x+w and y<=my<=y+h:
                    settings["sound"] = not settings.get("sound", True); self.sounds.play('click')
            if hasattr(self,"_r_music"):
                x,y,w,h = self._r_music
                if x<=mx<=x+w and y<=my<=y+h:
                    settings["music"] = not settings.get("music", True); self.sounds.play('click')
                    if settings["music"]:
                        self.sounds.start_music()
                    else:
                        try: pygame.mixer.music.stop()
                        except Exception: pass
            if hasattr(self,"_r_g3d"):
                x,y,w,h = self._r_g3d
                if x<=mx<=x+w and y<=my<=y+h:
                    settings["graphics_3d"] = not settings.get("graphics_3d", True); self.sounds.play('click')
            # Update settings from sliders immediately
            if hasattr(self, "slider_music") and self.slider_music:
                settings["music_volume"] = self.slider_music.value
                self.sounds.update_music_volume()
            if hasattr(self, "slider_sound") and self.slider_sound:
                settings["sound_volume"] = self.slider_sound.value
            
            # nickname inputs
            if hasattr(self, "_input1") and self._input1.collidepoint(event.pos):
                self.input_active = "p1"; self.sounds.play('click')
            elif hasattr(self, "_input2") and self._input2.collidepoint(event.pos):
                self.input_active = "p2"; self.sounds.play('click')
            else:
                # avatars (simple area detection)
                # if user clicks bottom-right "save" button
                if hasattr(self, "_r_back"):
                    x,y,w,h = self._r_back
                    if x<=mx<=x+w and y<=my<=y+h:
                        # save sliders (already updated in real-time above)
                        if hasattr(self, "slider_music") and self.slider_music:
                            settings["music_volume"] = float(self.slider_music.value)
                        if hasattr(self, "slider_sound") and self.slider_sound:
                            settings["sound_volume"] = float(self.slider_sound.value)
                        # save nicknames and avatars
                        settings["player1_name"] = self.input_text1
                        settings["player2_name"] = self.input_text2
                        settings["player1_avatar"] = self.avatar1
                        settings["player2_avatar"] = self.avatar2
                        save_settings(settings)
                        self.nick1 = self.input_text1; self.nick2 = self.input_text2
                        self.avatar1 = settings.get("player1_avatar", self.avatar1)
                        self.avatar2 = settings.get("player2_avatar", self.avatar2)
                        self.input_active = None
                        self.state = "menu"
                        self.sounds.play('click')
            # avatar click detection
            if hasattr(self, "_avatar_rect") and "avatars" in self._avatar_rect:
                for rect,a in self._avatar_rect["avatars"]:
                    rx,ry,rw,rh = rect
                    if rx<=mx<=rx+rw and ry<=my<=ry+rh:
                        # Choose avatar based on active input or click position
                        if self.input_active == "p2":
                            self.avatar2 = a
                            settings["player2_avatar"] = a
                        elif self.input_active == "p1":
                            self.avatar1 = a
                            settings["player1_avatar"] = a
                        else:
                            # If no input active, alternate between players or use a simple rule
                            # For simplicity, let's assign to player 1 by default
                            self.avatar1 = a
                            settings["player1_avatar"] = a
                        self.sounds.play('click')
                        break  # Exit loop after selection

        elif event.type == KEYDOWN:
            if self.input_active == "p1":
                if event.key == K_BACKSPACE:
                    self.input_text1 = self.input_text1[:-1]
                elif event.key == K_RETURN:
                    self.input_active = None
                else:
                    self.input_text1 += event.unicode
            elif self.input_active == "p2":
                if event.key == K_BACKSPACE:
                    self.input_text2 = self.input_text2[:-1]
                elif event.key == K_RETURN:
                    self.input_active = None
                else:
                    self.input_text2 += event.unicode

    # helper: map click pos -> cell within grid anchored at top_left
    @staticmethod
    def _cell_at(pos, top_left):
        x0,y0 = top_left; mx,my = pos
        if mx < x0 or my < y0: return None
        gx = (mx - x0) // (CELL+MARGIN); gy = (my - y0) // (CELL+MARGIN)
        if 0<=gx<GRID_SIZE and 0<=gy<GRID_SIZE:
            cx = x0 + gx*(CELL+MARGIN); cy = y0 + gy*(CELL+MARGIN)
            if cx<=mx<cx+CELL and cy<=my<cy+CELL: return (int(gx), int(gy))
        return None

    def add_screen_shake(self, intensity, duration):
        """Add screen shake effect"""
        self.screen_shake['intensity'] = intensity
        self.screen_shake['duration'] = duration
    
    def apply_screen_shake(self):
        """Apply and update screen shake effect"""
        if self.screen_shake['duration'] > 0:
            self.screen_shake['duration'] -= 1
            intensity = self.screen_shake['intensity'] * (self.screen_shake['duration'] / 20)
            shake_x = random.randint(-int(intensity), int(intensity))
            shake_y = random.randint(-int(intensity), int(intensity))
            return shake_x, shake_y
        return 0, 0
    
    def update_animations(self):
        """Update all animations and effects"""
        # Update button pulse
        self.button_pulse_time += 1
        
        # Update shot animations
        self.shot_animations = [anim for anim in self.shot_animations if anim.update()]
        
        # Update flashes
        self.flashes = [flash for flash in self.flashes if flash.update()]
        
        # Update sink animations
        self.sink_animations = [anim for anim in self.sink_animations if anim.update()]
    
    # --- main loop runner ---
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            
            # Update animations
            self.update_animations()
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                elif event.type == KEYDOWN and event.key == K_ESCAPE:
                    if self.state != "menu": self.state = "menu"
                    else: self.running = False
                elif self.state == "settings":
                    self.handle_settings_event(event)
                elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    # route by state
                    if self.state == "menu":
                        self.handle_main_menu_click(pos)
                    elif self.state == "new_game_menu":
                        self.handle_new_game_click(pos)
                    elif self.state == "placement_1p":
                        self.handle_placement_1p_click(pos)
                    elif self.state == "difficulty":
                        self.handle_difficulty_click(pos)
                    elif self.state == "play_1p":
                        # Check menu and music buttons first
                        if hasattr(self, "_menu_btn"):
                            x,y,w,h = self._menu_btn
                            if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
                                try:
                                    self.paused_state = "play_1p"
                                    self.state = "menu"
                                    try:
                                        self.sounds.play('click')
                                    except:
                                        pass  # Ignore sound errors
                                except Exception as e:
                                    print(f"Menu button error: {e}")
                                    self.state = "menu"
                                return
                        if hasattr(self, "_music_btn"):
                            x,y,w,h = self._music_btn
                            if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
                                try:
                                    settings["music"] = not settings.get("music", True)
                                    try:
                                        save_settings(settings)
                                    except:
                                        pass  # Ignore save errors
                                    if settings["music"]:
                                        try:
                                            self.sounds.start_music()
                                        except:
                                            pass  # Ignore music start errors
                                    else:
                                        try: 
                                            pygame.mixer.music.stop()
                                        except: 
                                            pass  # Ignore music stop errors
                                    try:
                                        self.sounds.play('click')
                                    except:
                                        pass  # Ignore sound errors
                                except Exception as e:
                                    print(f"Music toggle error: {e}")
                                    # Fallback - just try to toggle without any other operations
                                    try:
                                        if settings.get("music", True):
                                            pygame.mixer.music.stop()
                                        else:
                                            self.sounds.start_music()
                                    except:
                                        pass
                                return
                        self.handle_play_1p_click(pos)
                    elif self.state == "placement_2p_p1":
                        self.handle_placement_2p_click(pos, 1)
                    elif self.state == "wait_p2":
                        # button to go to placement_2p_p2
                        x,y,w,h = self._btn_wait
                        if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
                            self.state = "placement_2p_p2"; self.sounds.play('click')
                    elif self.state == "placement_2p_p2":
                        self.handle_placement_2p_click(pos, 2)
                    elif self.state == "wait_p1b":
                        x,y,w,h = self._btn_wait
                        if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
                            # after p2 done go to play_2p
                            self.turn2p = "p1"  # p1 starts by default
                            self.game_in_progress = True
                            self.state = "play_2p"; self.sounds.play('click')
                    elif self.state == "play_2p":
                        # Check menu and music buttons first
                        if hasattr(self, "_menu_btn"):
                            x,y,w,h = self._menu_btn
                            if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
                                try:
                                    self.paused_state = "play_2p"
                                    self.state = "menu"
                                    try:
                                        self.sounds.play('click')
                                    except:
                                        pass  # Ignore sound errors
                                except Exception as e:
                                    print(f"Menu button error: {e}")
                                    self.state = "menu"
                                return
                        if hasattr(self, "_music_btn"):
                            x,y,w,h = self._music_btn
                            if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
                                try:
                                    settings["music"] = not settings.get("music", True)
                                    try:
                                        save_settings(settings)
                                    except:
                                        pass  # Ignore save errors
                                    if settings["music"]:
                                        try:
                                            self.sounds.start_music()
                                        except:
                                            pass  # Ignore music start errors
                                    else:
                                        try: 
                                            pygame.mixer.music.stop()
                                        except: 
                                            pass  # Ignore music stop errors
                                    try:
                                        self.sounds.play('click')
                                    except:
                                        pass  # Ignore sound errors
                                except Exception as e:
                                    print(f"Music toggle error: {e}")
                                    # Fallback - just try to toggle without any other operations
                                    try:
                                        if settings.get("music", True):
                                            pygame.mixer.music.stop()
                                        else:
                                            self.sounds.start_music()
                                    except:
                                        pass
                                return
                        self.handle_2p_play_click(pos)
                    elif self.state == "2p_miss":
                        self.handle_2p_miss_click(pos)
                    elif self.state == "2p_victory":
                        self.handle_2p_victory_click(pos)
                    elif self.state == "victory":
                        x,y,w,h = self._btn_victory
                        if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
                            self.state = "menu"; self.sounds.play('click')
                    elif self.state == "rating":
                        if hasattr(self, "_rating_back"):
                            x,y,w,h = self._rating_back
                            if x<=pos[0]<=x+w and y<=pos[1]<=y+h:
                                self.state = "menu"; self.sounds.play('click')
                elif event.type == MOUSEBUTTONUP and event.button==1:
                    pos = event.pos
                    if self.state == "placement_1p":
                        self.placement.handle_mouse_up(pos)
                    elif self.state == "placement_2p_p1":
                        self.placement.handle_mouse_up(pos)
                    elif self.state == "placement_2p_p2":
                        self.placement2.handle_mouse_up(pos)
                elif event.type == MOUSEMOTION:
                    pos = event.pos
                    # no special handling except drag preview included in draw

            # Autonomous bot move (in 1p)
            if self.state == "play_1p" and self.turn == "bot":
                now = pygame.time.get_ticks()
                if now - getattr(self, "last_turn_change_time", 0) >= settings.get("turn_delay_ms", 650):
                    self.handle_bot_turn()

            # Drawing by state
            w,h = self.screen.get_size()
            if self.state == "menu":
                self.draw_main_menu()
            elif self.state == "new_game_menu":
                self.draw_new_game_menu()
            elif self.state == "placement_1p":
                self.draw_placement_1p()
            elif self.state == "difficulty":
                self.draw_difficulty_menu()
            elif self.state == "play_1p":
                self.draw_play_1p()
            elif self.state == "placement_2p_p1":
                self.draw_placement_2p(1)
            elif self.state == "wait_p2":
                self.draw_wait_screen(f"Передати пристрій гравцю {self.nick2}", "Готово")
            elif self.state == "placement_2p_p2":
                self.draw_placement_2p(2)
            elif self.state == "wait_p1b":
                self.draw_wait_screen(f"Передати пристрій гравцю {self.nick1}", "Почати гру")
            elif self.state == "play_2p":
                self.draw_play_2p()
            elif self.state == "2p_miss":
                shooter = self.nick1 if self.turn2p=="p1" else self.nick2
                self.draw_2p_miss(shooter)
            elif self.state == "2p_victory":
                winner = self.nick1 if self._2p_winner=="p1" else self.nick2
                self.draw_victory(winner)
            elif self.state == "settings":
                self.draw_settings()
            elif self.state == "rating":
                self.draw_rating()
            elif self.state == "victory":
                # singleplayer victory handled via state 'victory' earlier
                self.draw_victory(getattr(self,"win_name", self.nick1))
            pygame.display.flip()
        pygame.quit()
        sys.exit()

# ---------- Slider class (used in settings) ----------
class Slider:
    def __init__(self, rect, value=0.5):
        self.rect = rect
        self.value = max(0.0, min(1.0, float(value)))
        self.drag = False
    def hit(self, pos):
        x,y,w,h = self.rect
        return x<=pos[0]<=x+w and y<=pos[1]<=y+h
    def handle(self, event):
        x,y,w,h = self.rect
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and self.hit(event.pos):
            self.drag = True; self._set_value_from_pos(event.pos[0])
        elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
            self.drag = False
        elif event.type==pygame.MOUSEMOTION and self.drag:
            self._set_value_from_pos(event.pos[0])
    def _set_value_from_pos(self, mx):
        x,y,w,h = self.rect
        t = (mx - x) / max(1, w)
        self.value = max(0.0, min(1.0, t))
    def draw(self, surface, label, font):
        x,y,w,h = self.rect
        pygame.draw.rect(surface, (70,70,90), (x,y,w,h), border_radius=10)
        filled = int(w*self.value)
        pygame.draw.rect(surface, (120,180,240), (x,y,filled,h), border_radius=10)
        hx = x + filled
        pygame.draw.rect(surface, (240,240,255), (hx-6, y-4, 12, h+8), border_radius=6)
        draw_text_centered(surface, f"{label}: {int(self.value*100)}%", x+w//2, y+h+16, font, WHITE)

# ---------- Main ----------
def main():
    pygame.init()
    try:
        pygame.display.set_caption("Морський бій — повна версія")
    except Exception:
        pass
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    game = GameFull(screen)
    game.run()

if __name__ == "__main__":
    main()
