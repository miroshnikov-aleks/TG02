import logging
import os
import requests
import asyncio # Добавили импорт asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ContentType
from googletrans import Translator
from config import API_TOKEN, WEATHER_API_KEY

CITY_NAME = 'Брянск'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаём экземпляры Bot и Dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# Словарь для перевода описаний погоды
weather_descriptions = {
    "clear sky": "ясное небо",
    "few clouds": "малооблачно",
    "scattered clouds": "рассеянные облака",
    "broken clouds": "облачность с прояснениями",
    "overcast clouds": "пасмурно",
    "light rain": "небольшой дождь",
    "moderate rain": "умеренный дождь",
    "heavy intensity rain": "сильный дождь",
    "thunderstorm": "гроза",
    "snow": "снег",
    # Добавьте другие описания по мере необходимости
}

# Создаем директорию для сохранения изображений, если она не существует
if not os.path.exists('img'):
    os.makedirs('img')

# Инициализация переводчика
translator = Translator()

# Команда /start
@router.message(Command(commands=['start']))
async def send_welcome(message: types.Message):
    logging.info("Получена команда /start")
    await message.answer(
        "Привет! Я бот, который может предоставить прогноз погоды и перевести текст на английский. Напиши /weather, чтобы получить прогноз, или отправь текст для перевода.",
        parse_mode="HTML"
    )

# Команда /help
@router.message(Command(commands=['help']))
async def send_help(message: types.Message):
    logging.info("Получена команда /help")
    await message.answer(
        "Я могу помочь тебе с прогнозом погоды и переводом текста.\n\nКоманды:\n/start - Начать работу с ботом\n/help - Получить справку\n/weather - Получить прогноз погоды\n/sendvoice - Отправить голосовое сообщение",
        parse_mode="HTML"
    )

# Команда /weather
@router.message(Command(commands=['weather']))
async def get_weather(message: types.Message):
    logging.info("Получена команда /weather")
    try:
        response = requests.get(
            f'http://api.openweathermap.org/data/2.5/weather?q={CITY_NAME}&appid={WEATHER_API_KEY}&units=metric',
            timeout=10
        )
        response.raise_for_status() # Вызываем ошибку для плохих кодов состояния
        data = response.json()
        temperature = data['main']['temp']
        weather_description = data['weather'][0]['description']
        translated_description = weather_descriptions.get(weather_description, weather_description)
        weather_info = f"Погода в {CITY_NAME}е:\nТемпература: {temperature}°C\nОписание: {translated_description.capitalize()}"
        await message.answer(weather_info, parse_mode="HTML")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при получении данных о погоде: {e}")
        await message.answer("Не удалось получить данные о погоде. Попробуйте позже.")

# Команда /sendvoice
@router.message(Command(commands=['sendvoice']))
async def send_voice_message(message: types.Message):
    logging.info("Получена команда /sendvoice")
    try:
        # Путь к голосовому файлу
        voice_path = 'voice.ogg'
        if not os.path.exists(voice_path):
            raise FileNotFoundError("Голосовой файл не найден.")

        # Отправляем голосовое сообщение
        voice = types.FSInputFile(voice_path)
        await message.answer_voice(voice=voice)
        logging.info("Голосовое сообщение отправлено")
    except Exception as e:
        logging.error(f"Ошибка при отправке голосового сообщения: {e}")
        await message.answer("Не удалось отправить голосовое сообщение. Попробуйте позже.")

# Обработка фотографий
@router.message(lambda message: message.content_type == ContentType.PHOTO)
async def handle_photo(message: types.Message):
    logging.info("Получено фото")
    try:
        # Получаем информацию о фото
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file = await bot.download_file(file_info.file_path)

        # Сохраняем фото в папку img
        file_path = os.path.join('img', f'{photo.file_id}.jpg')
        with open(file_path, 'wb') as f:
            f.write(file.read())

        logging.info(f"Фото сохранено в {file_path}")
        await message.answer("Фото сохранено!")
    except Exception as e:
        logging.error(f"Ошибка при сохранении фото: {e}")
        await message.answer("Не удалось сохранить фото. Попробуйте позже.")

# Обработка текстовых сообщений для перевода
@router.message(lambda message: message.text and not message.text.startswith('/'))
async def translate_text(message: types.Message):
    logging.info("Получен текст для перевода")
    try:
        # Добавили await перед вызовом translator.translate
        translation = await translator.translate(message.text, dest='en')
        translated_text = translation.text
        await message.answer(f"Перевод:\n{translated_text}")
    except Exception as e:
        logging.error(f"Ошибка при переводе текста: {e}")
        await message.answer("Не удалось перевести текст. Попробуйте позже.")

# Добавление маршрутизатора в диспетчер
dp.include_router(router)

# Запуск бота
async def main():
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске поллинга: {e}")

if __name__ == '__main__':
    asyncio.run(main())