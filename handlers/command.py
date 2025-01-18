import asyncio

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BufferedInputFile, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters.command import Command

from keyboards.keyboard import menu, my_lot_keyboard, add_participant, my_channel, add_my_channel
from loop.send_raffle import send_raffle
from sql import UserDAO, ChannelDAO, RaffleDAO

# роутеры для разделения функций по разным файлам
router = Router()
# надо от него избавиться, но не знаю как
bot = Bot(token=settings.get_token())

# перехватывает команду start
@router.message(Command('start'))
async def send_welcome(message: types.Message, state: FSMContext):
    # информация о пользователе по id
    user = await UserDAO.find_all(telegram_id=message.from_user.id)
    # если пользователь не был зарегестрирован до этого
    if not user:
        # добавление пользователя в базу данных
        await UserDAO.add(telegram_id=message.from_user.id,
                          first_name=message.from_user.first_name,
                          user_name=message.from_user.username,
                          channel=None)
        await bot.send_message(chat_id=message.from_user.id,
                               text="""👋 Приветствуем!
        Наш бот поможет Вам провести розыгрыш на канале.
        Готовы создать новый розыгрыш?""", reply_markup=menu
                               )

    # если все пользователь уже в системе и получен его телефон
    else:
        await bot.send_message(chat_id=message.from_user.id,
                               text="""👋 Приветствуем!
Наш бот поможет Вам провести розыгрыш на канале.
Готовы создать новый розыгрыш?""", reply_markup=menu
                               )


# если текст пользователя содержит /mylot
@router.message(F.text.contains('/mylot'))
async def my_lot(message: types.Message, state: FSMContext):
    # нахождение id розыгрыша
    raffle_id = message.text[6::]
    # сохранения в FSM id
    await state.update_data(id=raffle_id)
    # запрос информации об розырыше через его id
    raffles = await RaffleDAO.find_one_or_none(id=raffle_id)
    # если розыгрыш заканчивает из-за количества пользователей
    try:
        raffle_format = {"id": raffles[0].id,
                         "status": raffles[0].status,
                         "number_participants": raffles[0].number_participants,
                         "number_winners": raffles[0].number_winners,
                         "end": f'Завершение при количестве участников:{raffles[0].max_participants}'}
    # если розыгрыш заканчивает из-за времени
    except:
        raffle_format = {"id": raffles[0].id,
                         "status": raffles[0].status,
                         "number_participants": raffles[0].number_participants,
                         "number_winners": raffles[0].number_winners,
                         "end": f'Время завершения: {raffles[0].time_end}'}
    await bot.send_message(chat_id=message.from_user.id,
                           text=f'Розыгрыш №{raffle_format["id"]}\n'
                                f'Статус: {raffle_format["status"]}\n'
                                f'Количество участников: {raffle_format["number_participants"]}\n'
                                f'Количество победителей: {raffle_format["number_winners"]}'
                                f'{raffle_format["end"]}',
                           reply_markup=my_lot_keyboard(raffle_format["status"]).as_markup()
                           )


# если текст пользователя содержит /delete_channel
@router.message(F.text.contains('/delete_channel'))
async def delete_my_channel(message: types.Message, state: FSMContext):
    # удаление канала
    await ChannelDAO.delete(channel_telegram_id=message.text.split(" ")[1])
    await bot.send_message(chat_id=message.from_user.id,
                           text=f'Канал удален'
                           )


# если текст пользователя содержит /postlot (пользователь хочет отправить розыгрыш куда-то еще)
@router.message(F.text.contains('/postlot'))
async def delete_my_channel(message: types.Message, state: FSMContext):
    # запрос в бд  одного розыграша
    raffle = await RaffleDAO.find_one_or_none(id=message.text[8::])
    await bot.send_message(chat_id=message.from_user.id,
                           text=raffle[0].text_raffle,
                           reply_markup=add_participant(raffle[0].text_button, 0))
    # запрос в бд всех каналов пользователя
    channels = await ChannelDAO.find_all(user_telegram_id=message.from_user.id)
    await bot.send_message(chat_id=message.from_user.id,
                           text=f"🗓 В каком канале публикуем розыгрыш?", reply_markup=add_my_channel(channels, raffle_id=raffle[0].id).as_markup())


