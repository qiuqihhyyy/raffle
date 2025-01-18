from datetime import datetime, timedelta

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BufferedInputFile, InputMediaPhoto, ChatMemberUpdated
from config import settings
from aiogram import Bot, Dispatcher, types, F, Router

from keyboards.keyboard import cancel, not_subscription, publish_keyboard, Yes, need_raffle, need_raffle_change, \
    menu_channel, publishg, confirmation_r
from handlers.handler import AddRaffle, AdditionalRaffle, AddChannel
from lexicon.lexicon_message import LEXICON
from loop.send_raffle import send_raffle, choose_winner
from sql import ChannelDAO, RaffleDAO, ParticipantDAO

# роутеры для разделения функций по разным файлам
router = Router()
# надо от него избавиться, но не знаю как
bot = Bot(token=settings.get_token())


# нажатие инлайн кнопки добавления канала
@router.callback_query(F.data.in_(
    ['add_channel']
))
async def callback_admin(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(chat_id=callback.from_user.id, text=LEXICON['instruction'],
                           reply_markup=cancel,
                           parse_mode='HTML')
    # включение FSM состояния для добавления каналов
    await state.set_state(AddChannel.add_channel)


# нажатие инлайн кнопки варинатов кнопки розыгрыша
@router.callback_query(F.data.in_(
    ['engage', "engage!", "take_part"]
))
async def callback_engage(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "engage":
        await state.update_data(text_button="Участвую")
    elif callback.data == "engage!":
        await state.update_data(text_button="Участвую!")
    elif callback.data == "take_part":
        await state.update_data(text_button="Принять участи")
    await bot.send_message(chat_id=callback.from_user.id,
                           text="✅ Текст кнопки сохранен")
    await bot.send_message(chat_id=callback.from_user.id,
                           text=LEXICON['instruction_add_channel'],
                           reply_markup=not_subscription)
    # включение FSM состояния для добавления каналов
    await state.set_state(AddRaffle.channels_subscribe)


# нажатие инлайн кнопки достаточно каналов
@router.callback_query(F.data.in_(
    ["enough_channel"]
))
async def callback_enough(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(chat_id=callback.from_user.id, text="✅ Сохранено")
    await bot.send_message(chat_id=callback.from_user.id, text="🧮 Сколько победителей выбрать боту?")
    # включение FSM состояния для выбор количества победителей
    await state.set_state(AddRaffle.number_winners)


# нажатие инлайн кнопки куда отправлять розыгрыш
@router.callback_query(F.data.contains("name_channel"))
async def name_channel(callback: types.CallbackQuery, state: FSMContext):
    # сохранения
    await state.update_data(channel_send=f'{callback.data.split(" ")[1]}')
    await bot.send_message(chat_id=callback.from_user.id, text='⏰ Когда нужно опубликовать розыгрыш?',
                           reply_markup=publish_keyboard)

@router.callback_query(F.data.contains("add_channel"))
async def add_name_channel(callback: types.CallbackQuery, state: FSMContext):
    #await state.update_data(channel_send=f'{callback.data.split(" ")[1]}')
    data = callback.data.split(",")
    raffle = await RaffleDAO.find_one_or_none(id=data[-1])
    message = await bot.send_message(chat_id=callback.from_user.id, text=f'ℹ️ Публикуем в канал - {data[2]}',
                           reply_markup=publishg)
    await state.update_data(add_pubkish_channel=raffle[0].id,
                            add_channel=data[1],
                            message_id=message.message_id
                            )


@router.callback_query(F.data.in_(
    ["publish", "no_publish"]
))
async def publish(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if callback.data == "publish":

        raffle = await RaffleDAO.find_one_or_none(id=data["add_pubkish_channel"])
        await RaffleDAO.update(id=data["add_pubkish_channel"],
                               pablish_channal=f'{raffle[0].pablish_channal} {data["add_channel"]}')
        if raffle[0].time_start == '0' or raffle[0].start_time < datetime.now().strftime("%d.%m.%Y %H:%M"):
            await send_raffle(text=raffle[0].text_raffle, text_button=raffle[0].text_button, raffle_id=raffle[0].id,
                              chat_ids=data["add_channel"])
    else:
        await bot.delete_message(chat_id=callback.from_user.id,message_id=data['message_id'])

@router.callback_query(F.data.contains("name_my_channel"))
async def name_channel(callback: types.CallbackQuery, state: FSMContext):
    channel_telegram_id = await ChannelDAO.find_one_or_none(name=f'{callback.data[16::]}',
                                                            user_telegram_id=callback.from_user.id)
    await state.update_data(channel_update_delete=channel_telegram_id[0].channel_telegram_id)
    await bot.send_message(chat_id=callback.from_user.id, text='📢 Меню канала:',
                           reply_markup=menu_channel)

@router.callback_query(F.data.in_(
    ["delete_channel", "cancel_my_channel", "update_name"]
))
async def publish(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if callback.data == "delete_channel":

        await bot.send_message(chat_id=callback.from_user.id, text='⚠️ Чтобы удалить канал из бота, введите команду:\n'
                                                                   f'/delete_channel {data["channel_update_delete"]}')
    elif callback.data == "cancel_my_channel":
        await state.clear()
        await bot.send_message(chat_id=callback.from_user.id, text='Действие отменено')
    elif callback.data == "update_name":
        #bot.get_chat_member(chat_id=-1002457442445, user_id=callback.from_user.id)
        channel = await ChannelDAO.find_one_or_none(channel_telegram_id=data["channel_update_delete"])
        channel_check = await bot.get_chat(chat_id=data["channel_update_delete"])
        if channel[0].name == channel_check.title:
            await bot.send_message(chat_id=callback.from_user.id, text='Имя не менялось')
        else:
            await ChannelDAO.update(id=channel[0].id, name=channel_check.title)
            await bot.send_message(chat_id=callback.from_user.id, text=f'Имя изменено на {channel_check.title}')



@router.callback_query(F.data.in_(
    ["right_now", "choose_time"]
))
async def publish(callback: types.CallbackQuery, state: FSMContext):

    if callback.data == "right_now":
        await state.update_data(publish_time=0)
        await bot.send_message(chat_id=callback.from_user.id,
                               text="✅ Время публикации выбрано")
        await bot.send_message(chat_id=callback.from_user.id,
                               text="🗓 Как завершить розыгрыш?", reply_markup=need_raffle)
    else:
        await state.set_state(AddRaffle.publish_time)
        await bot.send_message(chat_id=callback.from_user.id,
                               text="⏰ Когда нужно опубликовать розыгрыш? (Укажите время в формате дд.мм.гг чч:мм)\n\n"
                                    "Бот живет по времени (GMT+3) Москва, Россия")

        await bot.send_message(chat_id=callback.from_user.id,
                               text=f'Примеры\n\n'
                                    f'`{(datetime.now() + timedelta(minutes=10)).strftime("%d.%m.%Y %H:%M")}` - 10 минут\n'
                                    f'`{(datetime.now() + timedelta(hours=1)).strftime("%d.%m.%Y %H:%M")}` - 1 час\n'
                                    f'`{(datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y %H:%M")}` - 1 день\n'
                                    f'`{(datetime.now() + timedelta(weeks=1)).strftime("%d.%m.%Y %H:%M")}` - 1 неделя\n',
                               parse_mode="MARKDOWN"
                               )
        await state.set_state(AddRaffle.publish_time)


@router.callback_query(F.data.contains("add_participant"))
async def add_participant_callback(callback: types.CallbackQuery, state: FSMContext):
    check = await ParticipantDAO.find_one_or_none(post_id=callback.data.split(" ")[1],
                             participant_telegram_id=callback.from_user.id)
    if not check:
        await ParticipantDAO.add(post_id=callback.data.split(" ")[1],
                                 participant_telegram_id=callback.from_user.id,
                                 participant_name=callback.from_user.first_name,
                                 participant_user_name=callback.from_user.username,
                                 )

        raffle = await RaffleDAO.find_all(id=callback.data.split(" ")[1])
        await RaffleDAO.update(id=callback.data.split(" ")[1],
                               number_participants=raffle[0].number_participants + 1
                               )
        try:
            if raffle[0].number_participants + 1 >= raffle[0].max_participants:
                await choose_winner(raffle_id=callback.data.split(" ")[1])
        except:
            pass


    # await bot.edit_message(
    #     chat_id=callback.message.chat.id,
    #     message_id=callback.message.message_id,
    #
    # )
    # в изначальном боте показывается сколько учасников в инлайн кнопке я этого делать не буду
    # может сделают позже

@router.callback_query(F.data.in_(
    ["time", "participant"]
))
async def publish(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "time":
        await state.set_state(AddRaffle.end_time)
        await bot.send_message(chat_id=callback.from_user.id,
                               text="🏁 Когда нужно определить победителя? (Укажите время в формате дд.мм.гг чч:мм)\n\n"""
                                    "Бот живет по времени (GMT+3) Москва, Россия")

        await bot.send_message(chat_id=callback.from_user.id,
                               text=f'Примеры\n\n'
                                    f'`{(datetime.now() + timedelta(minutes=10)).strftime("%d.%m.%Y %H:%M")}` - 10 минут\n'
                                    f'`{(datetime.now() + timedelta(hours=1)).strftime("%d.%m.%Y %H:%M")}` - 1 час\n'
                                    f'`{(datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y %H:%M")}` - 1 день\n'
                                    f'`{(datetime.now() + timedelta(weeks=1)).strftime("%d.%m.%Y %H:%M")}` - 1 неделя\n',
                               parse_mode="MARKDOWN"
                               )

    else:

        await state.set_state(AddRaffle.max_participant)
        await bot.send_message(chat_id=callback.from_user.id,
                               text="🏁 Укажите количество участников для проведения розыгрыша:\n\n"
                                    "❗️ Обратите внимание, участник - тот, кто поучаствовал в конкурсе, "
                                    "выбор будет не по количеству подписчиков канала,"
                                    " а именно по количеству участников (кто нажал на кнопку в конкурсе)")

@router.callback_query(F.data.in_(
    ["change_time", "change_participant", "change_cance"]
))
async def publish(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "change_time":

        await state.set_state(AdditionalRaffle.change_end_time)
        await bot.send_message(chat_id=callback.from_user.id,
                               text="🏁 Когда нужно определить победителя? (Укажите время в формате дд.мм.гг чч:мм)\n\n"""
                                    "Бот живет по времени (GMT+3) Москва, Россия")

        await bot.send_message(chat_id=callback.from_user.id,
                               text=f'Примеры\n\n'
                                    f'`{(datetime.now() + timedelta(minutes=10)).strftime("%d.%m.%Y %H:%M")}` - 10 минут\n'
                                    f'`{(datetime.now() + timedelta(hours=1)).strftime("%d.%m.%Y %H:%M")}` - 1 час\n'
                                    f'`{(datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y %H:%M")}` - 1 день\n'
                                    f'`{(datetime.now() + timedelta(weeks=1)).strftime("%d.%m.%Y %H:%M")}` - 1 неделя\n',
                               parse_mode="MARKDOWN"
                               )

    elif callback.data == "change_participant":

        await state.set_state(AdditionalRaffle.change_max_participant)
        await bot.send_message(chat_id=callback.from_user.id,
                               text="🏁 Укажите количество участников для проведения розыгрыша:\n\n"
                                    "❗️ Обратите внимание, участник - тот, кто поучаствовал в конкурсе, "
                                    "выбор будет не по количеству подписчиков канала,"
                                    " а именно по количеству участников (кто нажал на кнопку в конкурсе)")
    else:
        await bot.send_message(chat_id=callback.from_user.id,
                               text="✅ Действие отменено)")


@router.callback_query(F.data.in_(
    ["save", "cancel", "Yes"]
))
async def save_raffle(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "save":
        data = await state.get_data()

        # потом исправить это убожество
        try:
            data = await state.get_data()
            await RaffleDAO.add(text_raffle=data['text_raffle'],
                                text_button=data['text_button'],
                                telegram_id=callback.from_user.id,
                                channel_for_subscription=data['channels_subscribe'],
                                number_winners=data['number_winners'],
                                pablish_channal=data['channel_send'],
                                number_participants=0,
                                max_participants=data['max_participant'],
                                time_start=data['publish_time'],
                                status='create')
            raffle = await RaffleDAO.find_one_or_none(text_raffle=data['text_raffle'],
                                                     text_button=data['text_button'],
                                                     telegram_id=callback.from_user.id,
                                                     channel_for_subscription=data['channels_subscribe'],
                                                     number_winners=data['number_winners'],
                                                     time_start=data['publish_time'],
                                                     status='create')
        except:
            await RaffleDAO.add(text_raffle=data['text_raffle'],
                                text_button=data['text_button'],
                                telegram_id=callback.from_user.id,
                                channel_for_subscription=data['channels_subscribe'],
                                number_winners=data['number_winners'],
                                pablish_channal=data['channel_send'],
                                number_participants=0,
                                time_start=data['publish_time'],
                                time_end=data['time_end'],
                                status='create')
        await bot.send_message(chat_id=callback.from_user.id,
                               text="✅ Розыгрыш сохранен и в ближайшее время будет опубликован")
        await bot.send_message(chat_id=callback.from_user.id,
                               text=f"""🆕 Если необходимо запостить розыгрыш в другие каналы/чаты,
                                то введите команду в боте:\n
                                /postlot{raffle[0].id}\n
                                ❗️ Вводящий данную команду должен являться админом такого канала,
                                 а сам канал должен быть добавлен в раздел "мои каналы" в боте.""")

        if data['publish_time'] == 0:
            raffle = await RaffleDAO.find_one_or_none(text_raffle=data['text_raffle'],
                                             text_button=data['text_button'],
                                             telegram_id=callback.from_user.id,
                                             channel_for_subscription=data['channels_subscribe'],
                                             number_winners=data['number_winners'],
                                             time_start=data['publish_time'],
                                             status='create')

            await send_raffle(text=data['text_raffle'], text_button=data['text_button'], raffle_id=raffle[0].id,
                              chat_ids=data['channel_send'])

    elif callback.data == "cancel":
        await bot.send_message(chat_id=callback.from_user.id,
                               text="Вы действительно хотите отменить создание розыгрыша?", reply_markup=Yes)
    else:
        await bot.send_message(chat_id=callback.from_user.id,
                               text="✅ Создание розыгрыша отменено\n"
                                    "Для вызова меню напишите /start")
        await state.clear()

@router.callback_query(F.data.in_(
    ["confirmation", "no confirmation",]
))
async def confirmation(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if callback.data == "confirmation":
        await choose_winner(raffle_id=data["id"])
    else:
        await bot.send_message(chat_id=callback.from_user.id,
                               text="Отмена")



@router.callback_query(F.data.in_(
    ["update_result", "chouse_winner", "delete_raffle", ]
))
async def publish(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if callback.data == "update_result":
        await bot.send_message(chat_id=callback.from_user.id,
                               text="🗓 Как завершить розыгрыш?", reply_markup=need_raffle_change)
    elif callback.data == "delete_raffle":
        await RaffleDAO.delete(id=data["id"])
        await bot.send_message(chat_id=callback.from_user.id,
                               text="Розыгрыш удален")
    elif callback.data == "chouse_winner":
        #await choose_winner(id=data["id"])
        await bot.send_message(chat_id=callback.from_user.id,
                               text="⚠️ Подтвердите завершение розыгрыша", reply_markup=confirmation_r)




