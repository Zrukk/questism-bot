import os
import sqlite3
import random
import html
from datetime import date, timedelta, time, datetime
from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup,
                      BotCommand)
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

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
    "F":   ["E", "E", "E", "D"],
    "E":   ["E", "D", "D", "D"],
    "D":   ["D", "D", "C", "C"],
    "C":   ["C", "C", "D", "B"],
    "B":   ["B", "B", "C", "A"],
    "A":   ["A", "A", "B", "S"],
    "S":   ["S", "S", "A", "SS"],
    "SS":  ["SS", "SS", "S", "SSS"],
    "SSS": ["SSS", "SSS", "SS", "SSS"],
}

QUEST_RANK_ICONS = {
    "E": "🟢", "D": "🔵", "C": "🟣", "B": "🟠",
    "A": "🔴", "S": "⭐", "SS": "🌟", "SSS": "💎",
}

RANDOM_QUESTS = [
    ("Minum 1 gelas air sekarang", "VIT", 30),
    ("Push-up 10x sekarang", "STR", 30),
    ("Jalan cepat 5 menit", "AGI", 30),
    ("Baca 3 halaman buku", "INT", 30),
    ("Senyum + afirmasi positif", "VIT", 20),
    ("Squat 15x sekarang", "STR", 35),
    ("Tarik napas dalam 10x", "VIT", 20),
]

RANK_TABLE = [
    (1000, "SSS"), (750, "SS"), (550, "S"), (400, "A"),
    (280, "B"), (180, "C"), (100, "D"), (50, "E"), (0, "F"),
]

BADGES = {
    "first_quest": ("🌱", "Langkah Pertama", "Selesaikan quest pertama"),
    "streak_7":    ("🔥", "Konsisten", "Streak 7 hari"),
    "streak_30":   ("💎", "Legenda", "Streak 30 hari"),
    "level_5":     ("⭐", "Pemula", "Capai Level 5"),
    "level_10":    ("🌟", "Ahli", "Capai Level 10"),
    "level_25":    ("💫", "Master", "Capai Level 25"),
    "rank_c":      ("🥉", "Pejuang", "Capai Rank C"),
    "rank_b":      ("🥈", "Ksatria", "Capai Rank B"),
    "rank_a":      ("🥇", "Elit", "Capai Rank A"),
    "rank_s":      ("👑", "Sang Raja", "Capai Rank S"),
    "quest_50":    ("📜", "Rajin", "Selesaikan 50 quest"),
    "quest_100":   ("📚", "Disiplin", "Selesaikan 100 quest"),
    "boss_slayer": ("🐉", "Pembunuh Naga", "Kalahkan Weekly Boss"),
    "hidden_finder":("🎰", "Penjelajah", "Temukan Hidden Quest"),
    "rank_ss":     ("⚡", "Overlord", "Capai Rank SS"),
    "rank_sss":    ("🌌", "Monarch", "Capai Rank SSS"),
}

BOSS_BASE_HP = 5000

def get_rank(total):
    for thresh, name in RANK_TABLE:
        if total >= thresh: return name
    return "F"

def exp_needed(level): return level * 100

def week_key(d=None):
    d = d or date.today()
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"

def pick_quest_for_rank(user_rank):
    quest_rank = random.choice(USER_RANK_TO_QUEST_RANKS.get(user_rank, ["E"]))
    stat = random.choice(["STR", "AGI", "VIT", "INT"])
    quest = random.choice(QUEST_DB[quest_rank][stat])
    return quest_rank, stat, quest

def pick_hidden_quest(user_rank):
    allowed = USER_RANK_TO_QUEST_RANKS.get(user_rank, ["E"])
    all_ranks = list(QUEST_DB.keys())
    highest_idx = max(all_ranks.index(r) for r in allowed)
    hidden_idx = min(highest_idx + 1, len(all_ranks) - 1)
    hidden_rank = all_ranks[hidden_idx]
    stat = random.choice(["STR", "AGI", "VIT", "INT"])
    quest = random.choice(QUEST_DB[hidden_rank][stat])
    return hidden_rank, stat, quest

def find_quest_reward(quest_rank, stat, quest_name):
    for q, exp, gain in QUEST_DB.get(quest_rank, {}).get(stat, []):
        if q == quest_name:
            return exp, gain
    return 100, 3

