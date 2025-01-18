from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, \
	InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


kb = [
	[types.KeyboardButton(text="Создать розыгрыш ❇️"), types.KeyboardButton(text="Мои розыгрыши 🎁")],
	[types.KeyboardButton(text="Мои каналы 📢"), types.KeyboardButton(text="Техническая поддержка ⚙️")],
    [types.KeyboardButton(text="Поддержать Бота ⭐️️")],
]
menu = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


kb = [
	[types.InlineKeyboardButton(text="добавить новый канал", callback_data="add_channel")]]
add_channel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)


# команда отмена
# используется админом
kb = [[types.InlineKeyboardButton(text="отмена", callback_data="cancel_my_channel")]]
cancel = types.InlineKeyboardMarkup(inline_keyboard=kb)

kb = [
	[types.InlineKeyboardButton(text="Участвую", callback_data="engage")],
	[types.InlineKeyboardButton(text="Участвую!", callback_data="engage!")],
	[types.InlineKeyboardButton(text="Принять участи", callback_data="take_part")],
]
various_engage = types.InlineKeyboardMarkup(inline_keyboard=kb)

kb = [[types.InlineKeyboardButton(text="Розыгрыш без обязательной подписки", callback_data="enough_channel")]]
not_subscription = types.InlineKeyboardMarkup(inline_keyboard=kb)

kb = [
	[types.InlineKeyboardButton(text="Прямо сейчас", callback_data="right_now")],
	[types.InlineKeyboardButton(text="Запланировать публикацию", callback_data="choose_time")],

]
publish_keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)



kb = [
	[types.InlineKeyboardButton(text="По количеству участников", callback_data="participant")],
	[types.InlineKeyboardButton(text="По времени", callback_data="time")],
]
need_raffle = types.InlineKeyboardMarkup(inline_keyboard=kb)

kb = [
	[types.InlineKeyboardButton(text="По количеству участников", callback_data="change_participant")],
	[types.InlineKeyboardButton(text="По времени", callback_data="change_time")],
	[types.InlineKeyboardButton(text="Отмена", callback_data="change_cancel")],
]
need_raffle_change = types.InlineKeyboardMarkup(inline_keyboard=kb)

kb = [
	[types.InlineKeyboardButton(text="Сохранить", callback_data="save")],
	[types.InlineKeyboardButton(text="отмена", callback_data="cancel")],
]
save_raffle = types.InlineKeyboardMarkup(inline_keyboard=kb)

kb = [
	[types.InlineKeyboardButton(text="Да", callback_data="Yes")],
]
Yes = types.InlineKeyboardMarkup(inline_keyboard=kb)

kb = [
	[types.InlineKeyboardButton(text="Достаточно каналов, идем дальше", callback_data="enough_channel")],
]
save = types.InlineKeyboardMarkup(inline_keyboard=kb)

kb = [
	[types.InlineKeyboardButton(text="Завершить", callback_data="confirmation")],
	[types.InlineKeyboardButton(text="Не Завершить", callback_data="no confirmation")],

]
confirmation_r = types.InlineKeyboardMarkup(inline_keyboard=kb)

kb = [
	[types.InlineKeyboardButton(text="обновить имя", callback_data="update_name")],
	[types.InlineKeyboardButton(text="удалить из бота", callback_data="delete_channel")],

]
menu_channel = types.InlineKeyboardMarkup(inline_keyboard=kb)

kb = [
	[types.InlineKeyboardButton(text="Публикуем", callback_data="publish")],
	[types.InlineKeyboardButton(text="Отмена", callback_data="no_publish")],

]
publishg = types.InlineKeyboardMarkup(inline_keyboard=kb)


def names_channel(list_name):
	result = InlineKeyboardBuilder()
	result.row(types.InlineKeyboardButton(text="добавить новый канал", callback_data="add_channel"))

	for i in list_name:
		result.row(types.InlineKeyboardButton(text=f"{i}", callback_data=f"name_my_channel {i}"))
	return result

# def names_channel_my_channel(list_name):
# 	result = InlineKeyboardBuilder()
# 	result.row(types.InlineKeyboardButton(text="добавить новый канал", callback_data="add_channel"))
# 	for i in list_name:
# 		result.row(types.InlineKeyboardButton(text=f"{i}", callback_data=f"name_channel {i}"))
# 	return result

def add_participant(text_raffle, id):
	kb = [
		[types.InlineKeyboardButton(text=f"{text_raffle} ", callback_data=f"add_participant {id}")],
	]
	add_participant = types.InlineKeyboardMarkup(inline_keyboard=kb)
	return add_participant

def my_channel(channels):
	result = InlineKeyboardBuilder()
	for i in channels:
		result.row(types.InlineKeyboardButton(text=f"{i.name}", callback_data=f"name_channel {i.id}"))
	return result

def add_my_channel(channels, raffle_id):
	result = InlineKeyboardBuilder()
	for i in channels:
		result.row(types.InlineKeyboardButton(text=f"{i.name}", callback_data=f"add_channel,{i.id},{i.name},{raffle_id}"))
	return result

def button_raffle(button):
	result = InlineKeyboardBuilder()
	result.row(types.InlineKeyboardButton(text=f"{button}", callback_data=f"{button}"))
	return result

def my_lot_keyboard(status):
	result = InlineKeyboardBuilder()

	if status == "publish":
		result.row(types.InlineKeyboardButton(text=f"Изменения условия подведения результатов",
											  callback_data=f"update_result"))
		result.row(types.InlineKeyboardButton(text=f"Подвести итоги прямо сейчас" ,
											  callback_data=f"chouse_winner"))
	elif status == "end":
		pass
		# result.row(types.InlineKeyboardButton(text=f"выбрать дополнительных победителей",
		# 									  callback_data=f"add_winner"))
	else:
		result.row(types.InlineKeyboardButton(text=f"изменить условия подведения результатов",
											  callback_data=f"update_result"))
	result.row(types.InlineKeyboardButton(text=f"Удалить розыгрыш",
										  callback_data=f"delete_raffle"))
	return result
