import time
import random
import re
import json
import os
import string
import threading
import telebot
from telebot import types
from datetime import datetime, timedelta

print("🔄 Инициализация системы...")

BOT_TOKEN = "8209142071:AAE83Nnm1MGOJLtN5lX6XwIhcVfy3qadfIQ"
BOT_USERNAME = "Repluka_puzdyi_bot"
ADMIN_ID = 7762932483
CONTACT = "@qyfod"

bot = telebot.TeleBot(BOT_TOKEN)
print("✅ Бот создан!")

DATA_FILE = "bot_data.json"
USER_STATE = {}
ACCOUNTS = {}
TG_TO_LOGIN = {}
CASINO_STREAKS = {}
LAST_BONUS = {}
PROMOCODES = {}
COUPONS = {}

RUSSIA_CITIES = [
    "сызрань", "самара", "тольятти", "москва", "санкт-петербург", "новосибирск",
    "екатеринбург", "казань", "нижний новгород", "челябинск", "красноярск", "уфа",
    "ростов-на-дону", "омск", "краснодар", "воронеж", "пермь", "волгоград",
    "саратов", "тюмень"
]

PHONE_CATEGORIES = {
    "budget": ("🟢 Бюджетные", 0, 15000),
    "mid":    ("🟡 Среднебюджетные", 15000, 35000),
    "flag":   ("🟠 Флагманы", 35000, 70000),
    "ultra":  ("🔴 Ультра-флагманы", 70000, 9999999),
}


def save_data():
    data = {
        "accounts": ACCOUNTS,
        "tg_to_login": {str(k): v for k, v in TG_TO_LOGIN.items()},
        "streaks": {str(k): v for k, v in CASINO_STREAKS.items()},
        "promocodes": PROMOCODES,
        "coupons": COUPONS,
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Save: {e}")


def load_data():
    global ACCOUNTS, TG_TO_LOGIN, CASINO_STREAKS, PROMOCODES, COUPONS
    if not os.path.exists(DATA_FILE):
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        ACCOUNTS = data.get("accounts", {})
        for login, acc in ACCOUNTS.items():
            acc.setdefault("vip_until", None)
            acc.setdefault("streak", 0)
            acc.setdefault("last_streak", None)
            acc.setdefault("last_free", None)
            acc.setdefault("last_wheel", None)
            acc.setdefault("friends", 0)
            acc.setdefault("achievements", [])
            acc.setdefault("banned", False)
            acc.setdefault("requests", 0)
            acc.setdefault("free_used", 0)
            acc.setdefault("balance", 5000)
        TG_TO_LOGIN = {int(k): v for k, v in data.get("tg_to_login", {}).items()}
        CASINO_STREAKS = {int(k): v for k, v in data.get("streaks", {}).items()}
        PROMOCODES = data.get("promocodes", {})
        COUPONS = data.get("coupons", {})
        print(f"📦 Загружено: {len(ACCOUNTS)} аккаунтов")
    except Exception as e:
        print(f"⚠️ Load: {e}")


def get_acc(tg_id):
    login = TG_TO_LOGIN.get(tg_id)
    if not login:
        return None
    return ACCOUNTS.get(login)


def is_admin(tg_id):
    return tg_id == ADMIN_ID


def is_vip(login):
    if not login:
        return False
    acc = ACCOUNTS.get(login)
    if not acc or not acc.get("vip_until"):
        return False
    try:
        return datetime.fromisoformat(acc["vip_until"]) > datetime.now()
    except:
        return False


def vip_until_str(login):
    acc = ACCOUNTS.get(login)
    if not acc or not acc.get("vip_until"):
        return "нет"
    try:
        return datetime.fromisoformat(acc["vip_until"]).strftime("%d.%m.%Y %H:%M")
    except:
        return "нет"


def vip_add(login, days=0, hours=0, minutes=0):
    acc = ACCOUNTS.get(login)
    if not acc:
        return
    now = datetime.now()
    delta = timedelta(days=days, hours=hours, minutes=minutes)
    cur = None
    if acc.get("vip_until"):
        try:
            cur = datetime.fromisoformat(acc["vip_until"])
        except:
            cur = None
    if cur and cur > now:
        acc["vip_until"] = (cur + delta).isoformat()
    else:
        acc["vip_until"] = (now + delta).isoformat()
    save_data()


def gen_captcha():
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=5))


def gen_login():
    for _ in range(100):
        login = "".join(random.choices(string.digits, k=6))
        if login not in ACCOUNTS:
            return login
    return None


def find_phone(name):
    if not name:
        return None
    name = name.strip().lower()
    best, best_score = None, 0
    for p in PHONE_DATABASE:
        common = len(set(name.split()) & set(p["model"].lower().split()))
        if common > best_score:
            best_score, best = common, p
    return best


def category_name(cat_key):
    return PHONE_CATEGORIES[cat_key][0]


def category_range(cat_key):
    _, lo, hi = PHONE_CATEGORIES[cat_key]
    return lo, hi
    

