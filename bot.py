"""
Telegram-бот: опитувальник про дизайн квартири.

Сценарій:
  /start -> питає ім'я -> прізвище -> кілька питань з кнопками
  -> надсилає всі відповіді власнику (тобі) у Telegram.

Є кнопка "⬅️ Назад" на кожному питанні та фото-приклади стилів
(якщо покласти зображення в папку photos/ — див. STYLE_PHOTOS).
"""

import logging
import os

from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")  # твій особистий chat_id

# папка з фото-прикладами (поряд із bot.py)
PHOTOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "photos")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Стани діалогу ---
NAME, SURNAME, COLOR, BRIGHTNESS, ZONING, STYLE = range(6)

# --- Питання опитувальника: стан -> (текст, [(підпис_кнопки, значення), ...]) ---
QUESTIONS = {
    COLOR: (
        "🎨 Який дизайн вам ближчий?",
        [
            ("Кольоровий, яскравий", "Кольоровий"),
            ("Однотонний, спокійний", "Однотонний"),
        ],
    ),
    BRIGHTNESS: (
        "💡 Яку гаму бажаєте?",
        [
            ("Світлу", "Світла"),
            ("Темну", "Темна"),
            ("Змішану", "Змішана"),
        ],
    ),
    ZONING: (
        "📐 Як організувати простір?",
        [
            ("Розділити на зони", "Зонування"),
            ("Все як одна зона", "Єдиний простір"),
        ],
    ),
    STYLE: (
        "🏠 Який стиль приміщення?",
        [
            ("Лофт", "Лофт"),
            ("Скандинавський", "Скандинавський"),
            ("Мінімалізм", "Мінімалізм"),
            ("Класика", "Класика"),
            ("Хай-тек", "Хай-тек"),
        ],
    ),
}

# стан -> (ключ_для_збереження, наступний_стан)
FLOW = {
    COLOR: ("color", BRIGHTNESS),
    BRIGHTNESS: ("brightness", ZONING),
    ZONING: ("zoning", STYLE),
    STYLE: ("style", ConversationHandler.END),
}

# стан -> куди веде кнопка "Назад" (SURNAME = текстовий крок прізвища)
BACK_TO = {
    COLOR: SURNAME,
    BRIGHTNESS: COLOR,
    ZONING: BRIGHTNESS,
    STYLE: ZONING,
}

# стиль -> ім'я файлу з прикладом у папці photos/
STYLE_PHOTOS = {
    "Лофт": "loft.jpg",
    "Скандинавський": "scandinavian.jpg",
    "Мінімалізм": "minimalism.jpg",
    "Класика": "classic.jpg",
    "Хай-тек": "hitech.jpg",
}


def build_keyboard(state: int) -> InlineKeyboardMarkup:
    """Кнопки для питання. callback_data = 'стан:значення' або 'back:стан'."""
    _, options = QUESTIONS[state]
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"{state}:{value}")]
        for label, value in options
    ]
    buttons.append(
        [InlineKeyboardButton("⬅️ Назад", callback_data=f"back:{state}")]
    )
    return InlineKeyboardMarkup(buttons)


async def send_style_examples(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Надсилає фото-приклади стилів (ті, що є у папці photos/)."""
    media = []
    open_files = []
    for style, filename in STYLE_PHOTOS.items():
        path = os.path.join(PHOTOS_DIR, filename)
        if os.path.exists(path):
            f = open(path, "rb")
            open_files.append(f)
            media.append(InputMediaPhoto(media=f, caption=style))
    if not media:
        return  # фото ще не додані — просто пропускаємо
    try:
        await context.bot.send_media_group(chat_id=chat_id, media=media)
    except Exception as e:
        logger.error("Не вдалося надіслати фото-приклади: %s", e)
    finally:
        for f in open_files:
            f.close()


async def ask_question(
    chat_id: int, state: int, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Показує питання з кнопками. Для стилю — спершу фото-приклади."""
    if state == STYLE:
        await send_style_examples(chat_id, context)
    question, _ = QUESTIONS[state]
    await context.bot.send_message(
        chat_id=chat_id, text=question, reply_markup=build_keyboard(state)
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Вітаю! 👋 Я допоможу зібрати ваші побажання щодо дизайну квартири.\n\n"
        "Для початку — як вас звати? (ім'я)"
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("Дякую! А тепер ваше прізвище?")
    return SURNAME


async def get_surname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["surname"] = update.message.text.strip()
    await ask_question(update.effective_chat.id, COLOR, context)
    return COLOR


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє натискання кнопок опитувальника (вибір відповіді або 'Назад')."""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

    action, payload = query.data.split(":", 1)

    # --- кнопка "Назад" ---
    if action == "back":
        state = int(payload)
        target = BACK_TO[state]
        if target == SURNAME:
            await query.edit_message_text("↩️ Повертаємось. Введіть прізвище ще раз:")
            return SURNAME
        await query.edit_message_text("↩️ Повертаємось до попереднього питання…")
        await ask_question(chat_id, target, context)
        return target

    # --- вибір відповіді ---
    state = int(action)
    value = payload
    key, next_state = FLOW[state]
    context.user_data[key] = value

    question, _ = QUESTIONS[state]
    await query.edit_message_text(f"{question}\n✅ Ваш вибір: {value}")

    if next_state == ConversationHandler.END:
        await finish(update, context)
        return ConversationHandler.END

    await ask_question(chat_id, next_state, context)
    return next_state


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Формує підсумок і надсилає його власнику + користувачу."""
    d = context.user_data
    user = update.effective_user

    summary = (
        "🆕 Нова заявка на дизайн квартири!\n\n"
        f"👤 Ім'я: {d.get('name', '—')}\n"
        f"👤 Прізвище: {d.get('surname', '—')}\n"
        f"🎨 Дизайн: {d.get('color', '—')}\n"
        f"💡 Гама: {d.get('brightness', '—')}\n"
        f"📐 Простір: {d.get('zoning', '—')}\n"
        f"🏠 Стиль: {d.get('style', '—')}\n\n"
        f"📎 Telegram: @{user.username or 'без_нікнейму'} (id {user.id})"
    )

    if OWNER_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=summary)
        except Exception as e:
            logger.error("Не вдалося надіслати власнику: %s", e)
    else:
        logger.warning("OWNER_CHAT_ID не заданий — заявку нікому надсилати.")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Дякуємо! 🙌 Ваші відповіді збережено та передано дизайнеру.\n"
        "Щоб пройти опитування знову — натисніть /start",
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Опитування скасовано. /start — почати заново.")
    return ConversationHandler.END


async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Допоміжна команда: показує твій chat_id (для налаштування OWNER_CHAT_ID)."""
    await update.message.reply_text(f"Ваш chat_id: {update.effective_chat.id}")


def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit(
            "❌ Не заданий BOT_TOKEN. Створи файл .env (див. .env.example)."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_surname)],
            COLOR: [CallbackQueryHandler(handle_answer)],
            BRIGHTNESS: [CallbackQueryHandler(handle_answer)],
            ZONING: [CallbackQueryHandler(handle_answer)],
            STYLE: [CallbackQueryHandler(handle_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("whoami", whoami))

    logger.info("Бот запущено. Натисни Ctrl+C для зупинки.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
