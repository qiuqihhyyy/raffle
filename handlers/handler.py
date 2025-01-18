from datetime import time, datetime

from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION, KICKED, LEFT, RESTRICTED, MEMBER, ADMINISTRATOR, \
    CREATOR, IS_NOT_MEMBER
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from aiogram.types import ChatMemberUpdated

from config import settings
from aiogram import Bot, types, F, Router

from lexicon.lexicon_message import LEXICON
from sql import UserDAO, ChannelDAO, RaffleDAO
from keyboards.keyboard import add_channel_keyboard, names_channel, various_engage, not_subscription, save, my_channel, \
    publish_keyboard, need_raffle, button_raffle, save_raffle, my_lot_keyboard

# роутеры для разделения функций по разным файлам
router = Router()
# надо от него избавиться, но не знаю как
bot = Bot(token=settings.get_token())


# FSM состояния для создания розыгрышей
class AddRaffle(StatesGroup):
    text_raffle = State()
    text_button = State()
    channels_subscribe = State()
    number_winners = State()
    publish_time = State()
    end_time = State()
    max_participant = State()


# FSM состояние для изменения условий окончания розыгрыша
class AdditionalRaffle(StatesGroup):
    change_end_time = State()
    change_max_participant = State()


# FSM состояние для добавления каналов
class AddChannel(StatesGroup):
    add_channel = State()


# функция главного меню
@router.message(F.text == "Создать розыгрыш ❇️")
async def create_raffle(message: types.Message, state: FSMContext):
    # проверка есть ли у пользователя каналы в боте
    channel = await ChannelDAO.find_all(user_telegram_id=message.from_user.id)
    # если нет, то просьба из добавить
    if not channel:
        await bot.send_message(chat_id=message.from_user.id,
                               text=LEXICON["lack_channels"])
    # если есть, то начало создания розыгрыша
    else:
        await bot.send_message(chat_id=message.from_user.id,
                               text=LEXICON["start_message"])
        # включение FSM состояния для ввода текста розыгрыша
        await state.set_state(AddRaffle.text_raffle)


# перехватывает текст розыгрыша
@router.message(AddRaffle.text_raffle)
async def add_text_raffle(message: types.Message, state: FSMContext):
    # проверка на не является ли текст одной из команд меню
    if await check_message(message, state):
        return None
    # сохранения текста для розыгрыша
    await state.update_data(text_raffle=message.text)

    await bot.send_message(chat_id=message.from_user.id,
                           text="✅ Текст добавлен")
    await bot.send_message(chat_id=message.from_user.id,
                           text=LEXICON["dd_text_button"],
                           reply_markup=various_engage)
    # включение FSM состояния для записи текста кнопки участия
    await state.set_state(AddRaffle.text_button)


# перехватывает текст кнопки
@router.message(AddRaffle.text_button)
async def add_text_button(message: types.Message, state: FSMContext):
    # проверка на не является ли текст одной из команд меню
    if await check_message(message, state):
        return None
    # сохранения текста для кнопки розыгрыша
    await state.update_data(text_button=message.text)

    await bot.send_message(chat_id=message.from_user.id,
                           text="✅ Текст кнопки сохранен")
    await bot.send_message(chat_id=message.from_user.id,
                           text=LEXICON['add_channel_raffle'],
                           reply_markup=not_subscription)
    # включение FSM состояния для записи каналов для подписки
    await state.set_state(AddRaffle.channels_subscribe)


# перехватывает названия каналов на которые надо подписаться
@router.message(AddRaffle.channels_subscribe)
async def add_channels_subscribe(message: types.Message, state: FSMContext):
    # проверка на не является ли текст одной из команд меню
    if await check_message(message, state):
        return None

    data = await state.get_data()
    # колхоз, но все же первая конструкция try except нужно для обозначени channels_subscribe в первый раз в except,
    # try для 2 и тд
    # вторая конструкция нужна для обработки неправильного отправленных сообщений(перессылка с групп и тд)
    try:
        # сохранения ид каналов для подписки функционал проверки подписки не сделан
        await state.update_data(channels_subscribe=f'{data["channels_subscribe"]} {message.forward_origin.chat.id}')
    except KeyError:
        try:
            await state.update_data(channels_subscribe=f'{message.forward_origin.chat.id}')
        except AttributeError:
            await bot.send_message(chat_id=message.from_user.id,
                                   text="❌ Неверный формат, попробуйте еще раз.")
            return None
    await bot.send_message(chat_id=message.from_user.id,
                           text=LEXICON['true_add_channel'],
                           reply_markup=save,
                           parse_mode='HTML')


