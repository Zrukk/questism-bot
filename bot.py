import os
import sqlite3
import random
import html
from datetime import date, timedelta, time, datetime
from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup,
                      BotCommand, LabeledPrice)
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                          ContextTypes, PreCheckoutQueryHandler,
                          MessageHandler, filters)

# ============ SETUP ============
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN belum diset!")
DB = os.environ.get("DB_PATH", "questism.db")

def esc(s): return html.escape(str(s))

# ================== QUEST DB ==================
QUEST_DB = {
    "E": {
        "STR": [("10 Push-up", 60, 2), ("15 Squat", 60, 2),
                ("Plank 30 detik", 55, 2), ("20 Jumping Jack", 50, 2)],
        "AGI": [("Jalan santai 15 menit", 60, 2), ("Stretching 5 menit", 50, 2),
                ("Naik turun tangga 5x", 55, 2)],
        "VIT": [("Minum 1 gelas air", 40, 2), ("Tidur 7 jam", 60, 2),
                ("Makan 1 porsi buah", 55, 2), ("Napas dalam 20x", 40, 2)],
        "INT": [("Baca 5 halaman buku", 60, 2), ("Hafal 3 kosakata", 55, 2),
                ("Tulis 1 kalimat jurnal", 50, 2)],
    },
    "D": {
        "STR": [("25 Push-up", 90, 3), ("40 Squat", 90, 3),
                ("Plank 1 menit", 85, 3), ("50 Jumping Jack", 85, 3)],
        "AGI": [("Jalan cepat 20 menit", 90, 3), ("Stretching 10 menit", 85, 3),
                ("Lompat tali 100x", 90, 3)],
        "VIT": [("Minum 1 liter air", 80, 3), ("Tidur 8 jam", 90, 3),
                ("Meditasi 5 menit", 85, 3), ("Puasa gula 1 hari", 100, 3)],
        "INT": [("Baca 15 halaman", 95, 3), ("Hafal 10 kosakata", 90, 3),
                ("Belajar 30 menit", 90, 3)],
    },
    "C": {
        "STR": [("50 Push-up", 150, 4), ("70 Squat", 150, 4),
                ("Plank 2 menit", 140, 4), ("30 Pull-up", 160, 4)],
        "AGI": [("Lari 2 km", 155, 4), ("Sprint 5x50m", 145, 4),
                ("Lompat tali 300x", 150, 4)],
        "VIT": [("Minum 2 liter air", 140, 4), ("Makan sehat 3x", 150, 4),
                ("Meditasi 15 menit", 145, 4), ("Puasa intermiten 12 jam", 160, 4)],
        "INT": [("Baca 30 halaman", 155, 4), ("Hafal 20 kosakata", 145, 4),
                ("Belajar skill baru 1 jam", 160, 4)],
    },
    "B": {
        "STR": [("75 Push-up", 220, 5), ("100 Squat", 220, 5),
                ("Plank 3 menit", 210, 5), ("50 Pull-up", 230, 5),
                ("Angkat beban 30 menit", 225, 5)],
        "AGI": [("Lari 3 km", 220, 5), ("Sprint 10x100m", 220, 5),
                ("Yoga 30 menit", 210, 5)],
        "VIT": [("Tidur 9 jam", 200, 5), ("Puasa gula 3 hari", 240, 5),
                ("Meditasi 30 menit", 220, 5), ("Cold shower", 210, 5)],
        "INT": [("Baca buku 1 jam", 220, 5), ("Hafal 30 kosakata", 215, 5),
                ("Selesaikan mini project", 240, 5), ("Tulis essay 500 kata", 230, 5)],
    },
    "A": {
        "STR": [("100 Push-up", 300, 6), ("150 Squat", 300, 6),
                ("Plank 5 menit", 290, 6), ("80 Pull-up", 320, 6),
                ("Angkat beban 45 menit", 310, 6)],
        "AGI": [("Lari 5 km", 310, 6), ("Sprint 15x100m", 300, 6),
                ("Lompat tali 1000x", 320, 6)],
        "VIT": [("Minum 3 liter air", 290, 6), ("Meditasi 45 menit", 300, 6),
                ("Puasa 16:8", 320, 6)],
        "INT": [("Baca buku 2 jam", 300, 6), ("Tulis artikel panjang", 320, 6),
                ("Hafal 50 kosakata", 310, 6), ("Ajari orang 1 topik", 320, 6)],
    },
    "S": {
        "STR": [("150 Push-up", 420, 8), ("200 Squat", 420, 8),
                ("Plank 10 menit", 400, 8), ("100 Pull-up", 450, 8)],
        "AGI": [("Lari 8 km", 430, 8), ("Sprint 20x100m", 420, 8),
                ("Hill sprint 10x", 450, 8)],
        "VIT": [("Puasa 24 jam", 450, 8), ("Meditasi 1 jam", 420, 8),
                ("Detox 3 hari", 430, 8)],
        "INT": [("Selesai 1 buku/hari", 430, 8), ("Selesaikan proyek coding", 450, 8),
                ("Publikasi tulisan", 440, 8)],
    },
    "SS": {
        "STR": [("200 Push-up", 600, 10), ("300 Squat", 600, 10),
                ("Pistol Squat 50x", 620, 10), ("One Arm Push-up 5x", 650, 10)],
        "AGI": [("Lari 10 km", 610, 10), ("Sprint 30x100m", 600, 10),
                ("Lari bukit 5 km", 630, 10)],
        "VIT": [("Puasa 36 jam", 630, 10), ("Meditasi 1.5 jam", 600, 10),
                ("Detox 5 hari", 620, 10)],
        "INT": [("Selesai 2 buku/hari", 620, 10), ("Proyek kompleks", 640, 10),
                ("Kuasai tool baru", 620, 10)],
    },
    "SSS": {
        "STR": [("300 Push-up", 800, 15), ("500 Squat", 800, 15),
                ("150 Pull-up", 850, 15), ("One Arm Push-up 10x", 900, 15),
                ("Plank 20 menit", 850, 15)],
        "AGI": [("Lari 15 km", 850, 15), ("Sprint 50x100m", 850, 15),
                ("Mini marathon 21 km", 900, 15)],
        "VIT": [("Puasa 48 jam", 900, 15), ("Meditasi 2 jam", 850, 15),
                ("Full detox 7 hari", 880, 15)],
        "INT": [("Tulis buku", 850, 15), ("Proyek besar selesai", 900, 15),
                ("Ajari workshop", 880, 15)],
    },
}

USER_RANK_TO_QUEST_RANKS = {
    "F": ["E", "E", "E", "D"], "E": ["E", "D", "D", "D"],
    "D": ["D", "D", "C", "C"], "C": ["C", "C", "D", "B"],
    "B": ["B", "B", "C", "A"], "A": ["A", "A", "B", "S"],
    "S": ["S", "S", "A", "SS"], "SS": ["SS", "SS", "S", "SSS"],
    "SSS": ["SSS", "SSS", "SS", "SSS"],
}

QUEST_RANK_ICONS = {"E": "🟢", "D": "🔵", "C": "🟣", "B": "🟠",
                    "A": "🔴", "S": "⭐", "SS": "🌟", "SSS": "💎"}
STAT_ICONS = {"STR": "💪", "AGI": "🏃", "VIT": "❤️", "INT": "🧠"}

RANDOM_QUESTS = [
    ("Minum 1 gelas air sekarang", "VIT", 30),
    ("Push-up 10x sekarang", "STR", 30),
    ("Jalan cepat 5 menit", "AGI", 30),
    ("Baca 3 halaman buku", "INT", 30),
    ("Senyum + afirmasi positif", "VIT", 20),
    ("Squat 15x sekarang", "STR", 35),
    ("Tarik napas dalam 10x", "VIT", 20),
]

RANK_TABLE = [(1000, "SSS"), (750, "SS"), (550, "S"), (400, "A"),
              (280, "B"), (180, "C"), (100, "D"), (50, "E"), (0, "F")]