def generate_phone_db():
    phones = [
        ("Xiaomi Redmi 13C", 45, 9000, "слабый CPU", "budget"),
        ("Xiaomi Redmi 12", 48, 11000, "слабый экран", "budget"),
        ("Xiaomi Redmi 10", 42, 9000, "слабый процессор", "budget"),
        ("Xiaomi Redmi 9A", 35, 6000, "очень слабый", "budget"),
        ("Poco C65", 42, 9000, "слабый", "budget"),
        ("Poco M5", 50, 11000, "слабый экран", "budget"),
        ("Poco M6 Pro", 55, 14000, "слабый экран", "budget"),
        ("Realme C53", 45, 10000, "тормозит", "budget"),
        ("Realme C55", 48, 12000, "слабый процессор", "budget"),
        ("Realme C67", 55, 14000, "слабый CPU", "budget"),
        ("Realme Narzo 60", 58, 14000, "слабый экран", "budget"),
        ("Samsung Galaxy A14", 45, 10000, "тормозит", "budget"),
        ("Samsung Galaxy A15", 48, 12000, "слабый CPU", "budget"),
        ("Samsung Galaxy A05", 40, 8000, "очень слабый", "budget"),
        ("Samsung Galaxy A05s", 45, 10000, "слабый", "budget"),
        ("Tecno Spark 10", 40, 8000, "очень слабый", "budget"),
        ("Tecno Spark 20", 48, 11000, "слабый экран", "budget"),
        ("Tecno Spark 20 Pro", 55, 14000, "слабый экран", "budget"),
        ("Tecno Camon 20", 50, 13000, "слабый CPU", "budget"),
        ("Infinix Hot 30", 42, 9000, "слабый процессор", "budget"),
        ("Infinix Hot 40", 48, 11000, "слабый CPU", "budget"),
        ("Infinix Note 30", 55, 14000, "слабый экран", "budget"),
        ("Nokia C32", 40, 8000, "очень слабый", "budget"),
        ("Nokia G42", 45, 12000, "слабый процессор", "budget"),
        ("Honor X7b", 50, 14000, "слабый процессор", "budget"),
        ("Honor X8b", 55, 15000, "слабый экран", "budget"),
        ("Motorola Moto G54", 55, 14000, "слабый экран", "budget"),
        ("Motorola Moto G24", 42, 9000, "слабый", "budget"),
        ("Vivo Y27", 48, 12000, "слабый CPU", "budget"),
        ("Vivo Y17s", 45, 11000, "слабый", "budget"),
        ("Oppo A78", 50, 14000, "слабый CPU", "budget"),
        ("Oppo A58", 48, 13000, "слабый", "budget"),
        ("Huawei Nova Y61", 45, 12000, "нет Google", "budget"),
        ("Huawei Nova Y70", 48, 13000, "нет Google", "budget"),
        ("Blackview A200", 40, 10000, "слабый CPU", "budget"),
        ("Ulefone Note 16", 42, 10000, "слабый", "budget"),

        ("Xiaomi Redmi Note 13", 60, 16000, "слабый экран", "mid"),
        ("Xiaomi Redmi Note 13 Pro", 68, 22000, "реклама в MIUI", "mid"),
        ("Xiaomi Redmi Note 13 Pro+", 72, 28000, "пластик", "mid"),
        ("Xiaomi Redmi Note 12", 60, 15000, "слабый экран", "mid"),
        ("Xiaomi Redmi Note 12 Pro", 65, 20000, "слабый CPU", "mid"),
        ("Poco X6", 75, 25000, "слабый экран", "mid"),
        ("Poco X6 Pro", 82, 30000, "пластик", "mid"),
        ("Poco F5", 80, 28000, "слабый динамик", "mid"),
        ("Poco F6", 82, 35000, "слабый софт", "mid"),
        ("Poco M6 Pro 5G", 60, 17000, "слабый", "mid"),
        ("Realme 11 Pro", 70, 24000, "слабый вибро", "mid"),
        ("Realme 12 Pro+", 75, 28000, "слабый софт", "mid"),
        ("Realme GT Neo 5", 85, 35000, "греется", "mid"),
        ("Samsung Galaxy A34", 58, 18000, "слабый процессор", "mid"),
        ("Samsung Galaxy A35", 60, 20000, "слабый экран", "mid"),
        ("Samsung Galaxy A54", 65, 25000, "слабый CPU", "mid"),
        ("Samsung Galaxy A55", 68, 28000, "тормозит в играх", "mid"),
        ("Samsung Galaxy M34", 55, 16000, "слабый процессор", "mid"),
        ("Samsung Galaxy M54", 62, 22000, "слабый софт", "mid"),
        ("Honor 90 Lite", 60, 18000, "слабый CPU", "mid"),
        ("Honor X9b", 62, 20000, "слабый CPU", "mid"),
        ("Honor 90", 75, 32000, "слабый софт", "mid"),
        ("Huawei Nova 11", 68, 25000, "нет Google", "mid"),
        ("Huawei Nova 12", 72, 28000, "нет Google", "mid"),
        ("OnePlus Nord CE 3 Lite", 60, 20000, "слабый CPU", "mid"),
        ("OnePlus Nord 3", 78, 32000, "греется", "mid"),
        ("Google Pixel 6a", 72, 25000, "слабый экран", "mid"),
        ("Google Pixel 7a", 80, 35000, "медленная зарядка", "mid"),
        ("Nothing Phone (2a)", 72, 30000, "слабый софт", "mid"),
        ("Nothing Phone 1", 70, 28000, "глючит софт", "mid"),
        ("Vivo V27e", 65, 15000, "слабый Helio G99", "mid"),
        ("Vivo V30 Pro", 78, 35000, "слабый софт", "mid"),
        ("Vivo Y36", 55, 16000, "слабый экран", "mid"),
        ("Oppo Reno 10", 72, 30000, "слабый софт", "mid"),
        ("Oppo Reno 11", 75, 32000, "слабый софт", "mid"),
        ("Motorola Edge 40", 80, 35000, "слабый софт", "mid"),
        ("Tecno Camon 30 Pro", 65, 22000, "слабый софт", "mid"),
        ("Tecno Pova 6 Pro", 62, 20000, "слабый процессор", "mid"),
        ("Infinix Note 40 Pro", 68, 24000, "слабый софт", "mid"),
        ("Asus Zenfone 9", 85, 35000, "слабый софт", "mid"),
        ("Nokia XR21", 68, 35000, "слабый софт", "mid"),
        ("ZTE Axon 40", 75, 35000, "слабый софт", "mid"),
        ("ZTE Blade V50", 55, 16000, "слабый CPU", "mid"),
        ("Meizu 20", 78, 30000, "нет сервисов", "mid"),

        ("iPhone 12", 78, 35000, "батарея быстро садится", "flag"),
        ("iPhone 12 Pro", 82, 40000, "батарея слабая", "flag"),
        ("iPhone 12 Pro Max", 88, 45000, "слабый 5G", "flag"),
        ("iPhone 13", 85, 48000, "слабый аккумулятор", "flag"),
        ("iPhone 13 Pro", 90, 55000, "дорогой ремонт", "flag"),
        ("iPhone 13 Pro Max", 92, 60000, "выгорание OLED", "flag"),
        ("iPhone 14", 88, 55000, "старый дизайн", "flag"),
        ("Samsung Galaxy S21", 80, 35000, "слабый экран", "flag"),
        ("Samsung Galaxy S21 FE", 78, 32000, "пластик", "flag"),
        ("Samsung Galaxy S22", 82, 40000, "перегрев", "flag"),
        ("Samsung Galaxy S22 Ultra", 92, 55000, "слабый аккумулятор", "flag"),
        ("Samsung Galaxy S23", 90, 55000, "греется", "flag"),
        ("Samsung Galaxy S23 FE", 85, 45000, "слабый CPU", "flag"),
        ("Samsung Galaxy Note 20 Ultra", 88, 55000, "дорогой", "flag"),
        ("Xiaomi 12", 82, 35000, "батарея слабая", "flag"),
        ("Xiaomi 12T Pro", 85, 40000, "греется", "flag"),
        ("Xiaomi 13T Pro", 88, 45000, "нет беспроводной зарядки", "flag"),
        ("Xiaomi 13", 90, 50000, "реклама в софте", "flag"),
        ("Xiaomi 14", 95, 65000, "реклама в MIUI", "flag"),
        ("Poco F5 Pro", 85, 38000, "греется", "flag"),
        ("Poco F6 Pro", 88, 45000, "пластиковый корпус", "flag"),
        ("Realme GT 6", 92, 55000, "слабый софт", "flag"),
        ("Honor Magic 5 Pro", 92, 65000, "слабый софт", "flag"),
        ("Honor Magic 6 Pro", 95, 70000, "дорогой", "flag"),
        ("Huawei P50 Pro", 82, 45000, "нет Google", "flag"),
        ("Huawei P60 Pro", 88, 60000, "нет Google", "flag"),
        ("OnePlus 10 Pro", 88, 45000, "греется", "flag"),
        ("OnePlus 11", 92, 55000, "слабый вибро", "flag"),
        ("OnePlus 12", 96, 65000, "слабый софт", "flag"),
        ("Google Pixel 8", 90, 55000, "медленная зарядка", "flag"),
        ("Google Pixel 7 Pro", 90, 50000, "греется", "flag"),
        ("Nothing Phone 2", 82, 45000, "слабый софт", "flag"),
        ("Sony Xperia 5 V", 88, 65000, "слабый софт", "flag"),
        ("Asus Zenfone 10", 90, 55000, "маленький экран", "flag"),
        ("Vivo X90", 92, 65000, "нет Google", "flag"),
        ("Vivo X100", 95, 70000, "дорогой", "flag"),
        ("Oppo Find X6", 92, 65000, "слабый софт", "flag"),

        ("iPhone 14 Pro", 93, 70000, "износ аккумулятора", "ultra"),
        ("iPhone 14 Pro Max", 94, 75000, "тяжёлый", "ultra"),
        ("iPhone 15", 92, 65000, "медленная зарядка", "ultra"),
        ("iPhone 15 Plus", 92, 70000, "тяжёлый", "ultra"),
        ("iPhone 15 Pro", 95, 80000, "перегрев при играх", "ultra"),
        ("iPhone 15 Pro Max", 96, 95000, "титановый корпус царапается", "ultra"),
        ("iPhone 16", 92, 85000, "нет зарядки в комплекте", "ultra"),
        ("iPhone 16 Plus", 92, 90000, "тяжёлый", "ultra"),
        ("iPhone 16 Pro", 98, 110000, "высокая цена", "ultra"),
        ("iPhone 16 Pro Max", 100, 130000, "дорогой ремонт", "ultra"),
        ("Samsung Galaxy S23 Ultra", 96, 75000, "тяжёлый", "ultra"),
        ("Samsung Galaxy S24", 92, 65000, "экран 1080p", "ultra"),
        ("Samsung Galaxy S24+", 95, 75000, "нет зарядки", "ultra"),
        ("Samsung Galaxy S24 Ultra", 99, 90000, "дорогой ремонт", "ultra"),
        ("Samsung Galaxy Z Fold 5", 92, 90000, "складка", "ultra"),
        ("Samsung Galaxy Z Flip 5", 88, 55000, "складка", "ultra"),
        ("Xiaomi 14 Ultra", 98, 85000, "дорогой ремонт", "ultra"),
        ("Xiaomi 13 Ultra", 96, 70000, "тяжёлый", "ultra"),
        ("Honor Magic V2", 92, 95000, "хрупкий", "ultra"),
        ("Huawei Pura 70 Ultra", 98, 95000, "нет Google", "ultra"),
        ("Huawei Mate 60 Pro", 94, 75000, "нет Google", "ultra"),
        ("OnePlus Open", 92, 90000, "хрупкий", "ultra"),
        ("Google Pixel 8 Pro", 96, 75000, "дорогой ремонт", "ultra"),
        ("Google Pixel 9 Pro", 97, 85000, "дорогой", "ultra"),
        ("Sony Xperia 1 V", 94, 85000, "дорогой", "ultra"),
        ("Asus ROG Phone 7", 100, 80000, "тяжёлый", "ultra"),
        ("Asus ROG Phone 8 Pro", 100, 95000, "тяжёлый", "ultra"),
        ("Vivo X100 Pro", 96, 75000, "дорогой", "ultra"),
        ("Vivo X100 Ultra", 98, 90000, "дорогой", "ultra"),
        ("Oppo Find X7 Ultra", 97, 85000, "дорогой", "ultra"),
        ("Meizu 21", 88, 70000, "нет сервисов", "ultra"),
    ]
    db = []
    for model, cpu, price, weak, cat in phones:
        db.append({"model": model, "cpu_score": cpu, "price": price,
                   "weakness": weak, "category": cat})
    return db


PHONE_DATABASE = generate_phone_db()
try:
    from тксерь import EXTRA_PHONES
    PHONE_DATABASE = PHONE_DATABASE + EXTRA_PHONES
    print(f"📱 Доп. база: {len(EXTRA_PHONES)} шт")
except Exception as e:
    print(f"⚠️ Не загрузилась доп. база: {e}")