# ================== DATABASE ==================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
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
        current_quest_rank TEXT DEFAULT 'E')""")
    c.execute("""CREATE TABLE IF NOT EXISTS boss_state (
        week TEXT PRIMARY KEY, hp INTEGER, max_hp INTEGER,
        defeated INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS boss_damage (
        user_id INTEGER, week TEXT, damage INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, week))""")
    conn.commit()
    conn.close()
    migrate_db()

def migrate_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    existing = {row[1] for row in c.fetchall()}
    new_cols = [
        ("last_login_date", "TEXT"), ("login_streak", "INTEGER DEFAULT 0"),
        ("total_quests", "INTEGER DEFAULT 0"), ("badges", "TEXT DEFAULT ''"),
        ("last_penalty_date", "TEXT"), ("in_penalty", "INTEGER DEFAULT 0"),
        ("current_quest_rank", "TEXT DEFAULT 'E'"),
    ]
    for col, typ in new_cols:
        if col not in existing:
            try: c.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
            except sqlite3.OperationalError: pass
    conn.commit()
    conn.close()

def get_user(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    conn.close()
    return row

def create_user(uid, username):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)", (uid, username))
    conn.commit()
    conn.close()

def reset_user(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""UPDATE users SET
        level=1, exp=0, str=0, agi=0, vit=0, int=0, stat_points=0,
        last_quest_date=NULL, current_quest=NULL, current_quest_stat=NULL,
        quest_completed=0, last_rest_week=NULL, streak=0,
        last_complete_date=NULL, last_login_date=NULL, login_streak=0,
        total_quests=0, badges='', last_penalty_date=NULL, in_penalty=0,
        current_quest_rank='E' WHERE user_id=?""", (uid,))
    c.execute("DELETE FROM boss_damage WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

def add_exp_and_levelup(uid, amount):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT level, exp, stat_points FROM users WHERE user_id=?", (uid,))
    level, exp, sp = c.fetchone()
    exp = max(0, exp + amount)
    leveled = 0
    while exp >= exp_needed(level):
        exp -= exp_needed(level)
        level += 1
        sp += 5
        leveled += 1
    c.execute("UPDATE users SET level=?, exp=?, stat_points=? WHERE user_id=?",
              (level, exp, sp, uid))
    conn.commit()
    conn.close()
    return leveled, level, sp

# ================== HELPER ==================
def check_daily_login(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT last_login_date, login_streak FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    if not row:
        conn.close(); return None
    last_login, streak = row
    today = date.today().isoformat()
    if last_login == today:
        conn.close(); return None
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    new_streak = streak + 1 if last_login == yesterday else 1
    bonus = min(new_streak * 10, 100)
    c.execute("UPDATE users SET last_login_date=?, login_streak=? WHERE user_id=?",
              (today, new_streak, uid))
    conn.commit()
    conn.close()
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
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute(f"""UPDATE users SET exp=MAX(0, exp-100),
                     {stat}=MAX(0, {stat}-2), in_penalty=1,
                     last_penalty_date=? WHERE user_id=?""",
                  (date.today().isoformat(), uid))
        conn.commit()
        conn.close()
        return (f"🚨 <b>PENALTY ZONE!</b>\n\n"
                f"Bolos {days_missed} hari!\n💔 -100 EXP\n💔 -2 {stat.upper()}\n\n"
                f"Selesaikan 1 quest untuk keluar.")
    return None

def check_badges(uid, row):
    if len(row) < 20: return []
    owned = set((row[19] or "").split(",")) - {""}
    total_stats = row[4] + row[5] + row[6] + row[7]
    total_quests = row[18] if len(row) > 18 else 0
    checks = {
        "first_quest": total_quests >= 1,
        "streak_7": row[14] >= 7, "streak_30": row[14] >= 30,
        "level_5": row[2] >= 5, "level_10": row[2] >= 10, "level_25": row[2] >= 25,
        "rank_c": total_stats >= 180, "rank_b": total_stats >= 280,
        "rank_a": total_stats >= 400, "rank_s": total_stats >= 550,
        "rank_ss": total_stats >= 750, "rank_sss": total_stats >= 1000,
        "quest_50": total_quests >= 50, "quest_100": total_quests >= 100,
    }
    new_badges = []
    for key, ok in checks.items():
        if ok and key not in owned:
            new_badges.append(key); owned.add(key)
    if new_badges:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("UPDATE users SET badges=? WHERE user_id=?",
                  (",".join(sorted(owned)), uid))
        conn.commit()
        conn.close()
    return new_badges

def unlock_badge(uid, key):
    row = get_user(uid)
    if not row or len(row) < 20: return False
    owned = set((row[19] or "").split(",")) - {""}
    if key in owned: return False
    owned.add(key)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE users SET badges=? WHERE user_id=?", (",".join(sorted(owned)), uid))
    conn.commit()
    conn.close()
    return True

def format_badge_msg(keys):
    if not keys: return ""
    lines = ["\n\n🏆 <b>BADGE BARU UNLOCKED!</b>"]
    for k in keys:
        if k in BADGES:
            emoji, name, desc = BADGES[k]
            lines.append(f"{emoji} <b>{name}</b> — {desc}")
    return "\n".join(lines)

# ================== BOSS RAID ==================
def get_or_spawn_boss():
    week = week_key()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT week, hp, max_hp, defeated FROM boss_state WHERE week=?", (week,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO boss_state (week, hp, max_hp, defeated) VALUES (?,?,?,0)",
                  (week, BOSS_BASE_HP, BOSS_BASE_HP))
        conn.commit()
        row = (week, BOSS_BASE_HP, BOSS_BASE_HP, 0)
    conn.close()
    return row

def add_boss_damage(uid, dmg):
    week = week_key()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT damage FROM boss_damage WHERE user_id=? AND week=?", (uid, week))
    if c.fetchone():
        c.execute("UPDATE boss_damage SET damage=damage+? WHERE user_id=? AND week=?",
                  (dmg, uid, week))
    else:
        c.execute("INSERT INTO boss_damage (user_id, week, damage) VALUES (?,?,?)",
                  (uid, week, dmg))
    c.execute("UPDATE boss_state SET hp = MAX(0, hp - ?) WHERE week=?", (dmg, week))
    c.execute("SELECT hp, defeated FROM boss_state WHERE week=?", (week,))
    hp, defeated = c.fetchone()
    conn.commit()
    conn.close()
    return hp, defeated

# ================== RENDERERS ==================
def render_quest_card(quest_rank, stat, quest_name, exp_reward, stat_gain, is_hidden=False):
    icon = QUEST_RANK_ICONS.get(quest_rank, "❓")
    title = "🎰 HIDDEN QUEST" if is_hidden else "🎴 DAILY QUEST"
    line = "━━━━━━━━━━━━━━━━━━━━"
    stat_icon = {"STR": "💪", "AGI": "🏃", "VIT": "❤️", "INT": "🧠"}.get(stat, "❓")
    return (
        f"<pre>{line}\n"
        f"  {title}\n"
        f"{line}\n"
        f"{icon} Rank     : 【 {quest_rank} 】\n"
        f"{stat_icon} Kategori : {stat}\n"
        f"📜 Misi     : {esc(quest_name)}\n"
        f"{line}\n"
        f"💎 Reward   : +{exp_reward} EXP\n"
        f"📈 Bonus    : +{stat_gain} {stat}\n"
        f"{line}</pre>"
    )

def render_status_text(row):
    (_, username, level, exp, s, a, v, i, sp, *_rest) = row
    total = s + a + v + i
    rank = get_rank(total)
    need = exp_needed(level)
    filled = int((exp / need) * 10) if need else 0
    bar = "█" * filled + "░" * (10 - filled)
    badges_count = len([b for b in (row[19] or "").split(",") if b]) if len(row) > 19 else 0
    in_penalty = row[21] if len(row) > 21 else 0
    penalty_label = " ⚠️ <b>PENALTY</b>" if in_penalty else ""
    allowed_ranks = sorted(set(USER_RANK_TO_QUEST_RANKS.get(rank, ["E"])))

    return (
        f"📊 <b>STATUS HUNTER</b>{penalty_label}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {esc(username)}\n"
        f"🏅 Rank: <b>{rank}</b>\n"
        f"⭐ Level: <b>{level}</b>\n"
        f"✨ EXP: {exp}/{need}\n"
        f"   [{bar}]\n"
        f"🔥 Streak: {row[14]} hari\n"
        f"🎁 Login streak: {row[17] if len(row) > 17 else 0} hari\n"
        f"🏆 Badge: {badges_count}/{len(BADGES)}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💪 STR: {s}\n🏃 AGI: {a}\n❤️ VIT: {v}\n🧠 INT: {i}\n"
        f"📈 Total Stats: <b>{total}</b>\n"
        f"🎯 Stat Points: <b>{sp}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎴 Quest rank tersedia: {' • '.join(allowed_ranks)}"
)
    # ================== KEYBOARDS ==================
def kb_quest_card():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Selesai", callback_data="do_complete"),
         InlineKeyboardButton("📊 Status", callback_data="view_status")],
    ])

