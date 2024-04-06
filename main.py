import asyncio
import logging
import os
import re
from datetime import datetime

import aioschedule as aioschedule
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

with open("bot_token.txt", "r") as f:
    bot = Bot(token=f.read())

dp = Dispatcher()


def get_config(chat_id: int) -> Config:
    logger.info(f"Try to get config for chat with id {chat_id}")
    config_path = f"configs/config_{chat_id}.json"

    if os.path.exists(config_path):
        config = Config.read(config_path)
        logger.info(f"Successfully load config for chat with id {chat_id}")
        return config

    config = Config.from_json({"chat_id": chat_id})
    config.save()
    logger.info(f"Create default config for chat with id {chat_id}")
    return config


async def send_error(message: types.Message, text: str, delete_message: bool = False, **kwargs: dict) -> None:
    if delete_message:
        await message.delete()

    error = await message.answer(text, parse_mode="HTML", **kwargs)
    await asyncio.sleep(5)
    await error.delete()


@dp.message(Command("get_id"))
async def log(message: types.Message) -> None:
    logger.info(f"Chat id: {message.chat.id}")
    logger.info(f"Chat title: {message.chat.title}")
    logger.info(f"Chat type: {message.chat.type}")
    await message.delete()


@dp.message(Command("start"))
async def start(message: types.Message) -> None:
    logger.info(f"Command {message.text} from user {message.from_user.username} ({message.from_user.id}) in chat {message.chat.title} ({message.chat.id})")
    config = get_config(message.chat.id)
    config.is_stopped = False
    config.save()

    await send_error(message, "Бот запущен для этого чата", True)


@dp.message(Command("stop"))
async def stop(message: types.Message) -> None:
    logger.info(f"Command {message.text} from user {message.from_user.username} ({message.from_user.id}) in chat {message.chat.title} ({message.chat.id})")
    config = get_config(message.chat.id)
    config.is_stopped = True
    config.save()

    await send_error(message, "Бот приостановлен для этого чата", True)


@dp.message(Command("info"))
async def info(message: types.Message) -> None:
    logger.info(f"Command {message.text} from user {message.from_user.username} ({message.from_user.id}) in chat {message.chat.title} ({message.chat.id})")
    config = get_config(message.chat.id)

    text = "\n".join([
        f'<b>Состояние</b>: бот {"остановлен" if config.is_stopped else "запущен"}',
        f"<b>Заголовок опроса</b>: {config.title}",
        f'<b>Варианты ответов</b>: {", ".join(config.options)}',
        f"<b>Период отправки</b>: {config.weekday_text()} в {config.time}",
    ])

    await send_error(message, text, True)


@dp.message(Command("poll"))
async def poll(message: types.Message) -> None:
    logger.info(f"Command {message.text} from user {message.from_user.username} ({message.from_user.id}) in chat {message.chat.title} ({message.chat.id})")
    config = get_config(message.chat.id)
    await message.delete()
    await message.answer_poll(question=config.title, options=config.options, is_anonymous=False, allows_multiple_answers=False)


@dp.message(Command("set_title"))
async def set_title(message: types.Message) -> None:
    logger.info(f"Command {message.text} from user {message.from_user.username} ({message.from_user.id}) in chat {message.chat.title} ({message.chat.id})")
    title = message.text.replace("/set_title", "").strip()

    if len(title) > 100:
        return await send_error(message, "Не удалось изменить заголовок опроса, так как он слишком длинный (больше 100 символов)", True)

    config = get_config(message.chat.id)
    config.title = title
    config.save()
    await send_error(message, f'Заголовок опроса успешно изменён на "{title}"', True)


@dp.message(Command("set_options"))
async def set_options(message: types.Message) -> None:
    logger.info(f"Command {message.text} from user {message.from_user.username} ({message.from_user.id}) in chat {message.chat.title} ({message.chat.id})")
    options = re.split(r"\s*,\s*", message.text.replace("/set_options", "").strip())

    if len(options) > 10:
        return await send_error(message, "Не удалось изменить варианты ответов на опрос, так как их больше 10", True)

    config = get_config(message.chat.id)
    config.options = options
    config.save()
    await send_error(message, f'Варианты ответов на опрос успешно изменены на "{", ".join(options)}"', True)


@dp.message(Command("set_weekday"))
async def set_weekday(message: types.Message) -> None:
    logger.info(f"Command {message.text} from user {message.from_user.username} ({message.from_user.id}) in chat {message.chat.title} ({message.chat.id})")
    weekday = message.text.replace("/set_weekday", "").strip()

    weekdays = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]

    if weekday not in weekdays:
        return await send_error(message, f'Не удалось изменить день отправки опроса, так как он введён некорректно ("{weekday}")', True)

    config = get_config(message.chat.id)
    config.weekday = weekdays.index(weekday)
    config.save()
    await send_error(message, f"Дата отправки опроса успешно изменена на {weekday}", True)


@dp.message(Command("set_time"))
async def set_time(message: types.Message) -> None:
    logger.info(f"Command {message.text} from user {message.from_user.username} ({message.from_user.id}) in chat {message.chat.title} ({message.chat.id})")
    time = message.text.replace("/set_time", "").strip()

    if not re.fullmatch(r"(\d|[01]\d|2[0123]):00", time):
        return await send_error(message, f'Не удалось изменить время отправки опроса, так как оно введено некорректно ("{time}")', True)

    config = get_config(message.chat.id)
    config.time = time
    config.save()
    await send_error(message, f"Время отправки опроса успешно изменено на {time}", True)


async def send_polls(time: str) -> None:
    today = datetime.now()

    for config_path in os.listdir("configs"):
        config = Config.read(os.path.join("configs", config_path))

        if config.is_stopped or today.weekday() != config.weekday or time != config.time:
            continue

        await bot.send_poll(chat_id=config.chat_id, question=config.title, options=config.options, is_anonymous=False, allows_multiple_answers=False)


async def scheduler() -> None:
    for hour in range(24):
        time = f"{hour:02}:00"
        aioschedule.every().day.at(time).do(send_polls, time)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def run_scheduler() -> None:
    asyncio.create_task(scheduler())


async def main() -> None:
    loop = asyncio.get_event_loop()
    loop.create_task(run_scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
