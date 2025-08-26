# -*- coding: utf-8 -*-
"""
Avatar collections for the Battleship game
"""

# Naval themed avatars
NAVAL_AVATARS = [
    "⚓", "🚢", "⛵", "🛥️", "🚤", "🛳️", "🏴‍☠️", "🧭",
    "🌊", "🐙", "🦈", "🐋", "🐠", "🦀", "⭐", "🌟"
]

# Military themed avatars
MILITARY_AVATARS = [
    "⚔️", "🛡️", "🎖️", "🏆", "👑", "💎", "🔱", "⚡",
    "🔥", "💥", "🎯", "🚀", "✈️", "🛩️", "🎪", "🎭"
]

# Classic symbols
CLASSIC_AVATARS = [
    "♠", "♣", "♦", "♥", "♀", "♂", "♪", "♫",
    "☺", "☻", "☀", "☽", "★", "☆", "♨", "♩"
]

# Ukrainian themed avatars
UKRAINIAN_AVATARS = [
    "🇺🇦", "🌻", "🌾", "🏛️", "🕊️", "💙", "💛", "🔱"
]

# All avatars combined
ALL_AVATARS = NAVAL_AVATARS + MILITARY_AVATARS + CLASSIC_AVATARS + UKRAINIAN_AVATARS

# Bot specific avatars
BOT_AVATARS = [
    "🤖", "👾", "🎮", "💻", "⚙️", "🔧", "⚡", "🧠",
    "👹", "👺", "💀", "☠️", "🎭", "🃏", "🎪", "🎨"
]

def get_avatar_by_rank(rank):
    """Get avatar based on player rank (0-9)"""
    rank_avatars = {
        0: "🔰",  # Новачок
        1: "⚓",  # Матрос
        2: "🎖️", # Старшина
        3: "🏅",  # Боцман
        4: "🎗️", # Лейтенант
        5: "🏆",  # Капітан-лейтенант
        6: "👑",  # Капітан
        7: "⭐",  # Контр-адмірал
        8: "🌟",  # Віце-адмірал
        9: "💎"   # Адмірал
    }
    return rank_avatars.get(rank, "🔰")

def get_random_avatar(category="all"):
    """Get random avatar from specified category"""
    import random
    
    if category == "naval":
        return random.choice(NAVAL_AVATARS)
    elif category == "military":
        return random.choice(MILITARY_AVATARS)
    elif category == "classic":
        return random.choice(CLASSIC_AVATARS)
    elif category == "ukrainian":
        return random.choice(UKRAINIAN_AVATARS)
    elif category == "bot":
        return random.choice(BOT_AVATARS)
    else:
        return random.choice(ALL_AVATARS)
