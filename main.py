import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import speech_recognition as sr
import pyttsx3
import random

logging.basicConfig(level=logging.INFO)

EXIT_STICKER_FILE_ID = "CAACAgIAAxkBAAEOec5oJEnpPl_g4bf0eBnsOCVf8AzwEwACGwADXQWCFnr-E0IuatztNgQ"
MENU_HELP = "Помощь"
MENU_EXIT = "Выход"

CITIES = {
    "москва": (55.75, 37.61),
    "санкт-Петербург": (59.93, 30.31),
    "братск": (56.15, 101.63),
    "киев": (50.45, 30.52),
    "минск": (53.90, 27.56),
    "новосибирск": (55.03, 82.92)
}


def get_weather(city):
    city = city.lower().strip()

    cities = {
        "москва": (55.75, 37.61),
        "санкт-петербург": (59.93, 30.31),
        "братск": (56.15, 101.63),
        "киев": (50.45, 30.52),
        "минск": (53.90, 27.56),
        "новосибирск": (55.03, 82.92)
    }

    if city not in cities:
        return {"error": "Город не найден"}

    latitude, longitude = cities[city]

    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        logging.error(f"Ошибка запроса: {err}")
        return {"error": "Ошибка запроса"}


def format_weather(data):
    if "error" in data:
        return data["error"]

    if "current" in data:
        temp = data["current"]["temperature_2m"]
        wind_speed = data["current"]["wind_speed_10m"]

        if temp >= 25:
            reaction = random.choice(WEATHER_REPLIES["hot"])
        elif temp <= 5:
            reaction = random.choice(WEATHER_REPLIES["cold"])
        elif wind_speed > 10:
            reaction = random.choice(WEATHER_REPLIES["windy"])
        else:
            reaction = random.choice(WEATHER_REPLIES["normal"])

        return f"🌍 Погода:\n🌡 Температура: {temp}°C\n💨 Ветер: {wind_speed} м/с\n\n{reaction}"

    return "Не удалось получить данные о погоде, попробуй позже."


WEATHER_REPLIES = {
    "hot": [
        "Жарковато! Пора доставать плавки и искать ближайший бассейн! 🏖",
        "Солнце жжет! Не забудь защитный крем, чтобы не превратиться в картошку-фри. 🌞",
        "Настоящая духота! Может, лучше спрятаться в холодильнике? ❄️"
    ],
    "cold": [
        "Холодно, как в сердце твоего бывшего! 🧊",
        "Минус на улице, плюс к желанию сидеть дома под пледом! 🥶",
        "Где твой теплый чай и толстый свитер? Сейчас самое время! 🍵"
    ],
    "windy": [
        "Ветер такой, что можно бесплатно испытать эффект парашюта! 💨",
        "Пора привязывать шапку, чтобы она не улетела в другой город! 🎩",
        "Хочешь бесплатную укладку? Просто выйди на улицу! 🌪"
    ],
    "normal": [
        "Погода вроде нормальная! Можно спокойно гулять. 😎",
        "Сегодня идеальный день, чтобы не париться о погоде! 😏",
        "Всё спокойно! Даже синоптики не жалуются. 😆"
    ]
}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.lower() == MENU_HELP.lower():
        await update.message.reply_text("Посмотри какая погода сегодня заебатая.")
    elif text == MENU_EXIT:
        await update.message.reply_text("Ну и пошел нахуй!", reply_markup=ReplyKeyboardRemove())
        await update.message.reply_sticker(sticker=EXIT_STICKER_FILE_ID)
    else:
        weather_data = get_weather(text)
        await update.message.reply_text(format_weather(weather_data))


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.voice.get_file()
    file_path = "voice.ogg"
    await file.download_to_drive(file_path)

    os.system(f"ffmpeg -y -i {file_path} -ar 16000 -ac 1 voice.wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile("voice.wav") as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio, language="ru-RU")
        weather_data = get_weather(text)
        await update.message.reply_text(format_weather(weather_data))
    except sr.UnknownValueError:
        await update.message.reply_text("Не удалось распознать речь.")
    except sr.RequestError:
        await update.message.reply_text("Ошибка сервиса распознавания.")

    os.remove("voice.ogg")
    os.remove("voice.wav")


def build_menu_keyboard():
    keyboard = [[MENU_HELP], [MENU_EXIT]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Дарова! Напиши название города или потыкай кнопки.",
                                    reply_markup=build_menu_keyboard())


def main():
    application = Application.builder().token(os.getenv('Telegram_bot_token')).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logging.info("Бот запущен")
    application.run_polling()


if __name__ == '__main__':
    main()