# перехватывает число победителей
@router.message(AddRaffle.number_winners)
async def add_number_winners(message: types.Message, state: FSMContext):
    # проверка на не является ли текст одной из команд меню
    if await check_message(message, state):
        return None
    # если формат верный (пользователь ввел число)
    try:
        # сохранения количества победителей
        await state.update_data(number_winners=int(message.text))
        await bot.send_message(chat_id=message.from_user.id,
                                   text=f"✅ Количество победителей сохранено: {message.text}")
        # поиск каналов пользователя
        channels = await ChannelDAO.find_all(user_telegram_id=message.from_user.id)
        await bot.send_message(chat_id=message.from_user.id,
                               text=f"🗓 В каком канале публикуем розыгрыш?",
                               reply_markup=my_channel(channels).as_markup())
    # если пользователь не число
    except:
        await bot.send_message(chat_id=message.from_user.id,
                               text="❌ Неверный формат, попробуйте еще раз.")


# перехватывает время оправления розыгрыша
@router.message(AddRaffle.publish_time)
async def add_time_publish(message: types.Message, state: FSMContext):
    print("f")
    # проверка на не является ли текст одной из команд меню
    if await check_message(message, state):
        return None
    # проверка на введение даты и времени в правильном формате
    try:
        # сохранения времени публикации
        datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        await state.update_data(publish_time=message.text)
        await bot.send_message(chat_id=message.from_user.id,
                               text="✅ Время публикации выбрано")
        await bot.send_message(chat_id=message.from_user.id,
                               text="🗓 Как завершить розыгрыш?", reply_markup=need_raffle)
    # работает если время неправильное
    except:
        await bot.send_message(chat_id=message.from_user.id,
                               text="❌ Неверный формат, попробуйте еще раз.")


# перехватывает время окончания розыгрыша, если есть
@router.message(AddRaffle.end_time)
async def add_time_end(message: types.Message, state: FSMContext):
    # проверка на не является ли текст одной из команд меню
    if await check_message(message, state):
        return None
    # проверка на введение даты и времени в правильном формате
    try:
        # сохранения времени окончания розыгрыша
        datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        await state.update_data(time_end=message.text)
        await bot.send_message(chat_id=message.from_user.id,
                               text="✅ Время для подведения результатов сохранено")
        # отправление данных введенных пользователем
        data = await state.get_data()
        await bot.send_message(chat_id=message.from_user.id,
                               text=f"{data['text_raffle']}",
                               reply_markup=button_raffle(data["text_button"]).as_markup())
        await bot.send_message(chat_id=message.from_user.id,
                               text=f"🧮 Внимательно перепроверьте розыгрыш\n"
                                    f"Розыгрыш завершится {message.text}\n"
                                    f"Количество победителей: {data['number_winners']}",
                               reply_markup=save_raffle)
    # работает если время неправильное
    except:
        await bot.send_message(chat_id=message.from_user.id,
                               text="❌ Неверный формат, попробуйте еще раз.")


# перехватывает время окончания розыгрыша, если пользователь хочет его изменить
@router.message(AdditionalRaffle.change_end_time)
async def change_time_end(message: types.Message, state: FSMContext):
    # проверка на не является ли текст одной из команд меню
    if await check_message(message, state):
        return None
    # проверка на введение даты и времени в правильном формате
    try:
        datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        data = await state.get_data()
        # изменение времени окончиня розыгрыша
        await RaffleDAO.update(id=data["id"], time_end=message.text)
        await bot.send_message(chat_id=message.from_user.id,
                               text="✅ Время для подведения результатов изменено")
        # удаление FSM состояния и данных в них
        await state.clear()
    except:
        await bot.send_message(chat_id=message.from_user.id,
                               text="❌ Неверный формат, попробуйте еще раз.")


