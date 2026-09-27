import sqlite3, random, html
from datetime import date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8950239574:AAGv35FGNgU3ZzKhObPZea6E55oBCprAou4"   # <-- GANTI INI

DB = "/content/questism.db"
def esc(s): return html.escape(str(s))

QUESTS = {
    "STR": [("100 Push-up", 100), ("50 Pull-up", 120), ("100 Squat", 100),
            ("Plank 3 menit", 90), ("Angkat beban 30 menit", 110)],
    "AGI": [("Lari 5 km", 110), ("Sprint 10x100m", 100), ("Stretching 20 menit", 80),
            ("Lompat tali 500x", 100), ("Yoga 30 menit", 90)],
    "VIT": [("Tidur 8 jam", 90), ("Minum air 2 liter", 80), ("Makan sehat 3x", 90),
            ("Puasa gula 1 hari", 110), ("Meditasi 15 menit", 80)],
    "INT": [("Baca buku 30 menit", 100), ("Belajar skill baru 1 jam", 120),
            ("Tulis jurnal hari ini", 80), ("Selesaikan 3 masalah coding/math", 120),
            ("Hafal 10 kosakata baru", 90)],
}

RANDOM_QUESTS = [
    ("Minum 1 gelas air sekarang", "VIT", 30),
    ("Push-up 20x sekarang", "STR", 30),
    ("Jalan cepat 10 menit", "AGI", 30),
    ("Baca 5 halaman buku", "INT", 30),
    ("Senyum + afirmasi positif", "VIT", 20),
    ("Squat 30x sekarang", "STR", 35),
]

RANK_TABLE = [
    (1000, "SSS"), (750, "SS"), (550, "S"), (400, "A"),
    (280, "B"), (180, "C"), (100, "D"), (50, "E"), (0, "F"),
]

def get_rank(total):
    for thresh, name in RANK_TABLE:
        if total >= thresh: return name
    return "F"

