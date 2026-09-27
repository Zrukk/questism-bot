import os
import sqlite3
import random
import html
from datetime import date, timedelta, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ============ TOKEN DARI RAILWAY VARIABLES ============
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN belum diset di Railway Variables!")

DB = "questism.db"

def esc(s):
    return html.escape(str(s))

# ================== POOL QUEST ==================
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
    ("Tarik napas dalam 10x", "VIT", 20),
]

RANK_TABLE = [
    (1000, "SSS"), (750, "SS"), (550, "S"), (400, "A"),
    (280, "B"), (180, "C"), (100, "D"), (50, "E"), (0, "F"),
]

def get_rank(total):
    for thresh, name in RANK_TABLE:
        if total >= thresh:
            return name
    return "F"

def exp_needed(level):
    return level * 100

# ================== DATABASE ==================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        level INTEGER DEFAULT 1,
        exp INTEGER DEFAULT 0,
        str INTEGER DEFAULT 0,
        agi INTEGER DEFAULT 0,
        vit INTEGER DEFAULT 0,
        int INTEGER DEFAULT 0,
        stat_points INTEGER DEFAULT 0,
        last_quest_date TEXT,
        current_quest TEXT,
        current_quest_stat TEXT,
        quest_completed INTEGER DEFAULT 0,
        last_rest_week TEXT,
        streak INTEGER DEFAULT 0,
        last_complete_date TEXT
    )""")
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

def add_exp_and_levelup(uid, amount):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT level, exp, stat_points FROM users WHERE user_id=?", (uid,))
    level, exp, sp = c.fetchone()
    exp += amount
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

# ================== HANDLERS ==================
async def start(update, context):
    u = update.effective_user
    name = u.username or u.first_name or "Hunter"
    create_user(u.id, name)
    await update.message.reply_text(
        f"⚔️ <b>Selamat datang, Hunter {esc(name)}!</b>\n\n"
        "Sistem Questism telah aktif. Selesaikan quest harian untuk menaikkan "
        "Level, EXP, dan Stats. Naikkan rank dari <b>F</b> sampai <b>SSS</b>!\n\n"
        "📜 <b>Commands:</b>\n"
        "/status – Lihat stats & rank\n"
        "/quest – Ambil quest hari ini\n"
        "/complete – Selesaikan quest\n"
        "/randomquest – Quest bonus random\n"
        "/rest – Hari istirahat (1x/minggu)\n"
        "/allocate – Pakai stat point\n"
        "/rank – Leaderboard\n"
        "/help – Bantuan",
        parse_mode="HTML")

async def help_cmd(update, context):
    await update.message.reply_text(
        "📖 <b>Cara Main</b>\n\n"
        "1. Ketik /quest tiap hari untuk dapat quest.\n"
        "2. Kerjakan, lalu /complete untuk klaim reward (EXP + Stat).\n"
        "3. Naik level → dapat 5 stat point → pakai /allocate.\n"
        "4. Total stats menentukan Rank kamu (F sampai SSS).\n"
        "5. /rest 1x seminggu kalau tidak bisa quest.\n"
        "6. /randomquest untuk bonus kecil kapan saja.\n",
        parse_mode="HTML")

async def status(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu ya.")
        return
    (_, username, level, exp, s, a, v, i, sp, lqd, cq, cqs, qc, lrw, streak, lcd) = row
    total = s + a + v + i
    rank = get_rank(total)
    need = exp_needed(level)
    filled = int((exp / need) * 10) if need else 0
    bar = "█" * filled + "░" * (10 - filled)

    text = (
        f"📊 <b>STATUS HUNTER</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {esc(username)}\n"
        f"🏅 Rank: <b>{rank}</b>\n"
        f"⭐ Level: <b>{level}</b>\n"
        f"✨ EXP: {exp}/{need}\n"
        f"   [{bar}]\n"
        f"🔥 Streak: {streak} hari\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💪 STR: {s}\n"
        f"🏃 AGI: {a}\n"
        f"❤️ VIT: {v}\n"
        f"🧠 INT: {i}\n"
        f"📈 Total Stats: <b>{total}</b>\n"
        f"🎯 Stat Points: <b>{sp}</b>"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def quest(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu.")
        return
    today = date.today().isoformat()
    lqd, cq, cqs, qc = row[9], row[10], row[11], row[12]

    if lqd == today:
        if qc:
            await update.message.reply_text(
                "✅ Quest hari ini sudah selesai!\n"
                "Istirahat atau coba /randomquest untuk bonus.")
        else:
            await update.message.reply_text(
                f"📜 <b>Quest hari ini:</b>\n\n"
                f"🎯 {esc(cq)}\n"
                f"🏷️ Kategori: {cqs}\n\n"
                f"Ketik /complete kalau sudah selesai.",
                parse_mode="HTML")
        return

    stat = random.choice(list(QUESTS.keys()))
    qtext, reward = random.choice(QUESTS[stat])

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""UPDATE users SET last_quest_date=?, current_quest=?,
                 current_quest_stat=?, quest_completed=0 WHERE user_id=?""",
              (today, qtext, stat, uid))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"🌅 <b>DAILY QUEST</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 {esc(qtext)}\n"
        f"🏷️ Kategori: <b>{stat}</b>\n"
        f"💎 Reward: +{reward} EXP, +3 {stat}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"Ketik /complete setelah selesai.",
        parse_mode="HTML")