# перехватывает максимальное количество участников, если есть
@router.message(AddRaffle.max_participant)
async def add_max_participant(message: types.Message, state: FSMContext):
    # проверка на не является ли текст одной из команд меню
    if await check_message(message, state):
        return None
    # проверка на введение числа
    try:
        # сохранения максимального числа участников
        await state.update_data(max_participant=int(message.text))
        await bot.send_message(chat_id=message.from_user.id,
                               text=f"✅ Количество участников для подведения результатов сохранено: {message.text}")
        # отправление данных введенных пользователем
        data = await state.get_data()
        await bot.send_message(chat_id=message.from_user.id,
                               text=f"{data['text_raffle']}", reply_markup=button_raffle(data["text_button"]).as_markup())
        await bot.send_message(chat_id=message.from_user.id,
                               text=f"🧮 Внимательно перепроверьте розыгрыш\n"
                                    f"Розыгрыш завершится, когда количество участников станет равно {message.text}\n"
                                    f"Количество победителей: {data['number_winners']}",
                               reply_markup=save_raffle)
    # работает если время неправильное
    except:
        await bot.send_message(chat_id=message.from_user.id,
                               text="❌ Неверный формат, попробуйте еще раз.")


# перехватывает изменения максимальное количество участников, если есть
@router.message(AdditionalRaffle.change_max_participant)
async def change_max_participant(message: types.Message, state: FSMContext):
    # проверка на не является ли текст одной из команд меню
    if await check_message(message, state):
        return None
    # проверка на введение числа
    try:
        # изменения числа участников
        data = await state.get_data()
        await RaffleDAO.update(id=data["id"], max_participants=int(message.text))
        await bot.send_message(chat_id=message.from_user.id,
                               text=f"✅ Количество участников для подведения результатов изменено: {message.text}")
        # удаление FSM состояния и данных в них
        await state.clear()
    # работает если введено не число
    except:
        await bot.send_message(chat_id=message.from_user.id,
                               text="❌ Неверный формат, попробуйте еще раз.")


# перехватывает команду главного меню
@router.message(F.text == "Мои каналы 📢")
async def add_channel_def(message: types.Message, state: FSMContext):
    # проверка есть ли у пользователя добавленные каналы
    channel = await ChannelDAO.find_all(user_telegram_id=message.from_user.id)
    if not channel:
        await bot.send_message(chat_id=message.from_user.id,
                               text="ℹ️ Добавленные вами каналы:", reply_markup=add_channel_keyboard)
    # если есть
    else:
        # преобразование результата из бд в список
        name_channel = []
        for i in channel:
            name_channel.append(i.name)
        await bot.send_message(chat_id=message.from_user.id,
                               text="ℹ️ Добавленные вами каналы:",
                               reply_markup=names_channel(name_channel).as_markup())


# перехватывает команду главного меню
@router.message(F.text == "Мои розыгрыши 🎁")
async def my_lot_menu(message: types.Message, state: FSMContext):
    # запрос в бд о розыгрышей пользователя
    raffles = await RaffleDAO.find_all(telegram_id=message.from_user.id)
    # преобразование результата из бд в список
    raffles_list = []
    for raffle in raffles:
        raffles_list.append(f'/mylot{raffle.id} {raffle.text_raffle}')
    text_lot = '\n'.join(raffles_list)

    await bot.send_message(chat_id=message.from_user.id,
                           text=f"ℹ️ Добавленные вами розыгрыши:\n{text_lot}")


# перехватывает команду главного меню
@router.message(F.text == "Техническая поддержка ⚙️")
async def support(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id,
                           text=LEXICON["support"])


# перехватывает команду главного меню
@router.message(F.text == "Поддержать Бота ⭐️️")
async def stair(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id,
                           text=LEXICON['stair'])


# если бот был добавлен в канал
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def bot_added(event: ChatMemberUpdated, bot: Bot, state: FSMContext):
    # добавление канала в бд
    await ChannelDAO.add(
        user_telegram_id=event.from_user.id,
        name=event.chat.title,
        channel_telegram_id=event.chat.id
    )
    await bot.send_message(chat_id=event.from_user.id, text=f"""
    ✅ Канал {event.chat.title} добавлен, можно переходить к созданию розыгрыша!\n
Чтобы создать новый розыгрыш, введите команду /new_lot""")