def kb_after_complete():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Status", callback_data="view_status"),
         InlineKeyboardButton("🎯 Allocate", callback_data="view_alloc")],
        [InlineKeyboardButton("🎲 Random Quest", callback_data="view_randomquest"),
         InlineKeyboardButton("🐉 Boss Raid", callback_data="view_boss")],
    ])

def kb_status():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎴 Quest", callback_data="view_quest"),
         InlineKeyboardButton("🎯 Allocate", callback_data="view_alloc")],
        [InlineKeyboardButton("🏆 Badge", callback_data="view_badges"),
         InlineKeyboardButton("🐉 Boss", callback_data="view_boss")],
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
    login_msg = check_daily_login(u.id)
    if login_msg: msgs.append(login_msg)
    penalty_msg = check_penalty(u.id, row)
    if penalty_msg: msgs.append(penalty_msg)

    welcome = (
        f"⚔️ <b>Selamat datang, Hunter {esc(name)}!</b>\n\n"
        "Sistem Questism aktif. Naikkan rank <b>F</b> → <b>SSS</b>!\n\n"
        "💡 <i>Ketik / untuk lihat semua command</i>\n"
        "📌 Mulai dari /quest atau cek /status"
    )
    if msgs:
        welcome = "\n\n".join(msgs) + "\n\n" + welcome
    await update.message.reply_text(welcome, parse_mode="HTML",
                                     reply_markup=kb_status())