print(f"📱 База телефонов: {len(PHONE_DATABASE)} шт")


def main_menu_kb(tg_id):
    login = TG_TO_LOGIN.get(tg_id)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text="🔍 Поиск смартфона", callback_data="search_start"))
    kb.add(types.InlineKeyboardButton(text="💰 Купить запросы", callback_data="buy_requests"))
    kb.add(types.InlineKeyboardButton(text="👑 Подписка VIP", callback_data="buy_subscription"))
    kb.add(types.InlineKeyboardButton(text="🎡 Колесо Фортуны", callback_data="wheel"))
    kb.add(types.InlineKeyboardButton(text="🎰 Слот-Машина", callback_data="game_casino"))
    kb.add(types.InlineKeyboardButton(text="🎲 Кубик-Казино", callback_data="dice_casino"))
    kb.add(types.InlineKeyboardButton(text="🎲 Ставки", callback_data="game_bet"))
    kb.add(types.InlineKeyboardButton(text="🎁 Ежедневный бонус", callback_data="daily_bonus"))
    kb.add(types.InlineKeyboardButton(text="🎫 Промокод", callback_data="enter_promo"))
    kb.add(types.InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile"))
    kb.add(types.InlineKeyboardButton(text="🏆 Топ игроков", callback_data="top_players"))
    kb.add(types.InlineKeyboardButton(text="🥇 Достижения", callback_data="achievements"))
    kb.add(types.InlineKeyboardButton(text="👥 Пригласить друга", callback_data="ref_link"))
    if login and is_vip(login):
        kb.add(types.InlineKeyboardButton(text="👑 VIP-МЕНЮ 👑", callback_data="vip_menu"))
    if is_admin(tg_id):
        kb.add(types.InlineKeyboardButton(text="🛡 АДМИН-ПАНЕЛЬ", callback_data="admin_panel"))
    return kb


def main_menu_text(tg_id):
    acc = get_acc(tg_id)
    if not acc:
        return "❌ Ошибка аккаунта"
    login = TG_TO_LOGIN[tg_id]
    vip_status = f"👑 VIP до {vip_until_str(login)}" if is_vip(login) else "❌ Обычный"
    free_left = 3 - acc.get("free_used", 0)
    return (
        f"╔══════════════════════════╗\n"
        f"   🔴 SYSTEM TERMINAL 🔴\n"
        f"╚══════════════════════════╝\n\n"
        f"👤 Логин: {login}\n"
        f"💰 Баланс: {acc['balance']} ₽\n"
        f"🔍 Запросы: {acc['requests']} шт\n"
        f"🎫 Бесплатных: {free_left}/3\n"
        f"✨ Статус: {vip_status}\n"
        f"🔥 Стрик: {acc.get('streak', 0)} дней\n\n"
        f"Выбери модуль ниже 👇"
    )


@bot.message_handler(commands=['start'])
def start_command(message):
    tg_id = message.chat.id
    args = message.text.split()

    ref_login = None
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_login = args[1][4:]

    if tg_id in TG_TO_LOGIN:
        login = TG_TO_LOGIN[tg_id]
        acc = ACCOUNTS.get(login)
        if acc and acc.get("banned"):
            bot.send_message(tg_id, f"🚫 Вы забанены. Обратитесь к админу: {CONTACT}")
            return
        update_streak(login)
        bot.send_message(tg_id, main_menu_text(tg_id), reply_markup=main_menu_kb(tg_id))
        return

    captcha = gen_captcha()
    USER_STATE[tg_id] = {"state": "captcha", "captcha": captcha, "ref": ref_login}
    bot.send_message(tg_id,
                     f"🛡 ВЕРИФИКАЦИЯ\n\n"
                     f"Напиши этот код, чтобы продолжить:\n\n"
                     f"👁 `{captcha}`\n\n"
                     f"⚠️ Регистр важен!",
                     parse_mode="Markdown")


@bot.message_handler(func=lambda m: USER_STATE.get(m.chat.id, {}).get("state") == "captcha", content_types=['text'])
def handle_captcha(message):
    tg_id = message.chat.id
    st = USER_STATE.get(tg_id)
    if not st:
        return
    if message.text.strip() != st["captcha"]:
        new_cap = gen_captcha()
        st["captcha"] = new_cap
        bot.reply_to(message, f"❌ Неверно! Новый код:\n\n👁 `{new_cap}`", parse_mode="Markdown")
        return
    st["state"] = "choose_reg"
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(text="🆕 Регистрация", callback_data="do_register"),
        types.InlineKeyboardButton(text="🔑 Войти", callback_data="do_login")
    )
    bot.send_message(tg_id,
                     "✅ Верификация пройдена!\n\n"
                     "🆕 *Регистрация* — создать новый аккаунт\n"
                     "🔑 *Войти* — если у тебя уже есть логин",
                     parse_mode="Markdown", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data == "do_register")