# FSM состояние добавления канала в бд
@router.message(AddChannel.add_channel)
async def add_channel(message: types.Message, state: FSMContext):
    # проверка на не является ли текст одной из команд меню
    if await check_message(message, state):
        return None
    # нужно для проверки статуса пользователя группы
    user_status = await bot.get_chat_member(chat_id=message.forward_origin.chat.id, user_id=message.from_user.id)
    try:
        # если пользователь создатель или админ
        if user_status.status == "creator" or user_status.status == "administrator":
            # добавить канал в бд
            await ChannelDAO.add(user_telegram_id=message.from_user.id,
                                 name=message.forward_origin.chat.title,
                                 channel_telegram_id=message.forward_origin.chat.id)
            await bot.send_message(chat_id=message.from_user.id, text=f"""✅ Канал {message.forward_origin.chat.title} добавлен, 
            можно переходить к созданию розыгрыша!
        Чтобы создать новый розыгрыш, введите команду /new_lot
                """)
            await state.clear()
        else:
            await bot.send_message(chat_id=message.from_user.id, text="Вы не админ и не создатель")
    # если канал не добавлен
    except:
        await bot.send_message(chat_id=message.from_user.id,
                               text="не получается проверить являетесь ли администратором канала")


# перехватывает событие удаление бота, его бан, уменьшение полномочий
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=
        (+RESTRICTED | ADMINISTRATOR | CREATOR)
        >>
        (KICKED | LEFT | -RESTRICTED | MEMBER)
    )
)
async def bot_delete(event: ChatMemberUpdated, bot: Bot, state: FSMContext):
    # удаление бота из бд
    await ChannelDAO.delete(
        user_telegram_id=event.from_user.id,
        name=event.chat.title,
        channel_telegram_id=event.chat.id
    )
    await bot.send_message(chat_id=event.from_user.id, text=f"""
    ❌ Канал {event.chat.title} удален""")


# перехватывает событие добавление бота в группу
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=
        (KICKED | LEFT | -RESTRICTED | MEMBER)
        >>
        (+RESTRICTED | ADMINISTRATOR | CREATOR)
    )
)
async def bot_delete(event: ChatMemberUpdated, bot: Bot, state: FSMContext):
    # добавление канала в бд
    await ChannelDAO.add(
        user_telegram_id=event.from_user.id,
        name=event.chat.title,
        channel_telegram_id=event.chat.id
    )
    await bot.send_message(chat_id=event.from_user.id, text=f"""
        ✅ Канал {event.chat.title} добавлен, можно переходить к созданию розыгрыша!\n
    Чтобы создать новый розыгрыш, введите команду /new_lot""")


# перехватывает событие бот перестал быть админом
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=
        (ADMINISTRATOR)
        >>
        (MEMBER)
    )
)
async def bot_added(event: ChatMemberUpdated, bot: Bot, state: FSMContext):
    await bot.send_message(chat_id=event.from_user.id, text=f"""
    В Канале {event.chat.title} бот не может отправлять сообщения так как не является администратором""")


# функция для фильтрации команд и простого текста
async def check_message(message, state):
    # если текст это команда
    if message.text == "Создать розыгрыш ❇️":
        await bot.send_message(chat_id=message.from_user.id, text="Действие отменено")
        # удаление FSM состояний
        await state.clear()
        # исполнение самой команды
        await create_raffle(message, state)
        # функция применяется в конструкции if если текст является командой, дальше исполняется только команда
        return True
    elif message.text == "Мои розыгрыши 🎁":
        await bot.send_message(chat_id=message.from_user.id, text="Действие отменено")
        await state.clear()
        await my_lot_menu(message, state)
        return True
    elif message.text == "Мои каналы 📢":
        await bot.send_message(chat_id=message.from_user.id, text="Действие отменено")
        await state.clear()
        await add_channel_def(message, state)
        return True
    elif message.text == "Техническая поддержка ⚙️":
        await bot.send_message(chat_id=message.from_user.id, text="Действие отменено")
        await state.clear()
        await support(message, state)
        return True
    elif message.text == "Поддержать Бота ⭐️️":
        await bot.send_message(chat_id=message.from_user.id, text="Действие отменено")
        await state.clear()
        await stair(message, state)
        return True
    # если текст не соответствует ни одной команде
    else:
        return False