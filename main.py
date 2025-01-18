import asyncio
import time
from datetime import datetime, timedelta

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm import storage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
import logging

from callbacks import callback
from config import settings
from aiogram import Bot, Dispatcher, types, F

from handlers import command, handler
from loop.send_raffle import send_raffle, start_end_raffle, choose_winner
from sql import UserDAO, ChannelDAO

# Инициализируем логгер
logger = logging.getLogger(__name__)


# # функция цикличного повторения
# async def periodic_operation():
#     # проверяет есть ли розыгрыши которые надо закончить или начать
#     await start_end_raffle()


# функция цикличного повторения
def repeat(coro, loop):
    # я не знаю для чего это
    asyncio.ensure_future(coro(), loop=loop)
    # выполнение coro раз в минуту бесконечно долго
    loop.call_later(60, repeat, coro, loop)


# главная функция
async def main():
    bot = Bot(token=settings.get_token())
    await bot.send_message(chat_id=-4725789557, text="ff")
    # установление логов
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    # FSM состояния
    storage = MemoryStorage()
    bot = Bot(token=settings.get_token())
    dp = Dispatcher(storage=storage)

    # подключения роутеров
    dp.include_routers(
        command.router,
        # admin.router,
        handler.router,
        callback.router

    )
    # запуск async постоянной функции
    loop = asyncio.get_event_loop()
    # постоянное повторение start_end_raffle раз в минуту
    loop.call_later(60, repeat, start_end_raffle, loop)
    # удаления веб хуков
    await bot.delete_webhook(drop_pending_updates=True)
    # начало работы бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