BADGES = {
    "first_quest": ("🌱", "Langkah Pertama", "Selesaikan quest pertama"),
    "streak_7": ("🔥", "Konsisten", "Streak 7 hari"),
    "streak_30": ("💎", "Legenda", "Streak 30 hari"),
    "level_5": ("⭐", "Pemula", "Capai Level 5"),
    "level_10": ("🌟", "Ahli", "Capai Level 10"),
    "level_25": ("💫", "Master", "Capai Level 25"),
    "rank_c": ("🥉", "Pejuang", "Capai Rank C"),
    "rank_b": ("🥈", "Ksatria", "Capai Rank B"),
    "rank_a": ("🥇", "Elit", "Capai Rank A"),
    "rank_s": ("👑", "Sang Raja", "Capai Rank S"),
    "quest_50": ("📜", "Rajin", "Selesaikan 50 quest"),
    "quest_100": ("📚", "Disiplin", "Selesaikan 100 quest"),
    "boss_slayer": ("🐉", "Pembunuh Naga", "Kalahkan Weekly Boss"),
    "hidden_finder": ("🎰", "Penjelajah", "Temukan Hidden Quest"),
    "rank_ss": ("⚡", "Overlord", "Capai Rank SS"),
    "rank_sss": ("🌌", "Monarch", "Capai Rank SSS"),
    "perfect_day": ("✨", "Sempurna", "Selesaikan semua quest sehari"),
    "shopper": ("🛍️", "Shopper", "Pertama kali beli di shop"),
    "whale": ("🐳", "Whale", "Beli 10+ item di shop"),
}

BOSS_BASE_HP = 5000

# ================== SHOP CONFIG ==================
SHOP_CATEGORIES = {
    "cosmetic": {"icon": "🎨", "name": "Kosmetik"},
    "boost":    {"icon": "⚡", "name": "Boost"},
    "qol":      {"icon": "🛠️", "name": "Quality of Life"},
    "gacha":    {"icon": "🎰", "name": "Gacha Box"},
    "bundle":   {"icon": "📦", "name": "Bundle"},
}

SHOP_ITEMS = {
    "color_rainbow": {"name": "🌈 Warna Rainbow", "desc": "Username rainbow di leaderboard",
        "price": 50, "cat": "cosmetic", "type": "permanent"},
    "color_gold":    {"name": "🟡 Warna Gold", "desc": "Username warna emas di leaderboard",
        "price": 40, "cat": "cosmetic", "type": "permanent"},
    "title_custom":  {"name": "🏷️ Custom Title", "desc": "Title custom di status",
        "price": 75, "cat": "cosmetic", "type": "permanent"},
    "card_neon":     {"name": "🎴 Card Theme: Neon", "desc": "Border neon di card quest",
        "price": 60, "cat": "cosmetic", "type": "permanent"},
    "card_gold":     {"name": "🎴 Card Theme: Gold", "desc": "Border emas elegan",
        "price": 100, "cat": "cosmetic", "type": "permanent"},
    "frame_flame":   {"name": "🔥 Frame: Flame", "desc": "Frame api di profil",
        "price": 120, "cat": "cosmetic", "type": "permanent"},
    "emoji_pack":    {"name": "✨ Animated Emoji", "desc": "Unlock emoji animasi",
        "price": 80, "cat": "cosmetic", "type": "permanent"},

    "boost_exp2x":   {"name": "🔥 2x EXP (24 jam)", "desc": "EXP 2x lipat 24 jam",
        "price": 40, "cat": "boost", "type": "timed", "hours": 24},
    "boost_stat2x":  {"name": "🎯 2x Stat (24 jam)", "desc": "Stat gain 2x lipat 24 jam",
        "price": 50, "cat": "boost", "type": "timed", "hours": 24},
    "boost_hidden":  {"name": "🍀 Hidden Guarantee", "desc": "Quest dijamin Hidden",
        "price": 30, "cat": "boost", "type": "instant"},
    "boost_boss":    {"name": "⚔️ 2x Boss Damage (7h)", "desc": "Damage boss 2x 7 hari",
        "price": 60, "cat": "boost", "type": "timed", "hours": 168},
    "boost_login":   {"name": "💰 3x Login Bonus (7h)", "desc": "Login bonus 3x 7 hari",
        "price": 45, "cat": "boost", "type": "timed", "hours": 168},

    "qol_reroll":    {"name": "🔄 Reroll Quest", "desc": "Ganti quest harian",
        "price": 15, "cat": "qol", "type": "instant"},
    "qol_shield":    {"name": "🛡️ Streak Shield", "desc": "Proteksi streak 1 hari",
        "price": 25, "cat": "qol", "type": "item"},
    "qol_heal":      {"name": "💊 Heal Penalty", "desc": "Keluar dari Penalty Zone",
        "price": 40, "cat": "qol", "type": "instant"},
    "qol_rest":      {"name": "📅 Extra Rest Day", "desc": "Rest kedua minggu ini",
        "price": 20, "cat": "qol", "type": "instant"},
    "qol_extra_quest": {"name": "🎯 Extra Quest", "desc": "+1 slot quest hari ini",
        "price": 35, "cat": "qol", "type": "instant"},

    "gacha_common":  {"name": "📦 Common Box", "desc": "Reward random biasa",
        "price": 20, "cat": "gacha", "type": "instant"},
    "gacha_rare":    {"name": "🎁 Rare Box", "desc": "Reward random bagus",
        "price": 80, "cat": "gacha", "type": "instant"},
    "gacha_legend":  {"name": "💎 Legendary Box", "desc": "Dijamin item terbaik!",
        "price": 250, "cat": "gacha", "type": "instant"},

    "bundle_starter": {"name": "🎒 Starter Pack",
        "desc": "2x EXP 24j + Common Box + Reroll",
        "price": 60, "cat": "bundle", "type": "instant"},
    "bundle_warrior": {"name": "⚔️ Warrior Pack",
        "desc": "2x EXP + 2x Stat + Hidden + Rare Box",
        "price": 150, "cat": "bundle", "type": "instant"},
    "bundle_legend":  {"name": "👑 Legend Pack",
        "desc": "Semua boost + Legendary Box + Card Gold + Flame",
        "price": 400, "cat": "bundle", "type": "instant"},
}

# ================== UTILS ==================
def get_rank(total):
    for thresh, name in RANK_TABLE:
        if total >= thresh: return name
    return "F"

def exp_needed(level): return level * 100

def week_key(d=None):
    d = d or date.today()
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"

def quests_per_day(level):
    if level < 3: return 1
    if level < 6: return 2
    if level < 11: return 3
    if level < 21: return 4
    return 5

def pick_quest_for_rank(user_rank):
    qr = random.choice(USER_RANK_TO_QUEST_RANKS.get(user_rank, ["E"]))
    stat = random.choice(["STR", "AGI", "VIT", "INT"])
    q = random.choice(QUEST_DB[qr][stat])
    return qr, stat, q

def pick_hidden_quest(user_rank):
    allowed = USER_RANK_TO_QUEST_RANKS.get(user_rank, ["E"])
    all_ranks = list(QUEST_DB.keys())
    highest = max(all_ranks.index(r) for r in allowed)
    hidden_idx = min(highest + 1, len(all_ranks) - 1)
    hr = all_ranks[hidden_idx]
    stat = random.choice(["STR", "AGI", "VIT", "INT"])
    q = random.choice(QUEST_DB[hr][stat])
    return hr, stat, q