def exp_needed(level): return level * 100

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
        streak INTEGER DEFAULT 0, last_complete_date TEXT)""")
    conn.commit(); conn.close()

def get_user(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = c.fetchone(); conn.close(); return row

def create_user(uid, username):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)", (uid, username))
    conn.commit(); conn.close()

def add_exp_and_levelup(uid, amount):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT level, exp, stat_points FROM users WHERE user_id=?", (uid,))
    level, exp, sp = c.fetchone()
    exp += amount; leveled = 0
    while exp >= exp_needed(level):
        exp -= exp_needed(level); level += 1; sp += 5; leveled += 1
    c.execute("UPDATE users SET level=?, exp=?, stat_points=? WHERE user_id=?",
              (level, exp, sp, uid))
    conn.commit(); conn.close()
    return leveled, level, sp

async def start(update, context):
    u = update.effective_user
    name = u.username or u.first_name or "Hunter"
    create_user(u.id, name)
    await update.message.reply_text(
        f"⚔️ <b>Selamat datang, Hunter {esc(name)}!</b>\n\n"
        "Sistem Questism aktif. Commands:\n"
        "/status /quest /complete /randomquest /rest /allocate /rank /help",
        parse_mode="HTML")

async def help_cmd(update, context):
    await update.message.reply_text(
        "📖 <b>Cara Main</b>\n\n"
        "1. /quest tiap hari\n2. Kerjakan, lalu /complete\n"
        "3. Naik level → +5 stat point → /allocate\n"
        "4. Total stats = Rank (F sampai SSS)\n"
        "5. /rest 1x/minggu\n6. /randomquest bonus", parse_mode="HTML")

async def status(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu."); return
    (_, username, level, exp, s, a, v, i, sp, *_rest) = row
    total = s + a + v + i; rank = get_rank(total); need = exp_needed(level)
    filled = int((exp / need) * 10) if need else 0
    bar = "█" * filled + "░" * (10 - filled)
    text = (f"📊 <b>STATUS HUNTER</b>\n━━━━━━━━━━━━━━━━━━━\n"
            f"👤 {esc(username)}\n🏅 Rank: <b>{rank}</b>\n⭐ Level: <b>{level}</b>\n"
            f"✨ EXP: {exp}/{need}\n   [{bar}]\n🔥 Streak: {row[14]} hari\n"
            f"━━━━━━━━━━━━━━━━━━━\n💪 STR: {s}\n🏃 AGI: {a}\n❤️ VIT: {v}\n🧠 INT: {i}\n"
            f"📈 Total: <b>{total}</b>\n🎯 Stat Points: <b>{sp}</b>")
    await update.message.reply_text(text, parse_mode="HTML")

async def quest(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu."); return
    today = date.today().isoformat()
    lqd, cq, cqs, qc = row[9], row[10], row[11], row[12]
    if lqd == today:
        if qc: await update.message.reply_text("✅ Quest hari ini selesai! Coba /randomquest.")
        else: await update.message.reply_text(f"📜 <b>Quest hari ini:</b>\n\n🎯 {esc(cq)}\n🏷️ {cqs}\n\nKetik /complete kalau selesai.", parse_mode="HTML")
        return
    stat = random.choice(list(QUESTS.keys()))
    qtext, reward = random.choice(QUESTS[stat])
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("UPDATE users SET last_quest_date=?, current_quest=?, current_quest_stat=?, quest_completed=0 WHERE user_id=?",
              (today, qtext, stat, uid))
    conn.commit(); conn.close()
    await update.message.reply_text(
        f"🌅 <b>DAILY QUEST</b>\n━━━━━━━━━━━━━━━━━━━\n🎯 {esc(qtext)}\n🏷️ {stat}\n"
        f"💎 Reward: +{reward} EXP, +3 {stat}\n━━━━━━━━━━━━━━━━━━━\nKetik /complete setelah selesai.",
        parse_mode="HTML")

async def complete(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu."); return
    today = date.today().isoformat()
    lqd, cq, cqs, qc, streak, lcd = row[9], row[10], row[11], row[12], row[14], row[15]
    if lqd != today or not cq:
        await update.message.reply_text("❌ Belum ada quest. Ketik /quest."); return
    if qc:
        await update.message.reply_text("✅ Sudah selesai."); return
    reward = next((r for q, r in QUESTS.get(cqs, []) if q == cq), 100)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    new_streak = streak + 1 if lcd == yesterday else 1
    streak_bonus = 20 if new_streak % 7 == 0 else 0
    total_exp = reward + streak_bonus
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute(f"UPDATE users SET quest_completed=1, streak=?, last_complete_date=?, {cqs.lower()}={cqs.lower()}+3 WHERE user_id=?",
              (new_streak, today, uid))
    conn.commit(); conn.close()
    leveled, new_level, sp = add_exp_and_levelup(uid, total_exp)
    msg = f"🎉 <b>QUEST COMPLETE!</b>\n\n💎 +{total_exp} EXP\n📈 +3 {cqs}"
    if streak_bonus: msg += f"\n🔥 Streak 7-hari bonus: +{streak_bonus} EXP"
    msg += f"\n🔥 Streak: {new_streak} hari"
    if leveled: msg += f"\n\n⬆️ <b>LEVEL UP!</b> Sekarang Level {new_level}\n🎁 +{leveled*5} Stat Points"
    await update.message.reply_text(msg, parse_mode="HTML")

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
    if leveled: msg += f"\n\n⬆️ <b>LEVEL UP!</b> Level {new_level} (+5 stat point)"
    await update.message.reply_text(msg, parse_mode="HTML")

async def rest(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu."); return
    today = date.today()
    week_str = f"{today.isocalendar()[0]}-{today.isocalendar()[1]}"
    if row[13] == week_str:
        await update.message.reply_text("😴 Sudah rest minggu ini. Reset Senin."); return
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("UPDATE users SET last_rest_week=?, last_quest_date=?, current_quest=NULL, quest_completed=1 WHERE user_id=?",
              (week_str, today.isoformat(), uid))
    conn.commit(); conn.close()
    await update.message.reply_text("😴 <b>REST DAY</b>\n\nHari ini bebas. Streak aman! 💪", parse_mode="HTML")

def alloc_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💪 STR +1", callback_data="alloc_STR"),
         InlineKeyboardButton("🏃 AGI +1", callback_data="alloc_AGI")],
        [InlineKeyboardButton("❤️ VIT +1", callback_data="alloc_VIT"),
         InlineKeyboardButton("🧠 INT +1", callback_data="alloc_INT")]])

async def allocate(update, context):
    row = get_user(update.effective_user.id)
    if not row:
        await update.message.reply_text("Ketik /start dulu."); return
    if row[8] <= 0:
        await update.message.reply_text("❌ Gak punya stat point."); return
    await update.message.reply_text(f"🎯 Stat Points: <b>{row[8]}</b>\nPilih:",
        parse_mode="HTML", reply_markup=alloc_keyboard())

async def alloc_cb(update, context):
    q = update.callback_query; await q.answer()
    stat = q.data.split("_", 1)[1]
    if stat not in ("STR","AGI","VIT","INT"): return
    uid = q.from_user.id
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT stat_points FROM users WHERE user_id=?", (uid,))
    r = c.fetchone()
    if not r or r[0] <= 0:
        await q.edit_message_text("❌ Habis."); conn.close(); return
    c.execute(f"UPDATE users SET stat_points=stat_points-1, {stat.lower()}={stat.lower()}+1 WHERE user_id=?", (uid,))
    conn.commit()
    c.execute("SELECT stat_points FROM users WHERE user_id=?", (uid,))
    new_sp = c.fetchone()[0]; conn.close()
    if new_sp <= 0: await q.edit_message_text(f"✅ +1 {stat}. Habis.")
    else: await q.edit_message_text(f"✅ +1 {stat}. Sisa: <b>{new_sp}</b>", parse_mode="HTML", reply_markup=alloc_keyboard())

async def rank_cmd(update, context):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT username, level, str+agi+vit+int AS total FROM users ORDER BY total DESC LIMIT 10")
    rows = c.fetchall(); conn.close()
    if not rows:
        await update.message.reply_text("Belum ada hunter."); return
    lines = ["🏆 <b>LEADERBOARD</b>", "━━━━━━━━━━━━━━━━━━━"]
    medals = ["🥇","🥈","🥉"]
    for i,(u,l,t) in enumerate(rows):
        p = medals[i] if i < 3 else f"{i+1}."
        lines.append(f"{p} {esc(u)} — [{get_rank(t)}] Lv.{l} • {t}")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

async def main_async():
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
    app.add_handler(CallbackQueryHandler(alloc_cb, pattern=r"^alloc_"))
    print("⚔️ Bot jalan! Jangan tutup tab ini.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    # biar tetap hidup
    import asyncio
    while True: await asyncio.sleep(3600)

import asyncio
asyncio.create_task(main_async())
