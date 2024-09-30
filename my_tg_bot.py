from telethon import TelegramClient, errors
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import logging
import time

# Настройки Telegram API
api_id = 'YOUR_API_ID'
api_hash = 'YOUR_API_HASH'
bot_token = 'YOUR_BOT_TOKEN'

# Инициализация клиента Telegram
client = TelegramClient('session_name', api_id, api_hash)

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_variants(word, max_variants=50):
    variants = set()

    def backtrack(current_word, index):
        if len(variants) >= max_variants:  # Прекращаем, если достигли лимита
            return
        if index >= len(word):  # Если достигли конца слова, добавляем его в варианты
            variants.add(current_word)
            return

        # Добавляем текущую букву без дублирования
        backtrack(current_word + word[index], index + 1)

        # Дублируем текущую букву
        backtrack(current_word + word[index] * 2, index + 1)

        # Утроим текущую букву
        backtrack(current_word + word[index] * 3, index + 1)

    backtrack('', 0)

    return list(variants)

async def get_user_profile_photo(username):
    try:
        user = await client.get_entity(username)
        if user.photo:
            return await client.download_profile_photo(user)
        else:
            return None
    except (errors.UsernameNotOccupiedError, errors.UsernameInvalidError):
        return None
    except errors.FloodWaitError as e:
        logger.warning(f"FloodWaitError: {e.seconds} seconds wait required.")
        time.sleep(e.seconds)
        return await get_user_profile_photo(username)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Отправь мне имя пользователя, и я найду его варианты с фотографиями.')

def find_variants(update: Update, context: CallbackContext) -> None:
    word = update.message.text.strip()
    variants = generate_variants(word)

    for i, variant in enumerate(variants[:50], 1):
        update.message.reply_text(f"{i}: @{variant}")
        photo_path = client.loop.run_until_complete(get_user_profile_photo(variant))
        if photo_path:
            with open(photo_path, 'rb') as photo:
                update.message.reply_photo(photo, caption=f"Фото профиля @{variant}")
        else:
            update.message.reply_text(f"Фото профиля @{variant} не найдено.")

def main() -> None:
    updater = Updater(bot_token)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("find", find_variants))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())