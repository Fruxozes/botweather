import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()
TELEGRAM_TOKEN = os.getenv('Telegram_bot_token')
API_KEY = os.getenv("API_KEY")

logging.basicConfig(level=logging.INFO)

EXIT_STICKER_FILE_ID = "CAACAgIAAxkBAAEOec5oJEnpPl_g4bf0eBnsOCVf8AzwEwACGwADXQWCFnr-E0IuatztNgQ"
MENU_HELP = "Помощь"
MENU_EXIT = "Выход"

def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        logging.error(f"Ошибка запроса: {err}")
        return None


def format_weather(data):
    if data:
        city = data.get("name", "Неизвестно")
        temp = data["main"]["temp"]
        weather = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        return f"🌍 Город: {city}\n☁️ Погода: {weather}\n🌡 Температура: {temp}°C\n💧 Влажность: {humidity}%\n💨 Ветер: {wind_speed} м/с"
    return "Не удалось получить данные. Проверь API-ключ или название города."


def build_menu_keyboard():
    keyboard = [[MENU_HELP], [MENU_EXIT]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.strip().lower() == MENU_HELP.lower():
        await update.message.reply_text("Тебе уже ничем не помочь блять, посмотри лучше какая погода сегодня заебатая.")
    elif text == MENU_EXIT:
        await update.message.reply_text("Ну и пошел нахуй от сюда!", reply_markup=ReplyKeyboardRemove())
        await update.message.reply_sticker(sticker=EXIT_STICKER_FILE_ID)
    else:
        weather_data = get_weather(text)
        await update.message.reply_text(format_weather(weather_data))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Дарова, посмотри погоду (напиши название города) либо потыкай кнопки.",
                                    reply_markup=build_menu_keyboard())


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    logging.info("Бот запущен")
    application.run_polling()


if __name__ == '__main__':
    main()