async def complete(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu.")
        return
    today = date.today().isoformat()
    lqd, cq, cqs, qc, streak, lcd = row[9], row[10], row[11], row[12], row[14], row[15]

    if lqd != today or not cq:
        await update.message.reply_text("❌ Kamu belum ambil quest hari ini. Ketik /quest.")
        return
    if qc:
        await update.message.reply_text("✅ Quest ini sudah kamu selesaikan.")
        return

    reward = 100
    for q, r in QUESTS.get(cqs, []):
        if q == cq:
            reward = r
            break

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    new_streak = streak + 1 if lcd == yesterday else 1
    streak_bonus = 20 if new_streak % 7 == 0 else 0
    total_exp = reward + streak_bonus

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    stat_col = cqs.lower()
    c.execute(f"""UPDATE users SET quest_completed=1, streak=?, last_complete_date=?,
                  {stat_col} = {stat_col} + 3 WHERE user_id=?""",
              (new_streak, today, uid))
    conn.commit()
    conn.close()

    leveled, new_level, sp = add_exp_and_levelup(uid, total_exp)

    msg = (
        f"🎉 <b>QUEST COMPLETE!</b>\n\n"
        f"💎 +{total_exp} EXP\n"
        f"📈 +3 {cqs}"
    )
    if streak_bonus:
        msg += f"\n🔥 Streak 7-hari bonus: +{streak_bonus} EXP"
    msg += f"\n🔥 Streak: {new_streak} hari"
    if leveled:
        msg += (f"\n\n⬆️ <b>LEVEL UP!</b> Sekarang Level {new_level}"
                f"\n🎁 +{leveled * 5} Stat Points (pakai /allocate)")

    await update.message.reply_text(msg, parse_mode="HTML")

async def random_quest(update, context):
    uid = update.effective_user.id
    if not get_user(uid):
        await update.message.reply_text("Ketik /start dulu.")
        return
    qtext, stat, reward = random.choice(RANDOM_QUESTS)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(f"UPDATE users SET {stat.lower()} = {stat.lower()} + 1 WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()
    leveled, new_level, sp = add_exp_and_levelup(uid, reward)

    msg = (
        f"🎲 <b>RANDOM QUEST</b>\n"
        f"🎯 {esc(qtext)}\n"
        f"💎 +{reward} EXP, +1 {stat}"
    )
    if leveled:
        msg += f"\n\n⬆️ <b>LEVEL UP!</b> Sekarang Level {new_level} (+5 stat point)"
    await update.message.reply_text(msg, parse_mode="HTML")

async def rest(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu.")
        return
    today = date.today()
    week_str = f"{today.isocalendar()[0]}-{today.isocalendar()[1]}"
    last_rest = row[13]

    if last_rest == week_str:
        await update.message.reply_text(
            "😴 Kamu sudah pakai hari istirahat minggu ini.\n"
            "Reset setiap hari Senin.")
        return

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""UPDATE users SET last_rest_week=?, last_quest_date=?,
                 current_quest=NULL, quest_completed=1 WHERE user_id=?""",
              (week_str, today.isoformat(), uid))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        "😴 <b>REST DAY</b>\n\n"
        "Hari ini kamu bebas. Streak tetap aman.\n"
        "Besok kembali lebih kuat! 💪",
        parse_mode="HTML")

def alloc_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💪 STR +1", callback_data="alloc_STR"),
         InlineKeyboardButton("🏃 AGI +1", callback_data="alloc_AGI")],
        [InlineKeyboardButton("❤️ VIT +1", callback_data="alloc_VIT"),
         InlineKeyboardButton("🧠 INT +1", callback_data="alloc_INT")],
    ])

async def allocate(update, context):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row:
        await update.message.reply_text("Ketik /start dulu.")
        return
    sp = row[8]
    if sp <= 0:
        await update.message.reply_text("❌ Kamu tidak punya stat point.")
        return
    await update.message.reply_text(
        f"🎯 Stat Points: <b>{sp}</b>\nPilih stat yang mau dinaikkan (+1):",
        parse_mode="HTML",
        reply_markup=alloc_keyboard())

async def alloc_cb(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    if not data.startswith("alloc_"):
        return
    stat = data.split("_", 1)[1]
    if stat not in ("STR", "AGI", "VIT", "INT"):
        return
    uid = query.from_user.id

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT stat_points FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    if not row or row[0] <= 0:
        await query.edit_message_text("❌ Stat point habis.")
        conn.close()
        return

    c.execute(f"UPDATE users SET stat_points = stat_points - 1, "
              f"{stat.lower()} = {stat.lower()} + 1 WHERE user_id=?", (uid,))
    conn.commit()
    c.execute("SELECT stat_points FROM users WHERE user_id=?", (uid,))
    new_sp = c.fetchone()[0]
    conn.close()

    if new_sp <= 0:
        await query.edit_message_text(f"✅ +1 {stat}. Stat point habis.")
    else:
        await query.edit_message_text(
            f"✅ +1 {stat}. Sisa: <b>{new_sp}</b>",
            parse_mode="HTML", reply_markup=alloc_keyboard())

async def rank_cmd(update, context):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""SELECT username, level, str+agi+vit+int AS total
                 FROM users ORDER BY total DESC LIMIT 10""")
    rows = c.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("Belum ada hunter terdaftar.")
        return

    lines = ["🏆 <b>LEADERBOARD HUNTER</b>", "━━━━━━━━━━━━━━━━━━━"]
    medals = ["🥇", "🥈", "🥉"]
    for idx, (uname, lvl, tot) in enumerate(rows):
        prefix = medals[idx] if idx < 3 else f"{idx+1}."
        rk = get_rank(tot)
        lines.append(f"{prefix} {esc(uname)} — [{rk}] Lv.{lvl} • {tot} pts")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

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
                text="🌅 <b>Quest baru tersedia!</b>\nKetik /quest untuk mengambil misi hari ini.",
                parse_mode="HTML")
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
    app.add_handler(CallbackQueryHandler(alloc_cb, pattern=r"^alloc_"))

    # Push quest tiap hari jam 07:00 UTC (14:00 WIB)
    app.job_queue.run_daily(daily_broadcast, time=time(hour=7, minute=0))

    print("⚔️ Bot Questism berjalan...", flush=True)
    app.run_polling()

if __name__ == "__main__":
    main()