def do_register(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    if tg_id not in USER_STATE:
        USER_STATE[tg_id] = {}
    USER_STATE[tg_id]["state"] = "waiting_login"
    bot.edit_message_text(chat_id=tg_id, message_id=call.message.id,
                          text="🆕 Введи свой логин — *6 цифр* (запомни его!):\n\nПример: `482913`",
                          parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "do_login")
def do_login(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    if tg_id not in USER_STATE:
        USER_STATE[tg_id] = {}
    USER_STATE[tg_id]["state"] = "waiting_login_input"
    bot.edit_message_text(chat_id=tg_id, message_id=call.message.id,
                          text="🔑 Введи свой логин (6 цифр):")


@bot.message_handler(func=lambda m: USER_STATE.get(m.chat.id, {}).get("state") in ["waiting_login", "waiting_login_input"], content_types=['text'])
def handle_login(message):
    tg_id = message.chat.id
    st = USER_STATE.get(tg_id)
    if not st:
        return
    login = message.text.strip()

    if not re.fullmatch(r"\d{6}", login):
        bot.reply_to(message, "❌ Логин должен быть ровно *6 цифр*. Попробуй снова:", parse_mode="Markdown")
        return

    if st["state"] == "waiting_login_input":
        if login not in ACCOUNTS:
            bot.reply_to(message, "❌ Аккаунт не найден. Нажми /start заново.")
            USER_STATE[tg_id] = None
            return
        acc = ACCOUNTS[login]
        if acc.get("banned"):
            bot.reply_to(message, "🚫 Аккаунт забанен.")
            USER_STATE[tg_id] = None
            return
        old_tg = acc.get("tg_id")
        if old_tg and old_tg in TG_TO_LOGIN:
            del TG_TO_LOGIN[old_tg]
        acc["tg_id"] = tg_id
        TG_TO_LOGIN[tg_id] = login
        USER_STATE[tg_id] = None
        save_data()
        update_streak(login)
        bot.send_message(tg_id, f"✅ Вход выполнен!\n👤 Логин: `{login}`", parse_mode="Markdown")
        bot.send_message(tg_id, main_menu_text(tg_id), reply_markup=main_menu_kb(tg_id))
        return

    if st["state"] == "waiting_login":
        if login in ACCOUNTS:
            bot.reply_to(message, "❌ Логин занят. Введи другой (6 цифр):")
            return
        ACCOUNTS[login] = {
            "tg_id": tg_id,
            "balance": 5000,
            "requests": 0,
            "free_used": 0,
            "last_free": None,
            "vip_until": None,
            "streak": 1,
            "last_streak": datetime.now().isoformat(),
            "last_wheel": None,
            "friends": 0,
            "achievements": [],
            "banned": False,
        }
        TG_TO_LOGIN[tg_id] = login

        ref = st.get("ref")
        if ref and ref in ACCOUNTS and ref != login:
            ACCOUNTS[ref]["requests"] += 1
            ACCOUNTS[ref]["balance"] += 1000
            ACCOUNTS[ref]["friends"] = ACCOUNTS[ref].get("friends", 0) + 1
            try:
                bot.send_message(ACCOUNTS[ref]["tg_id"],
                                 f"🎉 По твоей реф-ссылке зарегался друг!\n"
                                 f"🎁 +1 запрос, +1000 ₽\n👥 Друзей: {ACCOUNTS[ref]['friends']}")
            except:
                pass

        USER_STATE[tg_id] = None
        save_data()
        bot.send_message(tg_id,
                         f"🎉 Регистрация завершена!\n\n"
                         f"👤 Твой логин: `{login}`\n"
                         f"⚠️ *Сохрани его!* С ним ты можешь зайти с любого телефона.",
                         parse_mode="Markdown")
        bot.send_message(tg_id, main_menu_text(tg_id), reply_markup=main_menu_kb(tg_id))
        return


def update_streak(login):
    acc = ACCOUNTS.get(login)
    if not acc:
        return
    now = datetime.now()
    last = acc.get("last_streak")
    if last:
        try:
            last_dt = datetime.fromisoformat(last)
            diff = (now.date() - last_dt.date()).days
            if diff == 1:
                acc["streak"] = acc.get("streak", 0) + 1
                acc["last_streak"] = now.isoformat()
                if acc["streak"] == 7:
                    acc["balance"] += 5000
                    acc["requests"] += 3
                    try:
                        bot.send_message(acc["tg_id"], "🔥 СТРИК 7 ДНЕЙ!\n🎁 +5000 ₽, +3 запроса")
                    except:
                        pass
                elif acc["streak"] == 30:
                    vip_add(login, days=7)
                    try:
                        bot.send_message(acc["tg_id"], "🔥 СТРИК 30 ДНЕЙ!\n👑 +VIP на 7 дней")
                    except:
                        pass
            elif diff > 1:
                acc["streak"] = 1
                acc["last_streak"] = now.isoformat()
        except:
            pass
    else:
        acc["last_streak"] = now.isoformat()
    save_data()
    

def check_free_search(tg_id):
    acc = get_acc(tg_id)
    if not acc:
        return False, "нет аккаунта"
    now = datetime.now()
    last = acc.get("last_free")
    if last:
        try:
            last_dt = datetime.fromisoformat(last)
            if now - last_dt > timedelta(hours=8):
                acc["free_used"] = 0
                acc["last_free"] = None
            else:
                if acc["free_used"] >= 3:
                    left = timedelta(hours=8) - (now - last_dt)
                    h, m = left.seconds // 3600, (left.seconds // 60) % 60
                    return False, f"бесплатные кончились, ждать {h}ч {m}м"
        except:
            pass
    return True, "ok"


def spend_search(tg_id):
    acc = get_acc(tg_id)
    if not acc:
        return
    can, _ = check_free_search(tg_id)
    if can:
        if not acc.get("last_free"):
            acc["last_free"] = datetime.now().isoformat()
        acc["free_used"] = acc.get("free_used", 0) + 1
    else:
        if acc["requests"] > 0:
            acc["requests"] -= 1
    save_data()


@bot.callback_query_handler(func=lambda call: call.data == "search_start")
def search_start(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    acc = get_acc(tg_id)
    if not acc:
        return
    can, reason = check_free_search(tg_id)
    if not can and acc["requests"] <= 0:
        bot.send_message(tg_id,
                         f"❌ {reason}\n"
                         f"🔍 Запросов: {acc['requests']}\n\n"
                         f"Купи запросы или подожди 👇")
        return
    USER_STATE[tg_id] = {"state": "search_city"}
    bot.edit_message_text(chat_id=tg_id, message_id=call.message.id,
                          text="🔍 *ПОИСК СМАРТФОНА*\n\nШаг 1/2: Напиши город (например, Сызрань):",
                          parse_mode="Markdown")


@bot.message_handler(func=lambda m: USER_STATE.get(m.chat.id, {}).get("state") == "search_city", content_types=['text'])
def search_city(message):
    tg_id = message.chat.id
    city = message.text.strip().lower()
    if city not in RUSSIA_CITIES:
        bot.reply_to(message, "❌ Город не найден. Попробуй ещё:")
        return
    USER_STATE[tg_id] = {"state": "search_category", "city": city}
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(text="🟢 Бюджетные", callback_data="cat_budget"),
        types.InlineKeyboardButton(text="🟡 Среднебюджет", callback_data="cat_mid"),
        types.InlineKeyboardButton(text="🟠 Флагманы", callback_data="cat_flag"),
        types.InlineKeyboardButton(text="🔴 Ультра", callback_data="cat_ultra")
    )
    bot.reply_to(message,
                 f"✅ {city.title()}\n\nШаг 2/2: Выбери категорию:",
                 reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def search_do(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    st = USER_STATE.get(tg_id)
    if not st or st.get("state") != "search_category":
        return
    cat_key = call.data.replace("cat_", "")
    city = st["city"]
    USER_STATE[tg_id] = None

    spend_search(tg_id)

    matches = [p for p in PHONE_DATABASE if p["category"] == cat_key]
    random.shuffle(matches)
    top = sorted(matches, key=lambda x: x["cpu_score"], reverse=True)[:5]

    if not top:
        bot.send_message(tg_id, "😔 Ничего не нашёл.")
        return

    acc = get_acc(tg_id)
    text = f"📍 {city.title()} | {category_name(cat_key)}\n\n"
    for i, p in enumerate(top, 1):
        text += (f"{i}. *{p['model']}*\n"
                 f"   💰 ~{p['price']} ₽ | ⚡ CPU: {p['cpu_score']}\n"
                 f"   ⚠️ {p['weakness']}\n\n")
    text += (f"🔍 Осталось бесплатных: {3 - acc['free_used']}/3\n"
             f"🎫 Запросов: {acc['requests']}\n\n"
             f"━━━━━━━━━━━━━━━━━━\n"
             f"📞 Найти в реальных магазинах {city.title()}:\n"
             f"Напиши администратору: {CONTACT}")

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="🔍 Ещё поиск", callback_data="search_start"))
    kb.add(types.InlineKeyboardButton(text="⬅️ В меню", callback_data="back_main"))
    bot.send_message(tg_id, text, parse_mode="Markdown", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data == "my_profile")
def my_profile(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    acc = get_acc(tg_id)
    login = TG_TO_LOGIN.get(tg_id, "?")
    if not acc:
        return
    vip_status = f"👑 до {vip_until_str(login)}" if is_vip(login) else "❌ нет"
    text = (
        f"╔══════════════════════════╗\n"
        f"   👤 МОЙ ПРОФИЛЬ\n"
        f"╚══════════════════════════╝\n\n"
        f"🆔 Логин: `{login}`\n"
        f"💰 Баланс: {acc['balance']} ₽\n"
        f"🔍 Запросы: {acc['requests']}\n"
        f"🎫 Бесплатных: {3 - acc.get('free_used', 0)}/3\n"
        f"👑 VIP: {vip_status}\n"
        f"🔥 Стрик: {acc.get('streak', 0)} дней\n"
        f"👥 Друзей: {acc.get('friends', 0)}\n"
        f"🏆 Ачивок: {len(acc.get('achievements', []))}/10\n"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main"))
    bot.edit_message_text(chat_id=tg_id, message_id=call.message.id,
                          text=text, parse_mode="Markdown", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data == "ref_link")
def ref_link(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    login = TG_TO_LOGIN.get(tg_id)
    if not login:
        return
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{login}"
    text = (
        f"👥 *ПРИГЛАСИ ДРУГА*\n\n"
        f"🔗 Твоя личная ссылка:\n`{link}`\n\n"
        f"🎁 За каждого друга:\n"
        f"• +1 запрос\n"
        f"• +1000 ₽\n\n"
        f"👥 Уже приглашено: {ACCOUNTS[login].get('friends', 0)}"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main"))
    bot.edit_message_text(chat_id=tg_id, message_id=call.message.id,
                          text=text, parse_mode="Markdown", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    try:
        bot.edit_message_text(chat_id=tg_id, message_id=call.message.id,
                              text=main_menu_text(tg_id), reply_markup=main_menu_kb(tg_id))
    except:
        bot.send_message(tg_id, main_menu_text(tg_id), reply_markup=main_menu_kb(tg_id))
        

@bot.callback_query_handler(func=lambda call: call.data == "buy_requests")
def buy_requests(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    acc = get_acc(tg_id)
    text = (
        f"💰 *КУПИТЬ ЗАПРОСЫ*\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔍 1 запрос — *3 ₽*\n"
        f"🔍 5 запросов — *10 ₽*\n"
        f"🔍 10 запросов — *20 ₽*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"💳 У тебя: {acc['requests']} запросов\n\n"
        f"⚠️ Оплата через администратора.\n"
        f"Напиши: {CONTACT}"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text="1 запрос — 3 ₽", callback_data="buy_1"))
    kb.add(types.InlineKeyboardButton(text="5 запросов — 10 ₽", callback_data="buy_5"))
    kb.add(types.InlineKeyboardButton(text="10 запросов — 20 ₽", callback_data="buy_10"))
    kb.add(types.InlineKeyboardButton(text="✍️ Написать админу", url=f"https://t.me/{CONTACT.lstrip('@')}"))
    kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main"))
    bot.edit_message_text(chat_id=tg_id, message_id=call.message.id,
                          text=text, parse_mode="Markdown", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data in ["buy_1", "buy_5", "buy_10"])
def buy_process(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    n = int(call.data.replace("buy_", ""))
    prices = {1: 3, 5: 10, 10: 20}
    price = prices.get(n, 0)
    text = (
        f"💳 *ОПЛАТА*\n\n"
        f"Ты выбрал: *{n} запросов*\n"
        f"Сумма: *{price} ₽*\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📌 Как оплатить:\n"
        f"1. Напиши админу: {CONTACT}\n"
        f"2. Скинь скрин оплаты\n"
        f"3. Он выдаст запросы\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Твой логин: `{TG_TO_LOGIN.get(tg_id, '?')}`\n"
        f"⚠️ *Скинь этот логин админу*"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="✍️ Написать админу", url=f"https://t.me/{CONTACT.lstrip('@')}"))
    kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_requests"))
    bot.edit_message_text(chat_id=tg_id, message_id=call.message.id,
                          text=text, parse_mode="Markdown", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data == "buy_subscription")
def buy_subscription(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    text = (
        f"👑 *VIP-ПОДПИСКА*\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📅 1 неделя — *50 ₽*\n"
        f"📅 1 месяц — *150 ₽*\n"
        f"📅 3 месяца — *400 ₽*\n"
        f"📅 Навсегда — *1000 ₽*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👑 *Что даёт VIP:*\n"
        f"• ♾️ Безлимитный поиск\n"
        f"• 🥊 Битва смартфонов\n"
        f"• 🛠 Калькулятор дефектов\n"
        f"• 📊 ИИ-Оценка продажи\n"
        f"• 📈 Тренды цен\n"
        f"• ⚖️ Сравнение телефонов\n"
        f"• 🎯 Подбор под бюджет\n"
        f"• 💹 Прогноз цены\n"
        f"• 🚨 Проверка на развод\n"
        f"• 🎰 VIP-Рулетка\n\n"
        f"⚠️ *Если не хотите покупать запросы каждый раз — берите подписку!*\n\n"
        f"📝 По всем вопросам: {CONTACT}"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text="📅 Неделя — 50 ₽", callback_data="sub_week"))
    kb.add(types.InlineKeyboardButton(text="📅 Месяц — 150 ₽", callback_data="sub_month"))
    kb.add(types.InlineKeyboardButton(text="📅 3 месяца — 400 ₽", callback_data="sub_3month"))
    kb.add(types.InlineKeyboardButton(text="📅 Навсегда — 1000 ₽", callback_data="sub_forever"))
    kb.add(types.InlineKeyboardButton(text="✍️ Написать админу", url=f"https://t.me/{CONTACT.lstrip('@')}"))
    kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main"))
    bot.edit_message_text(chat_id=tg_id, message_id=call.message.id,
                          text=text, parse_mode="Markdown", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def sub_process(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    items = {"sub_week": ("1 неделя", "50 ₽"), "sub_month": ("1 месяц", "150 ₽"),
             "sub_3month": ("3 месяца", "400 ₽"), "sub_forever": ("Навсегда", "1000 ₽")}
    item = items.get(call.data)
    if not item:
        return
    text = (
        f"👑 *ОФОРМЛЕНИЕ VIP*\n\n"
        f"Срок: *{item[0]}*\n"
        f"Цена: *{item[1]}*\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📌 Напиши админу: {CONTACT}\n"
        f"👤 Логин: `{TG_TO_LOGIN.get(tg_id, '?')}`\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="✍️ Написать админу", url=f"https://t.me/{CONTACT.lstrip('@')}"))
    kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_subscription"))
    bot.edit_message_text(chat_id=tg_id, message_id=call.message.id,
                          text=text, parse_mode="Markdown", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data == "wheel")
def wheel(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    acc = get_acc(tg_id)
    login = TG_TO_LOGIN.get(tg_id)
    if not acc:
        return
    now = datetime.now()
    last = acc.get("last_wheel")
    if last:
        try:
            if now - datetime.fromisoformat(last) < timedelta(hours=24):
                left = timedelta(hours=24) - (now - datetime.fromisoformat(last))
                h, m = left.seconds // 3600, (left.seconds // 60) % 60
                bot.send_message(tg_id, f"⏳ Колесо через {h}ч {m}м")
                return
        except:
            pass
    msg = bot.send_message(tg_id, "🎡 *Крутим колесо...*", parse_mode="Markdown")

    def spin():
        prizes = [("₽", 500), ("₽", 1000), ("₽", 2000), ("₽", 5000),
                  ("req", 1), ("req", 2), ("req", 3),
                  ("vip", 1), ("empty", 0), ("empty", 0)]
        kind, val = random.choice(prizes)
        if kind == "₽":
            acc["balance"] += val
            res = f"💰 +{val} ₽"
        elif kind == "req":
            acc["requests"] += val
            res = f"🔍 +{val} запрос(а)"
        elif kind == "vip":
            vip_add(login, days=1)
            res = "👑 VIP на 1 день!"
        else:
            res = "😔 Пусто. В следующий раз повезёт!"
        acc["last_wheel"] = now.isoformat()
        save_data()
        bot.edit_message_text(chat_id=tg_id, message_id=msg.message_id,
                              text=f"🎡 *РЕЗУЛЬТАТ:*\n\n{res}",
                              parse_mode="Markdown")

    threading.Timer(2.0, spin).start()


@bot.callback_query_handler(func=lambda call: call.data == "game_casino")
def game_casino(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    acc = get_acc(tg_id)
    is_win = random.choice([True, True, True, False, False])
    msg = bot.send_message(tg_id, "🎰 Крутим барабан...")

    def spin():
        if is_win:
            CASINO_STREAKS[tg_id] = CASINO_STREAKS.get(tg_id, 0) + 1
            if CASINO_STREAKS[tg_id] >= 20:
                vip_add(TG_TO_LOGIN.get(tg_id), days=1)
                CASINO_STREAKS[tg_id] = 0
                save_data()
                bot.edit_message_text(chat_id=tg_id, message_id=msg.message_id,
                                      text="🏆 МЕГА-ВЫИГРЫШ! VIP на 1 день! /start")
            else:
                acc["balance"] += 200
                save_data()
                bot.edit_message_text(chat_id=tg_id, message_id=msg.message_id,
                                      text=f"🟢 ВЫИГРЫШ +200 ₽\nСерия: {CASINO_STREAKS[tg_id]}/20")
        else:
            CASINO_STREAKS[tg_id] = 0
            save_data()
            bot.edit_message_text(chat_id=tg_id, message_id=msg.message_id,
                                  text="🔴 ПРОИГРЫШ")

    threading.Timer(1.2, spin).start()


@bot.callback_query_handler(func=lambda call: call.data == "dice_casino")
def dice_casino(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    acc = get_acc(tg_id)
    msg = bot.send_message(tg_id, "🎲 Кидаю кубик...")

    def do_roll():
        roll = random.randint(1, 6)
        if roll >= 4:
            win = roll * 100
            acc["balance"] += win
            save_data()
            bot.edit_message_text(chat_id=tg_id, message_id=msg.message_id,
                                  text=f"🎲 Выпало: *{roll}*\n🟢 +{win} ₽\n💰 Баланс: {acc['balance']} ₽",
                                  parse_mode="Markdown")
        else:
            loss = roll * 100
            acc["balance"] = max(0, acc["balance"] - loss)
            save_data()
            bot.edit_message_text(chat_id=tg_id, message_id=msg.message_id,
                                  text=f"🎲 Выпало: *{roll}*\n🔴 -{loss} ₽\n💰 Баланс: {acc['balance']} ₽",
                                  parse_mode="Markdown")

    threading.Timer(1.0, do_roll).start()


@bot.callback_query_handler(func=lambda call: call.data == "game_bet")
def setup_bet(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    acc = get_acc(tg_id)
    if acc["balance"] < 500:
        bot.send_message(tg_id, "❌ Мало средств. Нужно 500 ₽.")
        return
    p1, p2 = random.choice(PHONE_DATABASE), random.choice(PHONE_DATABASE)
    USER_STATE[tg_id] = {"state": "bet", "p1": p1, "p2": p2}
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(text=f"👍 {p1['model'][:15]}", callback_data="bet_1"),
        types.InlineKeyboardButton(text=f"👍 {p2['model'][:15]}", callback_data="bet_2")
    )
    bot.send_message(tg_id,
                     f"🎲 *СТАВКИ*\n\n"
                     f"1️⃣ {p1['model']}\n   CPU: {p1['cpu_score']}\n\n"
                     f"2️⃣ {p2['model']}\n   CPU: {p2['cpu_score']}\n\n"
                     f"Ставка: 500 ₽",
                     parse_mode="Markdown", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data in ["bet_1", "bet_2"])
def process_bet(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    st = USER_STATE.get(tg_id)
    if not st or st.get("state") != "bet":
        return
    acc = get_acc(tg_id)
    p1, p2 = st["p1"], st["p2"]
    USER_STATE[tg_id] = None
    acc["balance"] -= 500
    choice = 1 if call.data == "bet_1" else 2
    winner = 1 if p1["cpu_score"] >= p2["cpu_score"] else 2
    wname = p1["model"] if winner == 1 else p2["model"]
    if choice == winner:
        acc["balance"] += 1200
        bot.send_message(tg_id, f"🟢 ВЫИГРЫШ! Победил: {wname}\n💰 Баланс: {acc['balance']} ₽")
    else:
        bot.send_message(tg_id, f"🔴 ПРОИГРЫШ! Победил: {wname}\n💰 Баланс: {acc['balance']} ₽")
    save_data()
    

@bot.callback_query_handler(func=lambda call: call.data == "daily_bonus")
def daily_bonus(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    acc = get_acc(tg_id)
    now = datetime.now()
    last = LAST_BONUS.get(tg_id)
    if last and (now - last) < timedelta(hours=24):
        left = timedelta(hours=24) - (now - last)
        h, m = left.seconds // 3600, (left.seconds // 60) % 60
        bot.send_message(tg_id, f"⏳ Бонус через {h}ч {m}м")
        return
    bonus = 500 + random.randint(0, 500)
    acc["balance"] += bonus
    LAST_BONUS[tg_id] = now
    save_data()
    bot.send_message(tg_id, f"🎁 Бонус: +{bonus} ₽\n💰 Баланс: {acc['balance']} ₽")


@bot.callback_query_handler(func=lambda call: call.data == "enter_promo")
def enter_promo(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    USER_STATE[tg_id] = {"state": "waiting_promo"}
    bot.edit_message_text(chat_id=tg_id, message_id=call.message.id,
                          text="🎫 Введи промокод:")


@bot.message_handler(func=lambda m: USER_STATE.get(m.chat.id, {}).get("state") == "waiting_promo", content_types=['text'])
def process_promo(message):
    tg_id = message.chat.id
    code = message.text.strip().upper()
    USER_STATE[tg_id] = None
    acc = get_acc(tg_id)
    if code not in PROMOCODES:
        bot.reply_to(message, "❌ Неверный промокод.")
        return
    promo = PROMOCODES[code]
    if promo["uses_left"] <= 0:
        bot.reply_to(message, "❌ Промокод исчерпан.")
        return
    if promo["type"] == "balance":
        acc["balance"] += promo["value"]
        bot.reply_to(message, f"🎉 +{promo['value']} ₽! Баланс: {acc['balance']} ₽")
    elif promo["type"] == "requests":
        acc["requests"] += promo["value"]
        bot.reply_to(message, f"🎉 +{promo['value']} запросов! Теперь: {acc['requests']}")
    elif promo["type"] == "vip":
        vip_add(TG_TO_LOGIN.get(tg_id), days=promo["value"])
        bot.reply_to(message, f"👑 VIP на {promo['value']} дней!")
    promo["uses_left"] -= 1
    save_data()


@bot.callback_query_handler(func=lambda call: call.data == "top_players")
def top_players(call):
    bot.answer_callback_query(call.id)
    sorted_acc = sorted(ACCOUNTS.items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
    text = "🏆 *ТОП-10 ИГРОКОВ*\n\n"
    for i, (login, acc) in enumerate(sorted_acc, 1):
        mark = "👑" if is_vip(login) else ""
        text += f"{i}. `{login}` {mark} — {acc['balance']} ₽\n"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text=text, parse_mode="Markdown", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data == "achievements")
def achievements(call):
    bot.answer_callback_query(call.id)
    acc = get_acc(call.message.chat.id)
    if not acc:
        return
    all_ach = [
        ("first_search", "🥇 Первый поиск"),
        ("ten_search", "🎯 10 поисков"),
        ("vip", "💎 Первый VIP"),
        ("millionaire", "👑 Миллионер"),
        ("streak7", "🔥 Стрик 7 дней"),
        ("ref5", "👥 5 друзей"),
        ("casino10", "🎰 10 побед в казино"),
        ("rich100k", "💰 100 000 ₽"),
        ("top1", "🏆 Топ-1"),
        ("luck", "🍀 Удача дня"),
    ]
    ach_list = acc.get("achievements", [])
    text = "🥇 *ДОСТИЖЕНИЯ*\n\n"
    for key, name in all_ach:
        mark = "✅" if key in ach_list else "⬜"
        text += f"{mark} {name}\n"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text=text, parse_mode="Markdown", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data == "vip_menu")
def vip_menu(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    login = TG_TO_LOGIN.get(tg_id)
    if not is_vip(login):
        bot.answer_callback_query(call.id, "❌ VIP истёк", show_alert=True)
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text="🥊 Битва смартфонов", callback_data="vip_battle"))
    kb.add(types.InlineKeyboardButton(text="🛠 Калькулятор дефектов", callback_data="vip_repair"))
    kb.add(types.InlineKeyboardButton(text="📊 ИИ-Оценка продажи", callback_data="vip_sell"))
    kb.add(types.InlineKeyboardButton(text="📈 Тренды цен", callback_data="vip_trends"))
    kb.add(types.InlineKeyboardButton(text="⚖️ Сравнить 2 телефона", callback_data="vip_compare"))
    kb.add(types.InlineKeyboardButton(text="🎯 Подбор под бюджет", callback_data="vip_budget"))
    kb.add(types.InlineKeyboardButton(text="💹 Прогноз цены", callback_data="vip_forecast"))
    kb.add(types.InlineKeyboardButton(text="🚨 Проверка на развод", callback_data="vip_scam"))
    kb.add(types.InlineKeyboardButton(text="🎰 VIP-Рулетка", callback_data="vip_roulette"))
    kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main"))
    bot.edit_message_text(chat_id=tg_id, message_id=call.message.id,
                          text="👑 *VIP-МЕНЮ*", parse_mode="Markdown", reply_markup=kb)


def require_vip_cb(call):
    login = TG_TO_LOGIN.get(call.message.chat.id)
    if not is_vip(login):
        bot.answer_callback_query(call.id, "❌ Нужен VIP", show_alert=True)
        return False
    return True


@bot.callback_query_handler(func=lambda call: call.data == "vip_battle")
def vip_battle(call):
    if not require_vip_cb(call): return
    bot.answer_callback_query(call.id)
    USER_STATE[call.message.chat.id] = {"state": "vip_battle_input"}
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="🥊 Формат: `Телефон1 против Телефон2`", parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "vip_repair")
def vip_repair(call):
    if not require_vip_cb(call): return
    bot.answer_callback_query(call.id)
    USER_STATE[call.message.chat.id] = {"state": "vip_repair_input"}
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="🛠 Опиши дефекты: экран, аккумулятор, камера...")


@bot.callback_query_handler(func=lambda call: call.data == "vip_sell")
def vip_sell(call):
    if not require_vip_cb(call): return
    bot.answer_callback_query(call.id)
    USER_STATE[call.message.chat.id] = {"state": "vip_sell_input"}
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="📊 Напиши модель телефона:")


@bot.callback_query_handler(func=lambda call: call.data == "vip_compare")
def vip_compare(call):
    if not require_vip_cb(call): return
    bot.answer_callback_query(call.id)
    USER_STATE[call.message.chat.id] = {"state": "vip_compare_input"}
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="⚖️ Формат: `Телефон1 vs Телефон2`", parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "vip_budget")
def vip_budget(call):
    if not require_vip_cb(call): return
    bot.answer_callback_query(call.id)
    USER_STATE[call.message.chat.id] = {"state": "vip_budget_input"}
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="🎯 Напиши бюджет в ₽:")


@bot.callback_query_handler(func=lambda call: call.data == "vip_forecast")
def vip_forecast(call):
    if not require_vip_cb(call): return
    bot.answer_callback_query(call.id)
    USER_STATE[call.message.chat.id] = {"state": "vip_forecast_input"}
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="💹 Напиши модель:")


@bot.callback_query_handler(func=lambda call: call.data == "vip_scam")
def vip_scam(call):
    if not require_vip_cb(call): return
    bot.answer_callback_query(call.id)
    USER_STATE[call.message.chat.id] = {"state": "vip_scam_input"}
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="🚨 Опиши объявление/цену:")
                        

@bot.callback_query_handler(func=lambda call: call.data == "vip_trends")
def vip_trends(call):
    if not require_vip_cb(call): return
    bot.answer_callback_query(call.id)
    random.seed(int(datetime.now().strftime("%Y%m%d")))
    up = random.sample(PHONE_DATABASE, 5)
    down = random.sample(PHONE_DATABASE, 5)
    random.seed()
    text = "📈 *ТРЕНДЫ ЦЕН*\n\n📈 Растут:\n"
    for p in up:
        text += f"⬆️ {p['model']} (+{random.randint(3,15)}%)\n"
    text += "\n📉 Падают:\n"
    for p in down:
        text += f"⬇️ {p['model']} (-{random.randint(3,15)}%)\n"
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "vip_roulette")
def vip_roulette(call):
    if not require_vip_cb(call): return
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    acc = get_acc(tg_id)
    if acc["balance"] < 1000:
        bot.send_message(tg_id, "❌ Нужно 1000 ₽ на ставку.")
        return
    msg = bot.send_message(tg_id, "🎰 Крутим VIP-рулетку...")

    def spin():
        mult = random.choice([0, 0, 2, 2, 5, 10])
        acc["balance"] -= 1000
        if mult == 0:
            bot.edit_message_text(chat_id=tg_id, message_id=msg.message_id,
                                  text=f"🔴 -1000 ₽. Баланс: {acc['balance']} ₽")
        else:
            win = 1000 * mult
            acc["balance"] += win
            bot.edit_message_text(chat_id=tg_id, message_id=msg.message_id,
                                  text=f"🎉 x{mult}! +{win} ₽. Баланс: {acc['balance']} ₽")
        save_data()

    threading.Timer(1.5, spin).start()


@bot.message_handler(func=lambda m: USER_STATE.get(m.chat.id, {}).get("state", "").startswith("vip_") and USER_STATE.get(m.chat.id, {}).get("state", "").endswith("_input"), content_types=['text'])
def handle_vip_input(message):
    tg_id = message.chat.id
    st = USER_STATE.get(tg_id)
    if not st:
        return
    state = st["state"]
    USER_STATE[tg_id] = None
    text_in = message.text.strip()

    if state == "vip_battle_input":
        parts = re.split(r"\s+против\s+", text_in, flags=re.IGNORECASE)
        if len(parts) != 2:
            bot.reply_to(message, "❌ Формат: Телефон1 против Телефон2")
            return
        a, b = find_phone(parts[0]), find_phone(parts[1])
        if not a or not b:
            bot.reply_to(message, "❌ Не распознал модель.")
            return
        w = a if a["cpu_score"] >= b["cpu_score"] else b
        bot.reply_to(message,
                     f"🥊 *БИТВА*\n\n"
                     f"1️⃣ {a['model']} — CPU {a['cpu_score']}\n"
                     f"2️⃣ {b['model']} — CPU {b['cpu_score']}\n\n"
                     f"🏆 Победитель: *{w['model']}*\n⚠️ {w['weakness']}",
                     parse_mode="Markdown")

    elif state == "vip_repair_input":
        low = text_in.lower()
        prices = {"экран": 3500, "дисплей": 3500, "аккумулятор": 1500, "батарея": 1500,
                  "камер": 2000, "разъем": 1200, "кнопк": 800, "динамик": 900,
                  "стекл": 1800, "корпус": 2500, "вода": 4000}
        total = 2000
        found = []
        for k, v in prices.items():
            if k in low:
                total += v
                found.append(f"• {k.title()} — {v} ₽")
        if not found:
            bot.reply_to(message, f"🛠 Базовая диагностика: 2000 ₽")
        else:
            bot.reply_to(message, "🛠 *Дефекты:*\n" + "\n".join(found) + f"\n\n💵 Итого: *{total} ₽*",
                         parse_mode="Markdown")

    elif state == "vip_sell_input":
        p = find_phone(text_in)
        if not p:
            bot.reply_to(message, "❌ Модель не найдена.")
            return
        resale = int(p["price"] * 0.65)
        bot.reply_to(message,
                     f"📊 *ОЦЕНКА*\n\n{p['model']}\n"
                     f"💰 Рыночная: {p['price']} ₽\n"
                     f"📉 Продажа: *{resale} ₽*\n⚠️ {p['weakness']}",
                     parse_mode="Markdown")

    elif state == "vip_compare_input":
        parts = re.split(r"\s+vs\s+", text_in, flags=re.IGNORECASE)
        if len(parts) != 2:
            bot.reply_to(message, "❌ Формат: A vs B")
            return
        a, b = find_phone(parts[0]), find_phone(parts[1])
        if not a or not b:
            bot.reply_to(message, "❌ Не распознал.")
            return
        bot.reply_to(message,
                     f"⚖️ *СРАВНЕНИЕ*\n\n"
                     f"1️⃣ {a['model']}\n   CPU {a['cpu_score']} | {a['price']} ₽\n\n"
                     f"2️⃣ {b['model']}\n   CPU {b['cpu_score']} | {b['price']} ₽\n\n"
                     f"🏆 {a['model'] if a['cpu_score'] >= b['cpu_score'] else b['model']}",
                     parse_mode="Markdown")

    elif state == "vip_budget_input":
        m = re.search(r"\d+", text_in)
        if not m:
            bot.reply_to(message, "❌ Введи число.")
            return
        budget = int(m.group())
        matches = [p for p in PHONE_DATABASE if p["price"] <= budget]
        top = sorted(matches, key=lambda x: x["cpu_score"], reverse=True)[:7]
        if not top:
            bot.reply_to(message, "😔 Ничего не нашёл.")
            return
        lines = [f"🎯 *До {budget} ₽:*\n"]
        for i, p in enumerate(top, 1):
            lines.append(f"{i}. {p['model']}\n   {p['price']} ₽ | CPU {p['cpu_score']}")
        bot.reply_to(message, "\n".join(lines), parse_mode="Markdown")

    elif state == "vip_forecast_input":
        p = find_phone(text_in)
        if not p:
            bot.reply_to(message, "❌ Не нашёл.")
            return
        m1 = int(p["price"] * random.uniform(0.85, 1.10))
        m2 = int(p["price"] * random.uniform(0.72, 1.05))
        m3 = int(p["price"] * random.uniform(0.60, 1.00))
        bot.reply_to(message,
                     f"💹 *ПРОГНОЗ*\n\n{p['model']}\n\n"
                     f"Сейчас: {p['price']} ₽\n"
                     f"1 мес: {m1} ₽\n2 мес: {m2} ₽\n3 мес: {m3} ₽",
                     parse_mode="Markdown")

    elif state == "vip_scam_input":
        low = text_in.lower()
        flags = []
        if any(w in low for w in ["срочно", "быстро", "торопись"]):
            flags.append("⚠️ Давят срочностью")
        if "предоплат" in low or "перевод" in low:
            flags.append("⚠️ Просят предоплату")
        if "без проверки" in low or "не встреча" in low:
            flags.append("⚠️ Отказ от встречи")
        m = re.search(r"\d+", low)
        if m and int(m.group()) < 3000:
            flags.append("⚠️ Подозрительно низкая цена")
        if "iphone" in low and m and int(m.group()) < 15000:
            flags.append("⚠️ iPhone дешевле 15к — почти 100% развод")
        if not flags:
            bot.reply_to(message, "✅ Явных флагов не нашёл. Но проверяй лично!")
        else:
            bot.reply_to(message, "🚨 *ФЛАГИ РАЗВОДА:*\n\n" + "\n".join(flags), parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    bot.answer_callback_query(call.id)
    tg_id = call.message.chat.id
    if not is_admin(tg_id):
        bot.answer_callback_query(call.id, "❌ Нет доступа", show_alert=True)
        return
    total_users = len(ACCOUNTS)
    total_balance = sum(a["balance"] for a in ACCOUNTS.values())
    total_vip = sum(1 for l in ACCOUNTS if is_vip(l))
    total_requests = sum(a["requests"] for a in ACCOUNTS.values())
    text = (
        f"🛡 *АДМИН-ПАНЕЛЬ*\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👥 Юзеров: {total_users}\n"
        f"👑 VIP: {total_vip}\n"
        f"💰 Общий баланс: {total_balance} ₽\n"
        f"🔍 Запросов у всех: {total_requests}\n"
        f"🎫 Промокодов: {len(PROMOCODES)}\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text="👥 Список юзеров", callback_data="adm_users"))
    kb.add(types.InlineKeyboardButton(text="🔍 Найти юзера", callback_data="adm_find"))
    kb.add(types.InlineKeyboardButton(text="💰 Выдать баланс", callback_data="adm_balance"))
    kb.add(types.InlineKeyboardButton(text="🔍 Выдать запросы", callback_data="adm_requests"))
    kb.add(types.InlineKeyboardButton(text="👑 Выдать VIP", callback_data="adm_vip"))
    kb.add(types.InlineKeyboardButton(text="🚫 Бан / разбан", callback_data="adm_ban"))
    kb.add(types.InlineKeyboardButton(text="🎫 Создать промокод", callback_data="adm_promo"))
    kb.add(types.InlineKeyboardButton(text="📋 Список промокодов", callback_data="adm_promo_list"))
    kb.add(types.InlineKeyboardButton(text="📢 Рассылка", callback_data="adm_broadcast"))
    kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main"))
    bot.edit_message_text(chat_id=tg_id, message_id=call.message.id,
                          text=text, parse_mode="Markdown", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data == "adm_users")
def adm_users(call):
    if not is_admin(call.message.chat.id):
        return
    bot.answer_callback_query(call.id)
    sorted_acc = sorted(ACCOUNTS.items(), key=lambda x: x[1]["balance"], reverse=True)[:30]
    text = "👥 *ТОП-30 ЮЗЕРОВ*\n\n"
    for i, (login, acc) in enumerate(sorted_acc, 1):
        ban = "🚫" if acc.get("banned") else ""
        vip = "👑" if is_vip(login) else ""
        text += f"{i}. `{login}` {vip}{ban} — {acc['balance']} ₽, {acc['requests']} req\n"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text=text, parse_mode="Markdown", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data == "adm_find")
def adm_find(call):
    if not is_admin(call.message.chat.id):
        return
    bot.answer_callback_query(call.id)
    USER_STATE[call.message.chat.id] = {"state": "adm_find_input"}
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="🔍 Напиши логин юзера (6 цифр):")


@bot.callback_query_handler(func=lambda call: call.data == "adm_balance")
def adm_balance(call):
    if not is_admin(call.message.chat.id):
        return
    bot.answer_callback_query(call.id)
    USER_STATE[call.message.chat.id] = {"state": "adm_balance_input"}
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="💰 Формат: `ЛОГИН СУММА`\n\nПример: `482913 10000`",
                          parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "adm_requests")
def adm_requests(call):
    if not is_admin(call.message.chat.id):
        return
    bot.answer_callback_query(call.id)
    USER_STATE[call.message.chat.id] = {"state": "adm_requests_input"}
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="🔍 Формат: `ЛОГИН КОЛ-ВО`\n\nПример: `482913 10`",
                          parse_mode="Markdown")
                          

@bot.callback_query_handler(func=lambda call: call.data == "adm_vip")
def adm_vip(call):
    if not is_admin(call.message.chat.id):
        return
    bot.answer_callback_query(call.id)
    USER_STATE[call.message.chat.id] = {"state": "adm_vip_input"}
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="👑 Формат: `ЛОГИН СРОК`\n\n"
                               "Сроки: `1h`, `1d`, `7d`, `30d`, `forever`\n\n"
                               "Примеры:\n"
                               "`482913 1h` — 1 час\n"
                               "`482913 7d` — 7 дней\n"
                               "`482913 forever` — навсегда",
                          parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "adm_ban")
def adm_ban(call):
    if not is_admin(call.message.chat.id):
        return
    bot.answer_callback_query(call.id)
    USER_STATE[call.message.chat.id] = {"state": "adm_ban_input"}
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="🚫 Формат: `ЛОГИН` — бан/разбан (переключает)\n\nПример: `482913`",
                          parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "adm_promo")
def adm_promo(call):
    if not is_admin(call.message.chat.id):
        return
    bot.answer_callback_query(call.id)
    USER_STATE[call.message.chat.id] = {"state": "adm_promo_input"}
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="🎫 Формат: `КОД ТИП ЗНАЧЕНИЕ КОЛ-ВО`\n\n"
                               "Типы: `balance`, `requests`, `vip`\n\n"
                               "Примеры:\n"
                               "`NEWYEAR balance 5000 100` — +5000₽, 100 юзов\n"
                               "`FREEREQ requests 5 50` — +5 запросов, 50 юзов\n"
                               "`VIPGIFT vip 7 10` — VIP на 7 дней, 10 юзов",
                          parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "adm_promo_list")
def adm_promo_list(call):
    if not is_admin(call.message.chat.id):
        return
    bot.answer_callback_query(call.id)
    if not PROMOCODES:
        text = "🎫 Промокодов нет."
    else:
        text = "🎫 *СПИСОК ПРОМОКОДОВ:*\n\n"
        for code, p in PROMOCODES.items():
            text += f"`{code}` — {p['type']} {p['value']}, осталось {p['uses_left']}\n"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text=text, parse_mode="Markdown", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data == "adm_broadcast")