async def help_cmd(update, context):
    text = (
        "⚔️ <b>QUESTISM BOT — COMMAND CENTER</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎯 <b>QUEST</b>\n"
        "/quest — Ambil quest harian\n"
        "/complete — Selesaikan (atau tap tombol ✅)\n"
        "/randomquest — Quest bonus random\n"
        "/rest — Rest day (1x/minggu)\n\n"
        "📊 <b>PROGRESS</b>\n"
        "/status — Stats, rank, level, badge\n"
        "/rank — Leaderboard hunter\n"
        "/badges — Koleksi badge\n"
        "/allocate — Pakai stat point\n\n"
        "🐉 <b>BOSS RAID</b>\n"
        "/boss — Info boss minggu ini\n"
        "/attack — Serang boss\n\n"
        "⚠️ <b>LAINNYA</b>\n"
        "/reset — Reset semua progress\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Ketik / untuk lihat menu command</i>"
    )
    await update.message.reply_text(text, parse_mode="HTML",
                                     reply_markup=kb_status())

async def status(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu ya."); return

    msgs = []
    login_msg = check_daily_login(uid)
    if login_msg: msgs.append(login_msg)
    penalty_msg = check_penalty(uid, row)
    if penalty_msg: msgs.append(penalty_msg)

    row = get_user(uid)
    text = render_status_text(row)
    if msgs:
        text = "\n\n".join(msgs) + "\n\n" + text
    await update.message.reply_text(text, parse_mode="HTML",
                                     reply_markup=kb_status())

async def quest(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu."); return

    penalty_msg = check_penalty(uid, row)
    if penalty_msg:
        await update.message.reply_text(penalty_msg, parse_mode="HTML")

    row = get_user(uid)
    today = date.today().isoformat()
    lqd, cq, cqs, qc = row[9], row[10], row[11], row[12]

    if lqd == today:
        if qc:
            await update.message.reply_text(
                "✅ Quest hari ini selesai!\nCoba Random Quest atau Attack Boss.",
                reply_markup=kb_after_complete())
        else:
            quest_rank = row[22] if len(row) > 22 else "E"
            exp_r, gain_r = find_quest_reward(quest_rank, cqs, cq)
            card = render_quest_card(quest_rank, cqs, cq, exp_r, gain_r)
            await update.message.reply_text(
                card + "\n\nTap tombol ✅ kalau sudah selesai!",
                parse_mode="HTML", reply_markup=kb_quest_card())
        return

    total_stats = row[4] + row[5] + row[6] + row[7]
    user_rank = get_rank(total_stats)

    is_hidden = random.random() < 0.10
    if is_hidden:
        quest_rank, stat, (qname, qexp, qgain) = pick_hidden_quest(user_rank)
        exp_reward = qexp * 2
        stat_gain = qgain + 2
    else:
        quest_rank, stat, (qname, qexp, qgain) = pick_quest_for_rank(user_rank)
        exp_reward = qexp
        stat_gain = qgain

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""UPDATE users SET last_quest_date=?, current_quest=?,
                 current_quest_stat=?, quest_completed=0,
                 current_quest_rank=? WHERE user_id=?""",
              (today, qname, stat, quest_rank, uid))
    conn.commit()
    conn.close()

    card = render_quest_card(quest_rank, stat, qname, exp_reward, stat_gain, is_hidden)
    footer = "\n\nTap tombol ✅ kalau sudah selesai!"
    if is_hidden:
        footer = "\n\n⚡ <b>Hidden Quest 2x reward!</b> Tap ✅ untuk klaim."
    await update.message.reply_text(card + footer, parse_mode="HTML",
                                     reply_markup=kb_quest_card())

async def complete(update, context):
    uid = update.effective_user.id
    result = do_complete_logic(uid)
    if result["error"]:
        await update.message.reply_text(result["error"]); return
    await update.message.reply_text(result["text"], parse_mode="HTML",
                                     reply_markup=kb_after_complete())

def do_complete_logic(uid):
    row = get_user(uid)
    if not row:
        return {"error": "Ketik /start dulu.", "text": None}

    today = date.today().isoformat()
    lqd, cq, cqs, qc = row[9], row[10], row[11], row[12]
    quest_rank = row[22] if len(row) > 22 else "E"

    if lqd != today or not cq:
        return {"error": "❌ Belum ada quest. Ketik /quest dulu.", "text": None}
    if qc:
        return {"error": "✅ Quest ini sudah kamu selesaikan hari ini.", "text": None}

    exp_r, gain_r = find_quest_reward(quest_rank, cqs, cq)
    is_hidden = exp_r >= 150 and gain_r >= 4

    streak = row[14]
    lcd = row[15]
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    new_streak = streak + 1 if lcd == yesterday else 1
    streak_bonus = 20 if new_streak % 7 == 0 else 0
    in_penalty = row[21] if len(row) > 21 else 0
    penalty_mult = 0.5 if in_penalty else 1.0
    total_exp = int((exp_r + streak_bonus) * penalty_mult)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    stat_col = cqs.lower()
    c.execute(f"""UPDATE users SET quest_completed=1, streak=?, last_complete_date=?,
                  {stat_col}={stat_col}+?, total_quests=total_quests+1,
                  in_penalty=0 WHERE user_id=?""",
              (new_streak, today, gain_r, uid))
    conn.commit()
    conn.close()

    leveled, new_level, sp = add_exp_and_levelup(uid, total_exp)

    icon = QUEST_RANK_ICONS.get(quest_rank, "❓")
    msg = (f"🎉 <b>QUEST COMPLETE!</b>\n\n"
           f"{icon} Rank Quest: <b>{quest_rank}</b>\n"
           f"💎 +{total_exp} EXP\n"
           f"📈 +{gain_r} {cqs}")

    if is_hidden:
        msg += f"\n🎰 <b>Hidden Quest Bonus!</b>"
        unlock_badge(uid, "hidden_finder")
    if in_penalty:
        msg += "\n\n✅ <b>Kamu keluar dari Penalty Zone!</b>"
    if streak_bonus:
        msg += f"\n🔥 Streak 7-hari: +{streak_bonus} EXP"
    msg += f"\n🔥 Streak: {new_streak} hari"
    if leveled:
        msg += f"\n\n⬆️ <b>LEVEL UP!</b> Level {new_level}\n🎁 +{leveled * 5} Stat Points"

    row2 = get_user(uid)
    new_badges = check_badges(uid, row2)
    msg += format_badge_msg(new_badges)
    return {"error": None, "text": msg}

async def random_quest(update, context):
    uid = update.effective_user.id
    if not get_user(uid):
        await update.message.reply_text("Ketik /start dulu."); return
    qtext, stat, reward = random.choice(RANDOM_QUESTS)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(f"UPDATE users SET {stat.lower()}={stat.lower()}+1 WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()
    leveled, new_level, sp = add_exp_and_levelup(uid, reward)

    msg = f"🎲 <b>RANDOM QUEST</b>\n🎯 {esc(qtext)}\n💎 +{reward} EXP, +1 {stat}"
    if leveled:
        msg += f"\n\n⬆️ <b>LEVEL UP!</b> Level {new_level} (+5 stat point)"
        row2 = get_user(uid)
        msg += format_badge_msg(check_badges(uid, row2))
    await update.message.reply_text(msg, parse_mode="HTML",
                                     reply_markup=kb_after_complete())

async def rest(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu."); return
    today = date.today()
    week_str = f"{today.isocalendar()[0]}-{today.isocalendar()[1]}"
    if row[13] == week_str:
        await update.message.reply_text("😴 Sudah pakai rest minggu ini. Reset Senin."); return
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""UPDATE users SET last_rest_week=?, last_quest_date=?,
                 current_quest=NULL, quest_completed=1 WHERE user_id=?""",
              (week_str, today.isoformat(), uid))
    conn.commit()
    conn.close()
    await update.message.reply_text(
        "😴 <b>REST DAY</b>\n\nHari ini bebas. Streak aman! 💪",
        parse_mode="HTML", reply_markup=kb_after_complete())

async def allocate(update, context):
    row = get_user(update.effective_user.id)
    if not row:
        await update.message.reply_text("Ketik /start dulu."); return
    if row[8] <= 0:
        await update.message.reply_text("❌ Gak punya stat point. Naikkan level dulu!");
        return
    await update.message.reply_text(
        f"🎯 Stat Points: <b>{row[8]}</b>\nPilih stat yang mau dinaikkan:",
        parse_mode="HTML", reply_markup=kb_alloc())

async def rank_cmd(update, context):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""SELECT username, level, str+agi+vit+int AS total
                 FROM users ORDER BY total DESC LIMIT 10""")
    rows = c.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("Belum ada hunter."); return
    lines = ["🏆 <b>LEADERBOARD HUNTER</b>", "━━━━━━━━━━━━━━━━━━━"]
    medals = ["🥇", "🥈", "🥉"]
    for idx, (uname, lvl, tot) in enumerate(rows):
        prefix = medals[idx] if idx < 3 else f"{idx+1}."
        lines.append(f"{prefix} {esc(uname)} — [{get_rank(tot)}] Lv.{lvl} • {tot} pts")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

async def badges_cmd(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu."); return
    owned = set((row[19] or "").split(",")) - {""} if len(row) > 19 else set()
    lines = [f"🏆 <b>KOLEKSI BADGE</b> ({len(owned)}/{len(BADGES)})",
             "━━━━━━━━━━━━━━━━━━━"]
    for key, (emoji, name, desc) in BADGES.items():
        if key in owned:
            lines.append(f"✅ {emoji} <b>{name}</b> — {desc}")
        else:
            lines.append(f"🔒 ??? — <i>tersembunyi</i>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML",
                                     reply_markup=kb_back())

async def boss_cmd(update, context):
    uid = update.effective_user.id
    if not get_user(uid):
        await update.message.reply_text("Ketik /start dulu."); return
    text = render_boss_text(uid)
    await update.message.reply_text(text, parse_mode="HTML",
                                     reply_markup=kb_boss())

def render_boss_text(uid):
    week, hp, max_hp, defeated = get_or_spawn_boss()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT damage FROM boss_damage WHERE user_id=? AND week=?", (uid, week))
    r = c.fetchone()
    my_dmg = r[0] if r else 0
    c.execute("""SELECT u.username, bd.damage FROM boss_damage bd
                 JOIN users u ON u.user_id = bd.user_id
                 WHERE bd.week=? ORDER BY bd.damage DESC LIMIT 5""", (week,))
    top = c.fetchall()
    conn.close()

    pct = int((hp / max_hp) * 100) if max_hp else 0
    filled = int((hp / max_hp) * 10) if max_hp else 0
    bar = "█" * filled + "░" * (10 - filled)
    status = "💀 <b>DIKALAHKAN</b>" if defeated else "⚔️ <b>MASIH HIDUP</b>"

    lines = [f"🐉 <b>WEEKLY BOSS RAID</b>",
             f"Minggu: {week}",
             f"━━━━━━━━━━━━━━━━━━━",
             f"👹 <b>Raja Kegelapan</b>",
             f"❤️ HP: {hp}/{max_hp} ({pct}%)",
             f"   [{bar}]", f"{status}",
             f"━━━━━━━━━━━━━━━━━━━",
             f"⚔️ Damage kamu: <b>{my_dmg}</b>",
             f"", f"🏅 <b>Top Attackers:</b>"]
    if top:
        for idx, (uname, dmg) in enumerate(top):
            lines.append(f"{idx+1}. {esc(uname)} — {dmg} dmg")
    else:
        lines.append("<i>Belum ada yang nyerang</i>")
    return "\n".join(lines)

async def attack(update, context):
    uid = update.effective_user.id
    result = do_attack_logic(uid)
    if result.get("error"):
        await update.message.reply_text(result["error"]); return
    await update.message.reply_text(result["text"], parse_mode="HTML",
                                     reply_markup=kb_boss())

def do_attack_logic(uid):
    row = get_user(uid)
    if not row:
        return {"error": "Ketik /start dulu."}
    week, hp, max_hp, defeated = get_or_spawn_boss()
    if defeated:
        return {"error": "💀 Boss minggu ini sudah kalah! Boss baru Senin depan."}

    total = row[4] + row[5] + row[6] + row[7]
    base_dmg = max(10, total // 4)
    bonus = random.randint(10, 50)
    dmg = base_dmg + bonus

    new_hp, defeated = add_boss_damage(uid, dmg)

    msg = (f"⚔️ <b>ATTACK!</b>\n\n"
           f"💥 Damage: <b>{dmg}</b>\n"
           f"❤️ Boss HP: {new_hp}/{BOSS_BASE_HP}")

    if new_hp <= 0 and not defeated:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("UPDATE boss_state SET defeated=1 WHERE week=?", (week_key(),))
        conn.commit()
        conn.close()
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT user_id FROM boss_damage WHERE week=?", (week_key(),))
        attackers = [r[0] for r in c.fetchall()]
        conn.close()
        for a_uid in attackers:
            add_exp_and_levelup(a_uid, 500)
            unlock_badge(a_uid, "boss_slayer")
        msg += f"\n\n🎉 <b>BOSS DIKALAHKAN!</b>\nSemua penyerang dapat <b>+500 EXP</b> & badge 🐉!"
    return {"text": msg}

async def reset_cmd(update, context):
    await update.message.reply_text(
        "⚠️ <b>KONFIRMASI RESET</b>\n\n"
        "Kamu akan <b>menghapus SEMUA progress</b>:\n"
        "• Level, EXP, Stats\n"
        "• Badge yang sudah dikumpulkan\n"
        "• Streak & riwayat quest\n"
        "• Damage boss\n\n"
        "<b>⚠️ Tindakan ini tidak bisa dibatalkan!</b>",
        parse_mode="HTML", reply_markup=kb_reset_confirm())

# ================== CALLBACK HANDLERS ==================
async def callback_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = query.from_user.id

    if data == "do_complete":
        result = do_complete_logic(uid)
        if result["error"]:
            await query.answer(result["error"], show_alert=True)
            return
        await safe_edit(query, result["text"], kb_after_complete())
        return

    if data == "view_status":
        row = get_user(uid)
        if not row:
            await safe_edit(query, "Ketik /start dulu."); return
        text = render_status_text(row)
        await safe_edit(query, text, kb_status())
        return

    if data == "view_quest":
        row = get_user(uid)
        if not row:
            await safe_edit(query, "Ketik /start dulu."); return
        today = date.today().isoformat()
        lqd, cq, cqs, qc = row[9], row[10], row[11], row[12]
        if lqd == today and cq:
            if qc:
                await safe_edit(query,
                    "✅ Quest hari ini selesai!\nCoba Random Quest atau Attack Boss.",
                    kb_after_complete())
            else:
                quest_rank = row[22] if len(row) > 22 else "E"
                exp_r, gain_r = find_quest_reward(quest_rank, cqs, cq)
                card = render_quest_card(quest_rank, cqs, cq, exp_r, gain_r)
                await safe_edit(query,
                    card + "\n\nTap tombol ✅ kalau sudah selesai!",
                    kb_quest_card())
        else:
            await safe_edit(query,
                "📜 Belum ada quest hari ini.\nKetik /quest untuk mengambil!",
                InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎴 Ambil Quest", callback_data="do_quest")
                ]]))
        return

    if data == "do_quest":
        row = get_user(uid)
        if not row:
            await safe_edit(query, "Ketik /start dulu."); return
        today = date.today().isoformat()
        if row[9] == today and row[10]:
            await query.answer("Kamu sudah punya quest hari ini!", show_alert=True)
            return
        total_stats = row[4] + row[5] + row[6] + row[7]
        user_rank = get_rank(total_stats)
        is_hidden = random.random() < 0.10
        if is_hidden:
            quest_rank, stat, (qname, qexp, qgain) = pick_hidden_quest(user_rank)
            exp_reward = qexp * 2
            stat_gain = qgain + 2
        else:
            quest_rank, stat, (qname, qexp, qgain) = pick_quest_for_rank(user_rank)
            exp_reward = qexp
            stat_gain = qgain
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("""UPDATE users SET last_quest_date=?, current_quest=?,
                     current_quest_stat=?, quest_completed=0,
                     current_quest_rank=? WHERE user_id=?""",
                  (today, qname, stat, quest_rank, uid))
        conn.commit()
        conn.close()
        card = render_quest_card(quest_rank, stat, qname, exp_reward, stat_gain, is_hidden)
        footer = "\n\nTap tombol ✅ kalau sudah selesai!"
        if is_hidden:
            footer = "\n\n⚡ <b>Hidden Quest 2x reward!</b> Tap ✅ untuk klaim."
        await safe_edit(query, card + footer, kb_quest_card())
        return

    if data == "view_alloc":
        row = get_user(uid)
        if not row:
            await safe_edit(query, "Ketik /start dulu."); return
        if row[8] <= 0:
            await safe_edit(query,
                "❌ Kamu belum punya stat point.\nNaikkan level dengan quest dulu!",
                kb_back())
            return
        await safe_edit(query,
            f"🎯 Stat Points: <b>{row[8]}</b>\nPilih stat yang mau dinaikkan:",
            kb_alloc())
        return

    if data.startswith("alloc_"):
        stat = data.split("_", 1)[1]
        if stat not in ("STR", "AGI", "VIT", "INT"): return
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT stat_points FROM users WHERE user_id=?", (uid,))
        r = c.fetchone()
        if not r or r[0] <= 0:
            await safe_edit(query, "❌ Stat point habis.", kb_back())
            conn.close(); return
        c.execute(f"UPDATE users SET stat_points=stat_points-1, "
                  f"{stat.lower()}={stat.lower()}+1 WHERE user_id=?", (uid,))
        conn.commit()
        c.execute("SELECT stat_points FROM users WHERE user_id=?", (uid,))
        new_sp = c.fetchone()[0]
        conn.close()
        if new_sp <= 0:
            await safe_edit(query, f"✅ +1 {stat}. Stat point habis.", kb_back())
        else:
            await safe_edit(query,
                f"✅ +1 {stat}!\n🎯 Sisa Stat Points: <b>{new_sp}</b>\n\nPilih lagi:",
                kb_alloc())
        return

    if data == "view_badges":
        row = get_user(uid)
        if not row:
            await safe_edit(query, "Ketik /start dulu."); return
        owned = set((row[19] or "").split(",")) - {""} if len(row) > 19 else set()
        lines = [f"🏆 <b>KOLEKSI BADGE</b> ({len(owned)}/{len(BADGES)})",
                 "━━━━━━━━━━━━━━━━━━━"]
        for key, (emoji, name, desc) in BADGES.items():
            if key in owned:
                lines.append(f"✅ {emoji} <b>{name}</b> — {desc}")
            else:
                lines.append(f"🔒 ??? — <i>tersembunyi</i>")
        await safe_edit(query, "\n".join(lines), kb_back())
        return

    if data == "view_boss":
        text = render_boss_text(uid)
        await safe_edit(query, text, kb_boss())
        return

    if data == "do_attack":
        result = do_attack_logic(uid)
        if result.get("error"):
            await query.answer(result["error"], show_alert=True)
            return
        await safe_edit(query, result["text"], kb_boss())
        return

    if data == "view_randomquest":
        qtext, stat, reward = random.choice(RANDOM_QUESTS)
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute(f"UPDATE users SET {stat.lower()}={stat.lower()}+1 WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        leveled, new_level, sp = add_exp_and_levelup(uid, reward)
        msg = f"🎲 <b>RANDOM QUEST</b>\n🎯 {esc(qtext)}\n💎 +{reward} EXP, +1 {stat}"
        if leveled:
            msg += f"\n\n⬆️ <b>LEVEL UP!</b> Level {new_level} (+5 stat point)"
            row2 = get_user(uid)
            msg += format_badge_msg(check_badges(uid, row2))
        await safe_edit(query, msg, kb_after_complete())
        return

    if data == "do_reset":
        reset_user(uid)
        await safe_edit(query,
            "✅ <b>RESET BERHASIL!</b>\n\n"
            "Semua progress kamu sudah dihapus.\n"
            "Ketik /quest untuk memulai petualangan baru! ⚔️",
            InlineKeyboardMarkup([[
                InlineKeyboardButton("🎴 Mulai Quest", callback_data="do_quest"),
                InlineKeyboardButton("📊 Status", callback_data="view_status")
            ]]))
        return

    if data == "cancel_reset":
        await safe_edit(query, "❌ Reset dibatalkan. Progress kamu aman!", kb_status())
        return

# ================== DAILY BROADCAST ==================
async def daily_broadcast(context):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [r[0] for r in c.fetchall()]
    conn.close()
    for uid in users:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text="🌅 <b>Quest baru tersedia!</b>\nKetik /quest untuk ambil misi.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎴 Ambil Quest", callback_data="do_quest")
                ]]))
        except Exception:
            pass

# ================== MAIN ==================
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("quest", quest))
    app.add_handler(CommandHandler("complete", complete))
    app.add_handler(CommandHandler("randomquest", random_quest))
    app.add_handler(CommandHandler("rest", rest))
    app.add_handler(CommandHandler("allocate", allocate))
    app.add_handler(CommandHandler("rank", rank_cmd))
    app.add_handler(CommandHandler("badges", badges_cmd))
    app.add_handler(CommandHandler("boss", boss_cmd))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))

    async def post_init(application):
        await application.bot.set_my_commands([
            BotCommand("start", "Mulai & dapat daily login bonus"),
            BotCommand("status", "Lihat stats, rank, level, badge"),
            BotCommand("quest", "Ambil quest harian sesuai rank"),
            BotCommand("complete", "Selesaikan quest hari ini"),
            BotCommand("randomquest", "Quest bonus random"),
            BotCommand("rest", "Rest day (1x per minggu)"),
            BotCommand("allocate", "Pakai stat point"),
            BotCommand("rank", "Leaderboard hunter terkuat"),
            BotCommand("badges", "Koleksi badge kamu"),
            BotCommand("boss", "Info weekly boss raid"),
            BotCommand("attack", "Serang boss untuk bonus EXP"),
            BotCommand("reset", "Reset semua progress (hati-hati!)"),
            BotCommand("help", "Panduan lengkap cara main"),
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
