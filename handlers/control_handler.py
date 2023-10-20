from aiogram import types, Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.utils.markdown import hbold

from aiogram.filters.command import Command, CommandStart

from handlers.db import check_last_sent_status, mess_reset, get_admins_list, remove_admin_list, add_admin_list
from handlers.service import auth_admin

router = Router()


class FormGetNewAdmins(StatesGroup):
    name_admin = State()


@router.message(Command(commands=['status']))
@auth_admin
async def command_check_status(message):
    sending_stats = check_last_sent_status()
    text_sending_stats = (f'All messages = {sending_stats[0]}\n'
                          f'Available Send = {sending_stats[2]}\n'
                          f'Sent = {sending_stats[1]}')
    kb = [
        [types.InlineKeyboardButton(text="Reset sending message", callback_data=f'reset')],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    return await message.answer(f"{text_sending_stats}", reply_markup=keyboard)


@router.callback_query(F.data == 'reset')
@auth_admin
async def command_mess_reset(message: CallbackQuery):
    return await message.answer(f"{mess_reset()}")


@router.message(CommandStart())
@auth_admin
async def command_start_handler(message: Message) -> Message:
    return await message.answer(f"Hello, {hbold(message.from_user.full_name)}")


@router.message(Command(commands=['help']))
@auth_admin
async def command_help(message: Message) -> Message:
    help_text = """To use this bot, you need to understand the available commands and how to interact with it.
    Here's a brief guide on how to use this bot:

<b>1. Searching for Messages:</b>
- Start a search by sending the `/search` command. The bot will prompt you to enter a string for the search.
- Enter the string you want to search for, and the bot will return messages containing that string.

<b>2. Viewing a Message by ID:</b>
- To view a specific message by its ID, use the `/get` command. The bot will prompt you to enter the ID of the message.
- Enter the ID of the message, and the bot will display the message content along with some options.

<b>3. Managing Images for a Message:</b>
- When viewing a message, you have several options:
  - Remove All Images: Click on "Remove Message & all Img" to delete the message and all associated images.
  - Remove All Images (Keep Message): Click on "Remove all Img" to delete only the images, keeping the message.
  - Edit Image List: Click on "Edit image list" to view and manage the list of images associated with the message.

<b>4. Managing Images in an Image List:</b>
- If you choose to edit the image list, you will see a list of images associated with the message. For each image,
 you can click "Remove" to delete that specific image.

<b>5. Adding a New Message:</b>
- You can add a new message to be saved using the `/create` command. The bot will prompt you to enter the new message.
- Enter the message text you want to save, and the bot will confirm the addition.

<b>6. Uploading an Image for a Message:</b>
- To upload an image for a specific message, use the `/upload` command. The bot will prompt you to upload an
 image and provide the ID of the message.
- Upload an image, and the bot will associate it with the specified message.

<b>7. Checking Bot Status:</b>
- To check the bot's status, you can use the `/status` command. 
It will display information about the number of messages,
 available messages for sending, and the number of sent messages.
- You also have the option to reset sending status if needed.

<b>8. Admin control panel:</b>
- The Admin Control Panel allows you to manage administrators and change the publication schedule using the `/control` command.
- You can add new administrators, remove existing ones, and configure the timing of messages.

<b>9. Starting the Bot:</b>
- When you start a chat with the bot, it will greet you. However, this bot seems to have permission settings,
 and not everyone may have permission to use all commands.
"""
    kb = [
        [types.InlineKeyboardButton(text="Get command from BotFather", callback_data=f'get_bot_father')],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    return await message.answer(f"{help_text}", reply_markup=keyboard)


@router.callback_query(lambda c: c.data and c.data.startswith('get_bot_father'))
@auth_admin
async def command_get_bot_father(callback_query: CallbackQuery):
    text_bot_father = """
status - Status
create - Add joke in DB
upload - Add img for joke in DB
get - View is message
search - Search text in message
help - View help
control - Add and remove admins
    """
    await callback_query.message.answer(f"Copy this text and past BotFather\n "
                                        f"> /mybots > 'select your bots' > 'Edit bot' >"
                                        f"'Edit Commands' > Enter next text ")
    return await callback_query.message.answer(f"{text_bot_father}")


@router.message(Command(commands=['test']))
@auth_admin
async def command_test(message: Message) -> Message:
    return await message.answer(text='test')


@router.message(Command(commands=['control']))
@auth_admin
async def command_control(message: Message):
    kb = [[types.InlineKeyboardButton(text="Control admins", callback_data=f'control_admins')]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    return await message.answer(f"Control bots settings", reply_markup=keyboard)


@router.callback_query(lambda c: c.data == 'control_admins')
@auth_admin
async def process_control_admins(callback_query: CallbackQuery):
    admins = get_admins_list()
    kb = []
    for admin in admins:
        kb.append([types.InlineKeyboardButton(text=f'❌ {admin[0]} ({admin[1]})',
                                              callback_data=f'remove_admin:{str(admin[0])}')])
    kb.append([types.InlineKeyboardButton(text="New admin", callback_data='new_admin'),
               types.InlineKeyboardButton(text="Cancel", callback_data='clear_keyboard')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    await callback_query.message.edit_text(reply_markup=keyboard, text="List of admins:")


@router.callback_query(lambda c: c.data == 'clear_keyboard')
@auth_admin
async def process_control_admins(callback_query: CallbackQuery):
    kb = []
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(lambda c: c.data and c.data.startswith('remove_admin:'))
@auth_admin
async def process_remove_admins(callback_query: CallbackQuery):
    admins = get_admins_list()
    if not len(admins) > 1:
        return await callback_query.answer(f"You do not have remove last admin")
    if remove_admin_list(callback_query.data.split(':')[-1]):
        return await callback_query.answer(f"Removed admin: {callback_query.data.split(':')[-1]}")
    else:
        return await callback_query.answer(f"Err remove: {callback_query.data.split(':')[-1]}")


@router.callback_query(lambda c: c.data and c.data.startswith('new_admin'))
@auth_admin
async def process_new_admins(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(FormGetNewAdmins.name_admin)
    await callback_query.message.answer(f"Enter id and descriptions new admin\n"
                                        f"Example: <b>12345678,NameAdmin</b>")


@router.message(FormGetNewAdmins.name_admin)
@auth_admin
async def process_mess_search(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    try:
        admin_id, description = message.text.split(',')
        result = add_admin_list(admin_id, description)
        if result:
            await message.answer(f'Add: {admin_id}, {description}')
        else:
            await message.answer(f'Err: {admin_id}, {description}\n {result}')
    except ValueError:
        await message.answer('Err: required\n<b>12345678,NameAdmin</b>')
    return await state.clear()