def adm_broadcast(call):
    if not is_admin(call.message.chat.id):
        return
    bot.answer_callback_query(call.id)
    USER_STATE[call.message.chat.id] = {"state": "adm_broadcast_input"}
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="📢 Напиши текст рассылки:")


@bot.message_handler(func=lambda m: USER_STATE.get(m.chat.id, {}).get("state", "").startswith("adm_") and USER_STATE.get(m.chat.id, {}).get("state", "").endswith("_input"), content_types=['text'])
def handle_admin_input(message):
    tg_id = message.chat.id
    if not is_admin(tg_id):
        return
    st = USER_STATE.get(tg_id)
    if not st:
        return
    state = st["state"]
    USER_STATE[tg_id] = None
    text_in = message.text.strip()

    if state == "adm_find_input":
        login = text_in
        if login not in ACCOUNTS:
            bot.reply_to(message, "❌ Не найден.")
            return
        acc = ACCOUNTS[login]
        ban = "🚫 ЗАБАНЕН" if acc.get("banned") else "✅ активен"
        vip = f"👑 до {vip_until_str(login)}" if is_vip(login) else "❌ нет VIP"
        bot.reply_to(message,
                     f"👤 *ЛОГИН:* `{login}`\n\n"
                     f"💰 Баланс: {acc['balance']} ₽\n"
                     f"🔍 Запросы: {acc['requests']}\n"
                     f"👑 VIP: {vip}\n"
                     f"🔥 Стрик: {acc.get('streak', 0)}\n"
                     f"👥 Друзей: {acc.get('friends', 0)}\n"
                     f"🚦 Статус: {ban}\n"
                     f"🆔 TG: `{acc.get('tg_id', '?')}`",
                     parse_mode="Markdown")

    elif state == "adm_balance_input":
        parts = text_in.split()
        if len(parts) != 2 or not parts[1].lstrip("-").isdigit():
            bot.reply_to(message, "❌ Формат: ЛОГИН СУММА")
            return
        login, amount = parts[0], int(parts[1])
        if login not in ACCOUNTS:
            bot.reply_to(message, "❌ Юзер не найден.")
            return
        ACCOUNTS[login]["balance"] += amount
        save_data()
        bot.reply_to(message, f"✅ {login}: баланс {amount:+d} ₽\nТеперь: {ACCOUNTS[login]['balance']} ₽")

    elif state == "adm_requests_input":
        parts = text_in.split()
        if len(parts) != 2 or not parts[1].lstrip("-").isdigit():
            bot.reply_to(message, "❌ Формат: ЛОГИН КОЛ-ВО")
            return
        login, amount = parts[0], int(parts[1])
        if login not in ACCOUNTS:
            bot.reply_to(message, "❌ Юзер не найден.")
            return
        ACCOUNTS[login]["requests"] += amount
        save_data()
        bot.reply_to(message, f"✅ {login}: запросы {amount:+d}\nТеперь: {ACCOUNTS[login]['requests']}")

    elif state == "adm_vip_input":
        parts = text_in.split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ Формат: ЛОГИН СРОК")
            return
        login, term = parts[0], parts[1].lower()
        if login not in ACCOUNTS:
            bot.reply_to(message, "❌ Юзер не найден.")
            return
        if term == "forever":
            vip_add(login, days=36500)
        elif term.endswith("h") and term[:-1].isdigit():
            vip_add(login, hours=int(term[:-1]))
        elif term.endswith("d") and term[:-1].isdigit():
            vip_add(login, days=int(term[:-1]))
        elif term.endswith("m") and term[:-1].isdigit():
            vip_add(login, minutes=int(term[:-1]))
        else:
            bot.reply_to(message, "❌ Неверный срок. Используй 1h / 7d / forever")
            return
        save_data()
        try:
            bot.send_message(ACCOUNTS[login]["tg_id"], f"👑 Тебе выдан VIP! До: {vip_until_str(login)}")
        except:
            pass
        bot.reply_to(message, f"✅ VIP выдан {login} до {vip_until_str(login)}")

    elif state == "adm_ban_input":
        login = text_in
        if login not in ACCOUNTS:
            bot.reply_to(message, "❌ Юзер не найден.")
            return
        acc = ACCOUNTS[login]
        acc["banned"] = not acc.get("banned", False)
        save_data()
        status = "🚫 ЗАБАНЕН" if acc["banned"] else "✅ РАЗБАНЕН"
        bot.reply_to(message, f"{status}: `{login}`", parse_mode="Markdown")

    elif state == "adm_promo_input":
        parts = text_in.split()
        if len(parts) != 4:
            bot.reply_to(message, "❌ Формат: КОД ТИП ЗНАЧЕНИЕ КОЛ-ВО")
            return
        code, ptype, val, uses = parts[0].upper(), parts[1], parts[2], parts[3]
        if ptype not in ["balance", "requests", "vip"]:
            bot.reply_to(message, "❌ Тип: balance / requests / vip")
            return
        if not val.isdigit() or not uses.isdigit():
            bot.reply_to(message, "❌ Значение и кол-во — цифры.")
            return
        PROMOCODES[code] = {"type": ptype, "value": int(val), "uses_left": int(uses)}
        save_data()
        bot.reply_to(message, f"✅ Промокод `{code}` создан\n{ptype} {val}, использований: {uses}",
                     parse_mode="Markdown")

    elif state == "adm_broadcast_input":
        sent = 0
        failed = 0
        for login, acc in ACCOUNTS.items():
            try:
                bot.send_message(acc["tg_id"], f"📢 *РАССЫЛКА*\n\n{text_in}", parse_mode="Markdown")
                sent += 1
                time.sleep(0.05)
            except:
                failed += 1
        bot.reply_to(message, f"📢 Отправлено: {sent}\n❌ Не дошло: {failed}")


@bot.message_handler(func=lambda m: True, content_types=['text'])
def fallback_handler(message):
    tg_id = message.chat.id
    if tg_id in TG_TO_LOGIN:
        bot.send_message(tg_id, "🤔 Не понял. Используй кнопки меню или /start")


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id,
                     f"🆘 *ПОМОЩЬ*\n\n"
                     f"Нажми /start для меню.\n"
                     f"По вопросам: {CONTACT}",
                     parse_mode="Markdown")


@bot.message_handler(commands=['admin'])
def admin_command(message):
    if not is_admin(message.chat.id):
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="🛡 Открыть админ-панель", callback_data="admin_panel"))
    bot.send_message(message.chat.id, "🛡 Админ-панель:", reply_markup=kb)
    import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def run_bot():
    load_data()
    print("🚀 Бот запущен...")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"📱 База: {len(PHONE_DATABASE)} телефонов")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"💥 Краш polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_web).start()
    run_bot()


                         