# ================== DATABASE ==================
def init_db():
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT,
        level INTEGER DEFAULT 1, exp INTEGER DEFAULT 0,
        str INTEGER DEFAULT 0, agi INTEGER DEFAULT 0,
        vit INTEGER DEFAULT 0, int INTEGER DEFAULT 0,
        stat_points INTEGER DEFAULT 0, last_quest_date TEXT,
        current_quest TEXT, current_quest_stat TEXT,
        quest_completed INTEGER DEFAULT 0, last_rest_week TEXT,
        streak INTEGER DEFAULT 0, last_complete_date TEXT,
        last_login_date TEXT, login_streak INTEGER DEFAULT 0,
        total_quests INTEGER DEFAULT 0, badges TEXT DEFAULT '',
        last_penalty_date TEXT, in_penalty INTEGER DEFAULT 0,
        current_quest_rank TEXT DEFAULT 'E',
        last_attack_date TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS daily_quests (
        user_id INTEGER, quest_date TEXT, slot INTEGER,
        quest_rank TEXT, stat TEXT, quest_name TEXT,
        exp_reward INTEGER, stat_gain INTEGER,
        completed INTEGER DEFAULT 0, is_hidden INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, quest_date, slot))""")
    c.execute("""CREATE TABLE IF NOT EXISTS boss_state (
        week TEXT PRIMARY KEY, hp INTEGER, max_hp INTEGER,
        defeated INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS boss_damage (
        user_id INTEGER, week TEXT, damage INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, week))""")
    c.execute("""CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, item_id TEXT, price INTEGER,
        purchase_date TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_cosmetics (
        user_id INTEGER, cosmetic_id TEXT,
        PRIMARY KEY (user_id, cosmetic_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_boosts (
        user_id INTEGER, boost_id TEXT, expires_at TEXT,
        PRIMARY KEY (user_id, boost_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_inventory (
        user_id INTEGER, item_id TEXT, quantity INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, item_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_title (
        user_id INTEGER PRIMARY KEY, title TEXT)""")
    conn.commit(); conn.close()
    migrate_db()

def migrate_db():
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    existing = {row[1] for row in c.fetchall()}
    new_cols = [
        ("last_login_date", "TEXT"), ("login_streak", "INTEGER DEFAULT 0"),
        ("total_quests", "INTEGER DEFAULT 0"), ("badges", "TEXT DEFAULT ''"),
        ("last_penalty_date", "TEXT"), ("in_penalty", "INTEGER DEFAULT 0"),
        ("current_quest_rank", "TEXT DEFAULT 'E'"),
        ("last_attack_date", "TEXT"),
    ]
    for col, typ in new_cols:
        if col not in existing:
            try: c.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
            except sqlite3.OperationalError: pass
    conn.commit(); conn.close()

def get_user(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = c.fetchone(); conn.close(); return row

def create_user(uid, username):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)",
              (uid, username))
    conn.commit(); conn.close()

def reset_user(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("""UPDATE users SET
        level=1, exp=0, str=0, agi=0, vit=0, int=0, stat_points=0,
        last_quest_date=NULL, current_quest=NULL, current_quest_stat=NULL,
        quest_completed=0, last_rest_week=NULL, streak=0,
        last_complete_date=NULL, last_login_date=NULL, login_streak=0,
        total_quests=0, badges='', last_penalty_date=NULL, in_penalty=0,
        current_quest_rank='E', last_attack_date=NULL WHERE user_id=?""", (uid,))
    c.execute("DELETE FROM boss_damage WHERE user_id=?", (uid,))
    c.execute("DELETE FROM daily_quests WHERE user_id=?", (uid,))
    c.execute("DELETE FROM purchases WHERE user_id=?", (uid,))
    c.execute("DELETE FROM user_cosmetics WHERE user_id=?", (uid,))
    c.execute("DELETE FROM user_boosts WHERE user_id=?", (uid,))
    c.execute("DELETE FROM user_inventory WHERE user_id=?", (uid,))
    c.execute("DELETE FROM user_title WHERE user_id=?", (uid,))
    conn.commit(); conn.close()

def add_exp_and_levelup(uid, amount):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT level, exp, stat_points FROM users WHERE user_id=?", (uid,))
    level, exp, sp = c.fetchone()
    exp = max(0, exp + amount)
    leveled = 0
    while exp >= exp_needed(level):
        exp -= exp_needed(level); level += 1; sp += 5; leveled += 1
    c.execute("UPDATE users SET level=?, exp=?, stat_points=? WHERE user_id=?",
              (level, exp, sp, uid))
    conn.commit(); conn.close()
    return leveled, level, sp
  # ================== DAILY QUEST LOGIC ==================
def generate_daily_quests(uid):
    row = get_user(uid)
    if not row: return []
    level = row[2]
    total_stats = row[4] + row[5] + row[6] + row[7]
    user_rank = get_rank(total_stats)
    n = quests_per_day(level)
    today = date.today().isoformat()
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("DELETE FROM daily_quests WHERE user_id=? AND quest_date=?", (uid, today))
    hidden_active = has_active_boost(uid, "boost_hidden_used")
    quests = []; used = set()
    for slot in range(n):
        for _try in range(20):
            if hidden_active or random.random() < 0.10:
                qr, stat, (qname, qexp, qgain) = pick_hidden_quest(user_rank)
                exp = qexp * 2; gain = qgain + 2; is_hidden = True
            else:
                qr, stat, (qname, qexp, qgain) = pick_quest_for_rank(user_rank)
                exp = qexp; gain = qgain; is_hidden = False
            if (stat, qname) not in used:
                used.add((stat, qname)); break
        c.execute("""INSERT INTO daily_quests
            (user_id, quest_date, slot, quest_rank, stat, quest_name,
             exp_reward, stat_gain, completed, is_hidden)
            VALUES (?,?,?,?,?,?,?,?,0,?)""",
            (uid, today, slot, qr, stat, qname, exp, gain, int(is_hidden)))
        quests.append({"slot": slot, "quest_rank": qr, "stat": stat,
                       "quest_name": qname, "exp": exp, "gain": gain,
                       "completed": 0, "is_hidden": is_hidden})
    conn.commit(); conn.close()
    if hidden_active:
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("DELETE FROM user_boosts WHERE user_id=? AND boost_id=?",
                  (uid, "boost_hidden_used"))
        conn.commit(); conn.close()
    return quests

def get_today_quests(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("""SELECT slot, quest_rank, stat, quest_name, exp_reward,
                 stat_gain, completed, is_hidden FROM daily_quests
                 WHERE user_id=? AND quest_date=? ORDER BY slot""",
              (uid, date.today().isoformat()))
    rows = c.fetchall(); conn.close()
    if not rows: return None
    return [{"slot": r[0], "quest_rank": r[1], "stat": r[2], "quest_name": r[3],
             "exp": r[4], "gain": r[5], "completed": r[6], "is_hidden": bool(r[7])}
            for r in rows]

def take_quests(uid):
    row = get_user(uid)
    if not row: return {"error": "Ketik /start dulu."}
    today = date.today().isoformat()
    quests = get_today_quests(uid)
    if row[9] == today and quests:
        return {"quests": quests}
    quests = generate_daily_quests(uid)
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("UPDATE users SET last_quest_date=? WHERE user_id=?", (today, uid))
    conn.commit(); conn.close()
    return {"quests": quests}

def complete_quest_slot(uid, slot):
    row = get_user(uid)
    if not row: return {"error": "Ketik /start dulu."}
    today = date.today().isoformat()
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("""SELECT quest_rank, stat, quest_name, exp_reward, stat_gain,
                 completed, is_hidden FROM daily_quests
                 WHERE user_id=? AND quest_date=? AND slot=?""", (uid, today, slot))
    q = c.fetchone()
    if not q:
        conn.close()
        return {"error": "Quest kadaluarsa. Ketik /quest untuk yang baru."}
    if q[5]:
        conn.close(); return {"error": "Quest ini sudah selesai."}
    qr, stat, qname, exp_r, gain_r, is_hidden = q[0], q[1], q[2], q[3], q[4], bool(q[6])
    c.execute("UPDATE daily_quests SET completed=1 WHERE user_id=? AND quest_date=? AND slot=?",
              (uid, today, slot))
    stat_col = stat.lower()
    stat_mult = 2 if has_active_boost(uid, "boost_stat2x") else 1
    c.execute(f"UPDATE users SET {stat_col}={stat_col}+?, total_quests=total_quests+1 WHERE user_id=?",
              (gain_r * stat_mult, uid))
    streak = row[14]; lcd = row[15]
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    new_streak = streak; streak_bonus = 0
    if lcd != today:
        new_streak = streak + 1 if lcd == yesterday else 1
        streak_bonus = 20 if new_streak % 7 == 0 else 0
        c.execute("UPDATE users SET streak=?, last_complete_date=? WHERE user_id=?",
                  (new_streak, today, uid))
    in_penalty = row[21] if len(row) > 21 else 0
    if in_penalty:
        c.execute("UPDATE users SET in_penalty=0 WHERE user_id=?", (uid,))
    c.execute("""SELECT COUNT(*) FROM daily_quests
                 WHERE user_id=? AND quest_date=? AND completed=0""", (uid, today))
    remaining = c.fetchone()[0]
    perfect_bonus = 100 if remaining == 0 else 0
    conn.commit(); conn.close()
    penalty_mult = 0.5 if in_penalty else 1.0
    total_exp = int((exp_r + streak_bonus + perfect_bonus) * penalty_mult)
    if has_active_boost(uid, "boost_exp2x"): total_exp *= 2
    leveled, new_level, sp = add_exp_and_levelup(uid, total_exp)
    icon = QUEST_RANK_ICONS.get(qr, "❓")
    si = STAT_ICONS.get(stat, "❓")
    msg = (f"🎉 <b>QUEST SELESAI!</b>\n\n"
           f"{icon} Rank: <b>{qr}</b> • {si} {stat}\n"
           f"📜 {esc(qname)}\n"
           f"💎 +{total_exp} EXP\n"
           f"📈 +{gain_r * stat_mult} {stat}")
    if is_hidden: msg += "\n🎰 <b>Hidden Quest bonus!</b>"
    if in_penalty: msg += "\n\n✅ <b>Keluar dari Penalty Zone!</b>"
    if streak_bonus: msg += f"\n🔥 Streak 7-hari: +{streak_bonus} EXP"
    if perfect_bonus: msg += f"\n\n✨ <b>PERFECT DAY! +100 EXP bonus!</b>"
    msg += f"\n🔥 Streak: {new_streak} hari"
    if leveled:
        msg += f"\n\n⬆️ <b>LEVEL UP!</b> Level {new_level}\n🎁 +{leveled * 5} Stat Points"
        old_n = quests_per_day(row[2]); new_n = quests_per_day(new_level)
        if new_n > old_n:
            msg += f"\n🎴 <b>Quest/hari naik: {old_n} → {new_n}!</b>"
    row2 = get_user(uid)
    if is_hidden: unlock_badge(uid, "hidden_finder")
    if perfect_bonus: unlock_badge(uid, "perfect_day")
    msg += format_badge_msg(check_badges(uid, row2))
    return {"text": msg, "perfect": bool(perfect_bonus)}

# ================== HELPERS ==================
def check_daily_login(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT last_login_date, login_streak FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    if not row: conn.close(); return None
    last_login, streak = row
    today = date.today().isoformat()
    if last_login == today: conn.close(); return None
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    new_streak = streak + 1 if last_login == yesterday else 1
    bonus = min(new_streak * 10, 100)
    if has_active_boost(uid, "boost_login"): bonus *= 3
    c.execute("UPDATE users SET last_login_date=?, login_streak=? WHERE user_id=?",
              (today, new_streak, uid))
    conn.commit(); conn.close()
    add_exp_and_levelup(uid, bonus)
    return f"🎁 <b>Daily Login Bonus!</b> Hari ke-{new_streak} • +{bonus} EXP"

def check_penalty(uid, row):
    if len(row) < 22: return None
    if row[21]:
        return "⚠️ Kamu masih di <b>Penalty Zone</b>!\nSelesaikan quest untuk keluar."
    last_quest = row[9]
    if not last_quest: return None
    try:
        last_dt = datetime.strptime(last_quest, "%Y-%m-%d").date()
    except Exception: return None
    days_missed = (date.today() - last_dt).days
    if days_missed >= 4:
        stat = random.choice(["str", "agi", "vit", "int"])
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute(f"""UPDATE users SET exp=MAX(0, exp-100),
                     {stat}=MAX(0, {stat}-2), in_penalty=1,
                     last_penalty_date=? WHERE user_id=?""",
                  (date.today().isoformat(), uid))
        conn.commit(); conn.close()
        return (f"🚨 <b>PENALTY ZONE!</b>\n\n"
                f"Bolos {days_missed} hari!\n💔 -100 EXP\n💔 -2 {stat.upper()}")
    return None

def check_badges(uid, row):
    if len(row) < 20: return []
    owned = set((row[19] or "").split(",")) - {""}
    total_stats = row[4] + row[5] + row[6] + row[7]
    total_quests = row[18] if len(row) > 18 else 0
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM purchases WHERE user_id=?", (uid,))
    purchases = c.fetchone()[0]; conn.close()
    checks = {
        "first_quest": total_quests >= 1,
        "streak_7": row[14] >= 7, "streak_30": row[14] >= 30,
        "level_5": row[2] >= 5, "level_10": row[2] >= 10, "level_25": row[2] >= 25,
        "rank_c": total_stats >= 180, "rank_b": total_stats >= 280,
        "rank_a": total_stats >= 400, "rank_s": total_stats >= 550,
        "rank_ss": total_stats >= 750, "rank_sss": total_stats >= 1000,
        "quest_50": total_quests >= 50, "quest_100": total_quests >= 100,
        "shopper": purchases >= 1, "whale": purchases >= 10,
    }
    new_badges = []
    for k, ok in checks.items():
        if ok and k not in owned: new_badges.append(k); owned.add(k)
    if new_badges:
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("UPDATE users SET badges=? WHERE user_id=?",
                  (",".join(sorted(owned)), uid))
        conn.commit(); conn.close()
    return new_badges

def unlock_badge(uid, key):
    row = get_user(uid)
    if not row or len(row) < 20: return False
    owned = set((row[19] or "").split(",")) - {""}
    if key in owned: return False
    owned.add(key)
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("UPDATE users SET badges=? WHERE user_id=?", (",".join(sorted(owned)), uid))
    conn.commit(); conn.close()
    return True

def format_badge_msg(keys):
    if not keys: return ""
    lines = ["\n\n🏆 <b>BADGE BARU UNLOCKED!</b>"]
    for k in keys:
        if k in BADGES:
            emoji, name, desc = BADGES[k]
            lines.append(f"{emoji} <b>{name}</b> — {desc}")
    return "\n".join(lines)

# ================== SHOP HELPERS ==================
def has_cosmetic(uid, cid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT 1 FROM user_cosmetics WHERE user_id=? AND cosmetic_id=?", (uid, cid))
    r = c.fetchone(); conn.close(); return bool(r)

def has_active_boost(uid, bid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT expires_at FROM user_boosts WHERE user_id=? AND boost_id=?", (uid, bid))
    r = c.fetchone(); conn.close()
    if not r: return False
    try: return datetime.fromisoformat(r[0]) > datetime.now()
    except: return False

def add_time_boost(uid, bid, hours):
    conn = sqlite3.connect(DB); c = conn.cursor()
    now = datetime.now()
    c.execute("SELECT expires_at FROM user_boosts WHERE user_id=? AND boost_id=?", (uid, bid))
    r = c.fetchone()
    if r:
        try:
            cur = datetime.fromisoformat(r[0])
            if cur > now: now = cur
        except: pass
    new_exp = (now + timedelta(hours=hours)).isoformat()
    c.execute("INSERT OR REPLACE INTO user_boosts (user_id, boost_id, expires_at) VALUES (?,?,?)",
              (uid, bid, new_exp))
    conn.commit(); conn.close()
    return new_exp

def add_cosmetic(uid, cid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO user_cosmetics (user_id, cosmetic_id) VALUES (?,?)",
              (uid, cid))
    conn.commit(); conn.close()

def add_item(uid, iid, qty=1):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("""INSERT INTO user_inventory (user_id, item_id, quantity) VALUES (?,?,?)
                 ON CONFLICT(user_id, item_id) DO UPDATE SET quantity=quantity+?""",
              (uid, iid, qty, qty))
    conn.commit(); conn.close()

def open_gacha(uid, box_id):
    rolls = {
        "gacha_common": [
            ("exp", (30, 80), 0.70), ("boost_exp2x", 6, 0.15),
            ("item", "qol_shield", 0.10), ("cosmetic", "color_gold", 0.05),
        ],
        "gacha_rare": [
            ("exp", (150, 300), 0.50), ("boost_exp2x", 24, 0.20),
            ("boost_stat2x", 24, 0.15), ("cosmetic", "card_neon", 0.10),
            ("cosmetic", "title_custom", 0.05),
        ],
        "gacha_legend": [
            ("exp", (500, 1000), 0.40), ("cosmetic", "color_rainbow", 0.20),
            ("cosmetic", "card_gold", 0.15), ("cosmetic", "frame_flame", 0.15),
            ("cosmetic", "emoji_pack", 0.10),
        ],
    }[box_id]
    r = random.random(); acc = 0
    for roll in rolls:
        acc += roll[-1]
        if r <= acc:
            if roll[0] == "exp":
                amt = random.randint(*roll[1])
                add_exp_and_levelup(uid, amt)
                return f"💎 Kamu dapat <b>+{amt} EXP</b>!"
            elif roll[0] == "boost_exp2x":
                add_time_boost(uid, "boost_exp2x", roll[1])
                return f"🔥 Kamu dapat <b>2x EXP {roll[1]} jam</b>!"
            elif roll[0] == "boost_stat2x":
                add_time_boost(uid, "boost_stat2x", roll[1])
                return f"🎯 Kamu dapat <b>2x Stat {roll[1]} jam</b>!"
            elif roll[0] == "item":
                add_item(uid, roll[1], 1)
                return f"🛡️ Kamu dapat <b>{SHOP_ITEMS.get(roll[1], {}).get('name', roll[1])}</b>!"
            elif roll[0] == "cosmetic":
                add_cosmetic(uid, roll[1])
                return f"🎨 Kamu dapat <b>{SHOP_ITEMS.get(roll[1], {}).get('name', roll[1])}</b>!"
    add_exp_and_levelup(uid, 50); return "💎 +50 EXP"

def process_purchase(uid, item_id):
    if item_id not in SHOP_ITEMS:
        return "❌ Item tidak ditemukan."
    item = SHOP_ITEMS[item_id]
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("INSERT INTO purchases (user_id, item_id, price, purchase_date) VALUES (?,?,?,?)",
              (uid, item_id, item["price"], date.today().isoformat()))
    conn.commit(); conn.close()
    t = item["type"]
    if t == "permanent":
        add_cosmetic(uid, item_id)
        return f"✅ <b>{item['name']}</b> aktif permanen!"
    if t == "timed":
        exp = add_time_boost(uid, item_id, item["hours"])
        return f"✅ <b>{item['name']}</b> aktif sampai <b>{exp[:16].replace('T', ' ')}</b>"
    if t == "item":
        add_item(uid, item_id, 1)
        return f"✅ <b>{item['name']}</b> masuk inventory!"
    if item_id == "qol_reroll":
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("DELETE FROM daily_quests WHERE user_id=? AND quest_date=?",
                  (uid, date.today().isoformat()))
        c.execute("UPDATE users SET last_quest_date=NULL WHERE user_id=?", (uid,))
        conn.commit(); conn.close()
        return "🔄 Quest di-reroll! Ketik /quest."
    if item_id == "qol_heal":
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("UPDATE users SET in_penalty=0, last_quest_date=? WHERE user_id=?",
                  (date.today().isoformat(), uid))
        conn.commit(); conn.close()
        return "💊 Kamu keluar dari Penalty Zone!"
    if item_id == "qol_rest":
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("UPDATE users SET last_rest_week=NULL WHERE user_id=?", (uid,))
        conn.commit(); conn.close()
        return "📅 Extra rest day aktif! Ketik /rest"
    if item_id == "qol_extra_quest":
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("DELETE FROM daily_quests WHERE user_id=? AND quest_date=?",
                  (uid, date.today().isoformat()))
        c.execute("UPDATE users SET last_quest_date=NULL WHERE user_id=?", (uid,))
        conn.commit(); conn.close()
        return "🎯 Extra quest slot aktif! Ketik /quest"
    if item_id == "boost_hidden":
        add_time_boost(uid, "boost_hidden_used", 1)
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("DELETE FROM daily_quests WHERE user_id=? AND quest_date=?",
                  (uid, date.today().isoformat()))
        c.execute("UPDATE users SET last_quest_date=NULL WHERE user_id=?", (uid,))
        conn.commit(); conn.close()
        return "🍀 Hidden Guarantee aktif! Ketik /quest."
    if item_id.startswith("gacha_"):
        return "🎁 " + open_gacha(uid, item_id)
    if item_id.startswith("bundle_"):
        parts_map = {
            "bundle_starter": ["exp2x_24", "gacha_common", "reroll"],
            "bundle_warrior": ["exp2x_24", "stat2x_24", "hidden", "gacha_rare"],
            "bundle_legend": ["exp2x_24", "stat2x_24", "boss_168", "login_168",
                              "gacha_legend", "card_gold", "frame_flame"],
        }
        results = []
        for sub in parts_map.get(item_id, []):
            if sub == "exp2x_24":
                add_time_boost(uid, "boost_exp2x", 24); results.append("🔥 2x EXP 24j")
            elif sub == "stat2x_24":
                add_time_boost(uid, "boost_stat2x", 24); results.append("🎯 2x Stat 24j")
            elif sub == "boss_168":
                add_time_boost(uid, "boost_boss", 168); results.append("⚔️ 2x Boss 7h")
            elif sub == "login_168":
                add_time_boost(uid, "boost_login", 168); results.append("💰 3x Login 7h")
            elif sub == "gacha_common":
                results.append(open_gacha(uid, "gacha_common"))
            elif sub == "gacha_rare":
                results.append(open_gacha(uid, "gacha_rare"))
            elif sub == "gacha_legend":
                results.append(open_gacha(uid, "gacha_legend"))
            elif sub == "reroll":
                conn = sqlite3.connect(DB); c = conn.cursor()
                c.execute("DELETE FROM daily_quests WHERE user_id=? AND quest_date=?",
                          (uid, date.today().isoformat()))
                c.execute("UPDATE users SET last_quest_date=NULL WHERE user_id=?", (uid,))
                conn.commit(); conn.close(); results.append("🔄 Reroll")
            elif sub == "hidden":
                add_time_boost(uid, "boost_hidden_used", 1); results.append("🍀 Hidden")
            elif sub == "card_gold":
                add_cosmetic(uid, "card_gold"); results.append("🎴 Card Gold")
            elif sub == "frame_flame":
                add_cosmetic(uid, "frame_flame"); results.append("🔥 Flame Frame")
        return "📦 <b>Bundle dibuka!</b>\n" + "\n".join("• " + x for x in results)
    return f"✅ <b>{item['name']}</b> aktif!"

# ================== BOSS ==================
def get_or_spawn_boss():
    week = week_key()
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT week, hp, max_hp, defeated FROM boss_state WHERE week=?", (week,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO boss_state VALUES (?,?,?,0)",
                  (week, BOSS_BASE_HP, BOSS_BASE_HP))
        conn.commit(); row = (week, BOSS_BASE_HP, BOSS_BASE_HP, 0)
    conn.close(); return row

def add_boss_damage(uid, dmg):
    week = week_key()
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT damage FROM boss_damage WHERE user_id=? AND week=?", (uid, week))
    if c.fetchone():
        c.execute("UPDATE boss_damage SET damage=damage+? WHERE user_id=? AND week=?",
                  (dmg, uid, week))
    else:
        c.execute("INSERT INTO boss_damage VALUES (?,?,?)", (uid, week, dmg))
    c.execute("UPDATE boss_state SET hp=MAX(0, hp-?) WHERE week=?", (dmg, week))
    c.execute("SELECT hp, defeated FROM boss_state WHERE week=?", (week,))
    hp, defeated = c.fetchone()
    conn.commit(); conn.close()
    return hp, defeated
  # ================== RENDERERS ==================
def render_quests_list(quests):
    done = sum(1 for q in quests if q["completed"])
    total = len(quests)
    lines = [f"🎴 <b>DAILY QUESTS</b> [{done}/{total}]", "━━━━━━━━━━━━━━━━━━━━"]
    for q in quests:
        mark = "✅" if q["completed"] else "⬜"
        icon = QUEST_RANK_ICONS.get(q["quest_rank"], "❓")
        si = STAT_ICONS.get(q["stat"], "❓")
        num = q["slot"] + 1
        hid = "🎰 " if q["is_hidden"] else ""
        lines.append(f"{mark} <b>#{num}</b> {icon} {q['quest_rank']} • {si} {q['stat']}")
        lines.append(f"     {hid}<i>{esc(q['quest_name'])}</i>")
        lines.append(f"     💎 +{q['exp']} EXP • +{q['gain']} {q['stat']}")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    if done == total:
        lines.append("🎉 <b>PERFECT DAY!</b> Semua quest selesai!")
    return "\n".join(lines)

def render_status_text(row):
    (_, username, level, exp, s, a, v, i, sp, *_r) = row
    total = s + a + v + i
    rank = get_rank(total)
    need = exp_needed(level)
    filled = int((exp / need) * 10) if need else 0
    bar = "█" * filled + "░" * (10 - filled)
    bc = len([b for b in (row[19] or "").split(",") if b]) if len(row) > 19 else 0
    in_p = row[21] if len(row) > 21 else 0
    plabel = " ⚠️ <b>PENALTY</b>" if in_p else ""
    n_quest = quests_per_day(level)
    allowed = sorted(set(USER_RANK_TO_QUEST_RANKS.get(rank, ["E"])))
    return (
        f"📊 <b>STATUS HUNTER</b>{plabel}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {esc(username)}\n"
        f"🏅 Rank: <b>{rank}</b>\n"
        f"⭐ Level: <b>{level}</b>\n"
        f"✨ EXP: {exp}/{need}\n   [{bar}]\n"
        f"🔥 Streak: {row[14]} hari\n"
        f"🎁 Login: {row[17] if len(row) > 17 else 0} hari\n"
        f"🎴 Quest/hari: <b>{n_quest}</b>\n"
        f"🏆 Badge: {bc}/{len(BADGES)}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💪 STR: {s}\n🏃 AGI: {a}\n❤️ VIT: {v}\n🧠 INT: {i}\n"
        f"📈 Total: <b>{total}</b> • 🎯 Points: <b>{sp}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎴 Quest rank: {' • '.join(allowed)}"
    )

def render_boss_text(uid):
    week, hp, max_hp, defeated = get_or_spawn_boss()
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT damage FROM boss_damage WHERE user_id=? AND week=?", (uid, week))
    r = c.fetchone(); my_dmg = r[0] if r else 0
    c.execute("""SELECT u.username, bd.damage FROM boss_damage bd
                 JOIN users u ON u.user_id=bd.user_id
                 WHERE bd.week=? ORDER BY bd.damage DESC LIMIT 5""", (week,))
    top = c.fetchall()
    c.execute("SELECT last_attack_date FROM users WHERE user_id=?", (uid,))
    la = c.fetchone(); conn.close()
    today = date.today().isoformat()
    can_attack = not (la and la[0] == today)
    pct = int((hp / max_hp) * 100) if max_hp else 0
    filled = int((hp / max_hp) * 10) if max_hp else 0
    bar = "█" * filled + "░" * (10 - filled)
    status = "💀 <b>DIKALAHKAN</b>" if defeated else "⚔️ <b>MASIH HIDUP</b>"
    cd_status = "✅ <b>Siap menyerang!</b>" if can_attack else "⏳ <b>Cooldown (reset 00:00)</b>"
    lines = [f"🐉 <b>WEEKLY BOSS RAID</b>", f"Minggu: {week}",
             "━━━━━━━━━━━━━━━━━━━", f"👹 <b>Raja Kegelapan</b>",
             f"❤️ HP: {hp}/{max_hp} ({pct}%)", f"   [{bar}]", f"{status}",
             "━━━━━━━━━━━━━━━━━━━",
             f"⚔️ Damage kamu: <b>{my_dmg}</b>",
             f"🎯 Status: {cd_status}",
             "", "🏅 <b>Top Attackers:</b>"]
    if top:
        for idx, (u, d) in enumerate(top): lines.append(f"{idx+1}. {esc(u)} — {d} dmg")
    else: lines.append("<i>Belum ada yang nyerang</i>")
    return "\n".join(lines)

def render_shop_category(cat):
    items = [(k, v) for k, v in SHOP_ITEMS.items() if v["cat"] == cat]
    lines = [f"{SHOP_CATEGORIES[cat]['icon']} <b>{SHOP_CATEGORIES[cat]['name'].upper()}</b>",
             "━━━━━━━━━━━━━━━━━━━━"]
    for k, v in items:
        lines.append(f"• <b>{v['name']}</b> — <b>{v['price']}</b> ⭐")
        lines.append(f"  <i>{v['desc']}</i>")
    return "\n".join(lines)

# ================== KEYBOARDS ==================
def kb_quests_list(quests):
    incomplete = [q for q in quests if not q["completed"]]
    rows = []; row = []
    for q in incomplete:
        num = q["slot"] + 1
        row.append(InlineKeyboardButton(f"✅ {num}", callback_data=f"complete_{q['slot']}"))
        if len(row) == 3: rows.append(row); row = []
    if row: rows.append(row)
    rows.append([InlineKeyboardButton("📊 Status", callback_data="view_status"),
                 InlineKeyboardButton("🥇 Rank", callback_data="view_rank")])
    return InlineKeyboardMarkup(rows)

def kb_after_complete():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎴 Quest", callback_data="view_quest"),
         InlineKeyboardButton("📊 Status", callback_data="view_status")],
        [InlineKeyboardButton("🎯 Allocate", callback_data="view_alloc"),
         InlineKeyboardButton("🥇 Rank", callback_data="view_rank")],
        [InlineKeyboardButton("🐉 Boss", callback_data="view_boss"),
         InlineKeyboardButton("⭐ Shop", callback_data="shop_back")],
    ])

def kb_status():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎴 Quest", callback_data="view_quest"),
         InlineKeyboardButton("🎯 Allocate", callback_data="view_alloc"),
         InlineKeyboardButton("🥇 Rank", callback_data="view_rank")],
        [InlineKeyboardButton("🏆 Badge", callback_data="view_badges"),
         InlineKeyboardButton("🐉 Boss", callback_data="view_boss"),
         InlineKeyboardButton("⭐ Shop", callback_data="shop_back")],
    ])

def kb_alloc():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💪 STR +1", callback_data="alloc_STR"),
         InlineKeyboardButton("🏃 AGI +1", callback_data="alloc_AGI")],
        [InlineKeyboardButton("❤️ VIT +1", callback_data="alloc_VIT"),
         InlineKeyboardButton("🧠 INT +1", callback_data="alloc_INT")],
        [InlineKeyboardButton("📊 Status", callback_data="view_status")],
    ])

def kb_reset_confirm():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚠️ Ya, Reset Semua", callback_data="do_reset"),
         InlineKeyboardButton("❌ Batal", callback_data="cancel_reset")],
    ])

def kb_boss():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Attack Boss", callback_data="do_attack"),
         InlineKeyboardButton("📊 Status", callback_data="view_status")],
    ])

def kb_back():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Status", callback_data="view_status"),
         InlineKeyboardButton("🎴 Quest", callback_data="view_quest")],
    ])

def kb_shop_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎨 Kosmetik", callback_data="shop_cat_cosmetic"),
         InlineKeyboardButton("⚡ Boost", callback_data="shop_cat_boost")],
        [InlineKeyboardButton("🛠️ QoL", callback_data="shop_cat_qol"),
         InlineKeyboardButton("🎰 Gacha", callback_data="shop_cat_gacha")],
        [InlineKeyboardButton("📦 Bundle", callback_data="shop_cat_bundle"),
         InlineKeyboardButton("📊 Status", callback_data="view_status")],
    ])

def kb_shop_items(cat):
    items = [(k, v) for k, v in SHOP_ITEMS.items() if v["cat"] == cat]
    rows = []
    for k, v in items:
        rows.append([InlineKeyboardButton(f"{v['name']} • {v['price']}⭐",
                    callback_data=f"buy_{k}")])
    rows.append([InlineKeyboardButton("⬅️ Kembali", callback_data="shop_back")])
    return InlineKeyboardMarkup(rows)

async def safe_edit(query, text, keyboard=None):
    try:
        await query.edit_message_text(text, parse_mode="HTML",
                                       reply_markup=keyboard,
                                       disable_web_page_preview=True)
    except Exception:
        await query.message.reply_text(text, parse_mode="HTML",
                                        reply_markup=keyboard,
                                        disable_web_page_preview=True)

# ================== COMMANDS ==================
async def start(update, context):
    u = update.effective_user
    name = u.username or u.first_name or "Hunter"
    create_user(u.id, name)
    row = get_user(u.id)
    msgs = []
    lm = check_daily_login(u.id)
    if lm: msgs.append(lm)
    pm = check_penalty(u.id, row)
    if pm: msgs.append(pm)
    welcome = (
        f"⚔️ <b>Selamat datang, Hunter {esc(name)}!</b>\n\n"
        "Naikkan rank <b>F</b> → <b>SSS</b>!\n"
        "Makin tinggi level, makin banyak quest/hari! 🎴\n\n"
        "⭐ Ada <b>Shop</b> pakai Telegram Stars!\n\n"
        "📌 Mulai dari /quest atau /status"
    )
    if msgs: welcome = "\n\n".join(msgs) + "\n\n" + welcome
    await update.message.reply_text(welcome, parse_mode="HTML", reply_markup=kb_status())

async def help_cmd(update, context):
    text = (
        "⚔️ <b>QUESTISM — COMMAND CENTER</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎯 <b>QUEST</b>\n"
        "/quest — Ambil quest harian\n"
        "/randomquest — Quest bonus\n"
        "/rest — Rest day (1x/minggu)\n\n"
        "📊 <b>PROGRESS</b>\n"
        "/status — Stats & rank\n"
        "/rank — Leaderboard\n"
        "/badges — Koleksi badge\n"
        "/allocate — Pakai stat point\n\n"
        "⭐ <b>SHOP</b>\n"
        "/shop — Buka shop Stars\n"
        "/inventory — Lihat inventory\n\n"
        "🐉 <b>BOSS RAID</b>\n"
        "/boss — Info boss (cooldown 1x/hari)\n"
        "/attack — Serang boss\n\n"
        "⚠️ /reset — Hapus progress\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎴 <b>Quest per level:</b>\n"
        "Lv 1-2 : 1 quest\nLv 3-5 : 2 quest\n"
        "Lv 6-10: 3 quest\nLv 11-20: 4 quest\n"
        "Lv 21+ : 5 quest\n\n"
        "✨ Selesaikan semua = <b>Perfect Day +100 EXP</b>!"
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb_status())

async def status(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu."); return
    msgs = []
    lm = check_daily_login(uid)
    if lm: msgs.append(lm)
    pm = check_penalty(uid, row)
    if pm: msgs.append(pm)
    row = get_user(uid)
    text = render_status_text(row)
    if msgs: text = "\n\n".join(msgs) + "\n\n" + text
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb_status())

async def quest(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu."); return
    pm = check_penalty(uid, row)
    if pm: await update.message.reply_text(pm, parse_mode="HTML")
    result = take_quests(uid)
    if result.get("error"):
        await update.message.reply_text(result["error"]); return
    quests = result["quests"]
    text = render_quests_list(quests)
    kb = kb_quests_list(quests) if any(not q["completed"] for q in quests) else kb_after_complete()
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)

async def random_quest(update, context):
    uid = update.effective_user.id
    if not get_user(uid):
        await update.message.reply_text("Ketik /start dulu."); return
    qtext, stat, reward = random.choice(RANDOM_QUESTS)
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute(f"UPDATE users SET {stat.lower()}={stat.lower()}+1 WHERE user_id=?", (uid,))
    conn.commit(); conn.close()
    leveled, new_level, sp = add_exp_and_levelup(uid, reward)
    msg = f"🎲 <b>RANDOM QUEST</b>\n🎯 {esc(qtext)}\n💎 +{reward} EXP, +1 {stat}"
    if leveled:
        msg += f"\n\n⬆️ <b>LEVEL UP!</b> Level {new_level} (+5 stat point)"
        msg += format_badge_msg(check_badges(uid, get_user(uid)))
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=kb_after_complete())

async def rest(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu."); return
    today = date.today()
    wk = f"{today.isocalendar()[0]}-{today.isocalendar()[1]}"
    if row[13] == wk:
        await update.message.reply_text("😴 Sudah rest minggu ini. Reset Senin."); return
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("""UPDATE users SET last_rest_week=?, last_quest_date=?,
                 quest_completed=1 WHERE user_id=?""",
              (wk, today.isoformat(), uid))
    conn.commit(); conn.close()
    await update.message.reply_text("😴 <b>REST DAY</b>\n\nHari ini bebas. Streak aman! 💪",
                                     parse_mode="HTML", reply_markup=kb_after_complete())

async def allocate(update, context):
    row = get_user(update.effective_user.id)
    if not row:
        await update.message.reply_text("Ketik /start dulu."); return
    if row[8] <= 0:
        await update.message.reply_text("❌ Gak punya stat point."); return
    await update.message.reply_text(
        f"🎯 Stat Points: <b>{row[8]}</b>\nPilih stat:",
        parse_mode="HTML", reply_markup=kb_alloc())

async def rank_cmd(update, context):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("""SELECT username, level, str+agi+vit+int AS total
                 FROM users ORDER BY total DESC LIMIT 10""")
    rows = c.fetchall(); conn.close()
    if not rows:
        await update.message.reply_text("Belum ada hunter."); return
    lines = ["🏆 <b>LEADERBOARD HUNTER</b>", "━━━━━━━━━━━━━━━━━━━"]
    medals = ["🥇", "🥈", "🥉"]
    for idx, (u, lvl, tot) in enumerate(rows):
        pre = medals[idx] if idx < 3 else f"{idx+1}."
        lines.append(f"{pre} {esc(u)} — [{get_rank(tot)}] Lv.{lvl} • {tot} pts")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML", reply_markup=kb_back())

async def badges_cmd(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu."); return
    owned = set((row[19] or "").split(",")) - {""} if len(row) > 19 else set()
    lines = [f"🏆 <b>KOLEKSI BADGE</b> ({len(owned)}/{len(BADGES)})", "━━━━━━━━━━━━━━━━━━━"]
    for k, (em, nm, dc) in BADGES.items():
        if k in owned: lines.append(f"✅ {em} <b>{nm}</b> — {dc}")
        else: lines.append(f"🔒 ??? — <i>tersembunyi</i>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML", reply_markup=kb_back())

async def boss_cmd(update, context):
    uid = update.effective_user.id
    if not get_user(uid):
        await update.message.reply_text("Ketik /start dulu."); return
    await update.message.reply_text(render_boss_text(uid), parse_mode="HTML", reply_markup=kb_boss())

async def attack(update, context):
    result = do_attack_logic(update.effective_user.id)
    if result.get("error"):
        await update.message.reply_text(result["error"]); return
    await update.message.reply_text(result["text"], parse_mode="HTML", reply_markup=kb_boss())

def do_attack_logic(uid):
    row = get_user(uid)
    if not row: return {"error": "Ketik /start dulu."}
    today = date.today().isoformat()
    last_attack = row[23] if len(row) > 23 else None
    if last_attack == today:
        return {"error": "⏳ Kamu sudah menyerang boss hari ini!\nCooldown reset jam 00:00."}
    week, hp, max_hp, defeated = get_or_spawn_boss()
    if defeated: return {"error": "💀 Boss minggu ini sudah kalah!"}
    total = row[4] + row[5] + row[6] + row[7]
    dmg = max(10, total // 4) + random.randint(10, 50)
    if has_active_boost(uid, "boost_boss"): dmg *= 2
    new_hp, defeated = add_boss_damage(uid, dmg)
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("UPDATE users SET last_attack_date=? WHERE user_id=?", (today, uid))
    conn.commit(); conn.close()
    msg = f"⚔️ <b>ATTACK!</b>\n\n💥 Damage: <b>{dmg}</b>\n❤️ Boss HP: {new_hp}/{BOSS_BASE_HP}"
    if new_hp <= 0 and not defeated:
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("UPDATE boss_state SET defeated=1 WHERE week=?", (week_key(),))
        conn.commit()
        c.execute("SELECT user_id FROM boss_damage WHERE week=?", (week_key(),))
        attackers = [r[0] for r in c.fetchall()]; conn.close()
        for a in attackers:
            add_exp_and_levelup(a, 500); unlock_badge(a, "boss_slayer")
        msg += "\n\n🎉 <b>BOSS DIKALAHKAN!</b> Semua dapat +500 EXP & 🐉!"
    msg += "\n\n⏳ <i>Cooldown reset besok jam 00:00</i>"
    return {"text": msg}

async def reset_cmd(update, context):
    await update.message.reply_text(
        "⚠️ <b>KONFIRMASI RESET</b>\n\nSemua progress akan dihapus!\n\n"
        "<b>⚠️ Tidak bisa dibatalkan!</b>",
        parse_mode="HTML", reply_markup=kb_reset_confirm())

async def shop_cmd(update, context):
    text = (
        "⭐ <b>QUESTISM SHOP</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Beli pakai <b>Telegram Stars</b> (⭐)\n"
        "Mayoritas kosmetik & boost sementara.\n"
        "<i>Tidak ada pay-to-win!</i>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Pilih kategori:"
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb_shop_main())

async def inventory_cmd(update, context):
    uid = update.effective_user.id
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT item_id, quantity FROM user_inventory WHERE user_id=? AND quantity>0", (uid,))
    inv = c.fetchall()
    c.execute("SELECT cosmetic_id FROM user_cosmetics WHERE user_id=?", (uid,))
    cos = [r[0] for r in c.fetchall()]
    c.execute("SELECT boost_id, expires_at FROM user_boosts WHERE user_id=?", (uid,))
    boosts = c.fetchall()
    conn.close()
    lines = ["🎒 <b>INVENTORY KAMU</b>", "━━━━━━━━━━━━━━━━━━━"]
    if inv:
        lines.append("<b>📦 Item:</b>")
        for iid, qty in inv:
            lines.append(f"• {SHOP_ITEMS.get(iid, {}).get('name', iid)} ×{qty}")
    if cos:
        lines.append("<b>🎨 Kosmetik:</b>")
        for cid in cos:
            lines.append(f"• {SHOP_ITEMS.get(cid, {}).get('name', cid)}")
    active = []
    for bid, exp in boosts:
        try:
            if datetime.fromisoformat(exp) > datetime.now():
                active.append(f"• {SHOP_ITEMS.get(bid, {}).get('name', bid)} → {exp[:16]}")
        except: pass
    if active:
        lines.append("<b>⚡ Boost Aktif:</b>")
        lines.extend(active)
    if len(lines) == 2:
        lines.append("<i>Inventory masih kosong.</i>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML",
                                     reply_markup=kb_shop_main())
  # ================== MAIN CALLBACKS ==================
async def callback_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = query.from_user.id

    if data.startswith("complete_"):
        try: slot = int(data.split("_", 1)[1])
        except: return
        result = complete_quest_slot(uid, slot)
        if result.get("error"):
            await query.answer(result["error"], show_alert=True); return
        quests = get_today_quests(uid) or []
        text = result["text"] + "\n\n" + render_quests_list(quests)
        kb = kb_quests_list(quests) if any(not q["completed"] for q in quests) else kb_after_complete()
        await safe_edit(query, text, kb)
        return

    if data == "view_status":
        row = get_user(uid)
        if not row: await safe_edit(query, "Ketik /start dulu."); return
        await safe_edit(query, render_status_text(row), kb_status()); return

    if data == "view_quest":
        result = take_quests(uid)
        if result.get("error"): await safe_edit(query, result["error"]); return
        quests = result["quests"]
        text = render_quests_list(quests)
        kb = kb_quests_list(quests) if any(not q["completed"] for q in quests) else kb_after_complete()
        await safe_edit(query, text, kb); return

    if data == "view_alloc":
        row = get_user(uid)
        if not row: await safe_edit(query, "Ketik /start dulu."); return
        if row[8] <= 0:
            await safe_edit(query, "❌ Belum punya stat point. Naikkan level!", kb_back()); return
        await safe_edit(query,
            f"🎯 Stat Points: <b>{row[8]}</b>\nPilih stat:", kb_alloc()); return

    if data.startswith("alloc_"):
        stat = data.split("_", 1)[1]
        if stat not in ("STR", "AGI", "VIT", "INT"): return
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("SELECT stat_points FROM users WHERE user_id=?", (uid,))
        r = c.fetchone()
        if not r or r[0] <= 0:
            await safe_edit(query, "❌ Habis.", kb_back()); conn.close(); return
        c.execute(f"UPDATE users SET stat_points=stat_points-1, "
                  f"{stat.lower()}={stat.lower()}+1 WHERE user_id=?", (uid,))
        conn.commit()
        c.execute("SELECT stat_points FROM users WHERE user_id=?", (uid,))
        nsp = c.fetchone()[0]; conn.close()
        if nsp <= 0: await safe_edit(query, f"✅ +1 {stat}. Habis.", kb_back())
        else: await safe_edit(query,
            f"✅ +1 {stat}!\n🎯 Sisa: <b>{nsp}</b>\n\nPilih lagi:", kb_alloc())
        return

    if data == "view_badges":
        row = get_user(uid)
        if not row: await safe_edit(query, "Ketik /start dulu."); return
        owned = set((row[19] or "").split(",")) - {""} if len(row) > 19 else set()
        lines = [f"🏆 <b>KOLEKSI BADGE</b> ({len(owned)}/{len(BADGES)})", "━━━━━━━━━━━━━━━━━━━"]
        for k, (em, nm, dc) in BADGES.items():
            if k in owned: lines.append(f"✅ {em} <b>{nm}</b> — {dc}")
            else: lines.append(f"🔒 ??? — <i>tersembunyi</i>")
        await safe_edit(query, "\n".join(lines), kb_back()); return

    if data == "view_rank":
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("""SELECT username, level, str+agi+vit+int AS total
                     FROM users ORDER BY total DESC LIMIT 10""")
        rows = c.fetchall(); conn.close()
        if not rows:
            await safe_edit(query, "Belum ada hunter.", kb_back()); return
        lines = ["🏆 <b>LEADERBOARD</b>", "━━━━━━━━━━━━━━━━━━━"]
        medals = ["🥇", "🥈", "🥉"]
        for idx, (u, lvl, tot) in enumerate(rows):
            pre = medals[idx] if idx < 3 else f"{idx+1}."
            lines.append(f"{pre} {esc(u)} — [{get_rank(tot)}] Lv.{lvl} • {tot} pts")
        await safe_edit(query, "\n".join(lines), kb_back()); return

    if data == "view_boss":
        await safe_edit(query, render_boss_text(uid), kb_boss()); return

    if data == "do_attack":
        result = do_attack_logic(uid)
        if result.get("error"):
            await query.answer(result["error"], show_alert=True); return
        await safe_edit(query, result["text"], kb_boss()); return

    if data == "view_randomquest":
        qtext, stat, reward = random.choice(RANDOM_QUESTS)
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute(f"UPDATE users SET {stat.lower()}={stat.lower()}+1 WHERE user_id=?", (uid,))
        conn.commit(); conn.close()
        leveled, new_level, sp = add_exp_and_levelup(uid, reward)
        msg = f"🎲 <b>RANDOM QUEST</b>\n🎯 {esc(qtext)}\n💎 +{reward} EXP, +1 {stat}"
        if leveled:
            msg += f"\n\n⬆️ <b>LEVEL UP!</b> Level {new_level} (+5 stat point)"
            msg += format_badge_msg(check_badges(uid, get_user(uid)))
        await safe_edit(query, msg, kb_after_complete()); return

    if data == "do_reset":
        reset_user(uid)
        await safe_edit(query,
            "✅ <b>RESET BERHASIL!</b>\n\nMulai petualangan baru! ⚔️",
            InlineKeyboardMarkup([[
                InlineKeyboardButton("🎴 Mulai Quest", callback_data="view_quest"),
                InlineKeyboardButton("📊 Status", callback_data="view_status")
            ]])); return

    if data == "cancel_reset":
        await safe_edit(query, "❌ Reset dibatalkan. Progress aman!", kb_status()); return

# ================== SHOP CALLBACKS ==================
async def shop_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "shop_back":
        text = ("⭐ <b>QUESTISM SHOP</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                "Beli pakai <b>Telegram Stars</b> (⭐)\nPilih kategori:")
        await safe_edit(query, text, kb_shop_main()); return

    if data.startswith("shop_cat_"):
        cat = data.replace("shop_cat_", "")
        if cat not in SHOP_CATEGORIES: return
        text = render_shop_category(cat) + "\n\n━━━━━━━━━━━━━━━━━━━━\nTap item untuk beli:"
        await safe_edit(query, text, kb_shop_items(cat)); return

async def buy_callback(update, context):
    query = update.callback_query
    await query.answer()
    item_id = query.data.replace("buy_", "")
    if item_id not in SHOP_ITEMS: return
    item = SHOP_ITEMS[item_id]
    if item["type"] == "permanent" and has_cosmetic(query.from_user.id, item_id):
        await query.answer("✅ Kamu sudah punya item ini!", show_alert=True)
        return
    await context.bot.send_invoice(
        chat_id=query.from_user.id,
        title=item["name"],
        description=item["desc"],
        payload=f"shop:{item_id}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=item["name"], amount=item["price"])],
    )

async def precheckout_callback(update, context):
    q = update.pre_checkout_query
    if not q.invoice_payload.startswith("shop:"):
        await q.answer(ok=False, error_message="Invalid payload"); return
    await q.answer(ok=True)

async def successful_payment_callback(update, context):
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    uid = update.effective_user.id
    if not payload.startswith("shop:"): return
    item_id = payload.split(":", 1)[1]
    result = process_purchase(uid, item_id)
    msg = f"🎉 <b>PEMBELIAN BERHASIL!</b>\n\n{result}"
    row = get_user(uid)
    if row: msg += format_badge_msg(check_badges(uid, row))
    await update.message.reply_text(msg, parse_mode="HTML",
                                     reply_markup=kb_shop_main())

# ================== BROADCAST & MAIN ==================
async def daily_broadcast(context):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [r[0] for r in c.fetchall()]; conn.close()
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid,
                text="🌅 <b>Quest baru tersedia!</b>\nKetik /quest untuk ambil misi.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎴 Ambil Quest", callback_data="view_quest")
                ]]))
        except Exception: pass

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("quest", quest))
    app.add_handler(CommandHandler("randomquest", random_quest))
    app.add_handler(CommandHandler("rest", rest))
    app.add_handler(CommandHandler("allocate", allocate))
    app.add_handler(CommandHandler("rank", rank_cmd))
    app.add_handler(CommandHandler("badges", badges_cmd))
    app.add_handler(CommandHandler("boss", boss_cmd))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CommandHandler("shop", shop_cmd))
    app.add_handler(CommandHandler("inventory", inventory_cmd))
    app.add_handler(CallbackQueryHandler(shop_callback, pattern=r"^shop_"))
    app.add_handler(CallbackQueryHandler(buy_callback, pattern=r"^buy_"))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    async def post_init(application):
        await application.bot.set_my_commands([
            BotCommand("start", "Mulai & daily login bonus"),
            BotCommand("status", "Lihat stats, rank, level"),
            BotCommand("quest", "Ambil quest harian"),
            BotCommand("randomquest", "Quest bonus random"),
            BotCommand("rest", "Rest day (1x/minggu)"),
            BotCommand("allocate", "Pakai stat point"),
            BotCommand("rank", "Leaderboard hunter"),
            BotCommand("badges", "Koleksi badge"),
            BotCommand("shop", "Buka shop Stars"),
            BotCommand("inventory", "Lihat inventory"),
            BotCommand("boss", "Info weekly boss"),
            BotCommand("attack", "Serang boss (1x/hari)"),
            BotCommand("reset", "Reset progress (hati-hati!)"),
            BotCommand("help", "Panduan lengkap"),
        ])
    app.post_init = post_init

    try:
        app.job_queue.run_daily(daily_broadcast, time=time(hour=7, minute=0))
        print("✅ JobQueue aktif", flush=True)
    except Exception as e:
        print(f"⚠️ JobQueue gagal: {e}", flush=True)

    print("⚔️ Bot Questism berjalan...", flush=True)
    app.run_polling()

if __name__ == "__main__":
    main()
