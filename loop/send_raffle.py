import random
from datetime import datetime

from aiogram import Bot, Router

from config import settings
from keyboards.keyboard import save_raffle, add_participant
from sql import RaffleDAO, ParticipantDAO, ChannelDAO

router = Router()
bot = Bot(token=settings.get_token())


async def start_end_raffle():
    raffles = await RaffleDAO.find_all()

    for raffle in raffles:
        if datetime.now().strftime("%d.%m.%Y %H:%M") == raffle.time_start:
            await send_raffle(text=raffle.text_raffle, text_button=raffle.text_button, raffle_id=raffle.id,
                              chat_ids=raffle.pablish_channal)
        elif datetime.now().strftime("%d.%m.%Y %H:%M") == raffle.time_end:
             await choose_winner(raffle_id=raffle.id)


async def send_raffle(text, text_button, raffle_id, chat_ids):
    await RaffleDAO.update(id=raffle_id, status="publish")
    for chat_id in chat_ids.split(" "):
        channel = await ChannelDAO.find_all(id=chat_id)
        await bot.send_message(chat_id=channel[0].channel_telegram_id,
                               text=text, reply_markup=add_participant(text_button, raffle_id))

async def choose_winner(raffle_id):
    participants = await ParticipantDAO.find_all(post_id=raffle_id)
    raffle = await RaffleDAO.find_one_or_none(id=raffle_id)
    random.shuffle(participants)
    text = '🎉 Результаты розыгрыша:\n\nПобедители:\n'
    for i in participants:
        text = f'{text}{participants.index(i)+1}. {i.participant_name} (@{i.participant_user_name})\n'
        if participants.index(i)+1 == raffle[0].number_winners:
            break
    await bot.send_message(chat_id=raffle[0].telegram_id,
                           text=text)

    await RaffleDAO.update(id=raffle_id, status="end")