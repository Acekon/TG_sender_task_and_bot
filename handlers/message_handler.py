import time

from aiogram import Router, types

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters.command import Command

from handlers.db import search_mess, get_message_id, add_message, remove_message, message_enable, message_disable, \
    message_update_text
from handlers.img import get_collage, download_img, remove_img, remove_all_img, img_journal_create_json_file, \
    img_journal_get_image_list, img_journal_is_send_json_file
from conf import bot_token
from handlers.logger_setup import logger
from handlers.service import auth_admin

router = Router()


class FormSearchText(StatesGroup):
    mess_search_text = State()


class FormGetId(StatesGroup):
    mess_id = State()


class FormAddMess(StatesGroup):
    text_message = State()


class FormGetIdImg(StatesGroup):
    mess_id = State()
    mess_text = None


class FormReplaceMess(StatesGroup):
    mess_id = None
    state = State()


@router.message(Command(commands=['search']))
@auth_admin
async def command_get_search(message: Message, state: FSMContext):
    await state.set_state(FormSearchText.mess_search_text)
    await message.answer(f"Enter string for search")


@router.message(FormSearchText.mess_search_text)
@auth_admin
async def process_mess_search(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    messages = search_mess(message.text)
    if len(messages) <= 10:
        for mess in messages:
            await message.answer(f"ID = {mess[0]}\n{mess[1]}")
            time.sleep(0.2)
    else:
        await message.answer(f"Find {len(messages)}, please specify your request")
    return await state.clear()


@router.message(Command(commands=['get']))
@auth_admin
async def command_get_id(message: Message, state: FSMContext):
    await state.set_state(FormGetId.mess_id)
    await message.answer(f"Enter ID message")


@router.message(FormGetId.mess_id)
@auth_admin
async def process_mess_get(message: Message, state: FSMContext):  # todo in v0.4.1, add manual send
    await state.update_data(name=message.text)
    message_text = get_message_id(message.text)
    if not message_text:
        logger.error(f"Err: Not found ID message")
        return await message.answer(f"Not found ID message")
    path_collage = get_collage(message.text)
    kb = []
    if bool(int(message_text[2])):
        state_bottoms = types.InlineKeyboardButton(text="⛔ Disable", callback_data=f'mess_disable:{message.text}')
    else:
        state_bottoms = types.InlineKeyboardButton(text="✅ Enable", callback_data=f'mess_enable:{message.text}')
    kb_line_one = [types.InlineKeyboardButton(text="Remove message", callback_data=f'remove_mess_img:{message.text}')]
    if path_collage:
        kb_line_one.append(types.InlineKeyboardButton(text="Edit image list",
                                                      callback_data=f'edit_image_list:{message.text}'))
    kb_line_two = [state_bottoms,
                   types.InlineKeyboardButton(text="Replace message",
                                              callback_data=f'mess_replace:{message.text}')]
    kb_line_three = [types.InlineKeyboardButton(text="Cancel",
                                                callback_data=f'clear_keyboard')]
    kb.append(kb_line_one)
    kb.append(kb_line_two)
    kb.append(kb_line_three)
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    mess_text = (f"ID: {message_text[0]} Enable: {bool(int(message_text[2]))}\n"
                 f"Text:\n<code>{message_text[1]}</code>")
    if path_collage:
        await message.answer_photo(FSInputFile(path_collage), caption=mess_text, reply_markup=keyboard)
        remove_img(path_collage)
    else:
        await message.answer(mess_text, reply_markup=keyboard)
    return await state.clear()


@router.callback_query(lambda c: c.data and c.data.startswith('remove_all_img:'))
@auth_admin
async def command_remove_img(callback_query: CallbackQuery):
    image_id = callback_query.data.split(':')[-1]
    files_name = remove_all_img(image_id)
    return await callback_query.answer(f"Removed files:\n {files_name}")


@router.callback_query(lambda c: c.data and c.data.startswith('remove_mess_img:'))
@auth_admin
async def command_remove_message_img(callback_query: CallbackQuery):
    id_message = callback_query.data.split(':')[-1]
    files_name = remove_all_img(id_message)
    mess = remove_message(id_message)
    if not mess:
        logger.error(f"Message not found")
        mess = 'Message not found'
    else:
        mess = 'Message removed'
    return await callback_query.message.answer(f"Removed files:\n {files_name},\n{mess}")


@router.callback_query(lambda c: c.data and c.data.startswith('edit_image_list:'))
@auth_admin
async def command_edit_image_list(callback_query: CallbackQuery):
    id_message = callback_query.data.split(':')[-1]
    path_collage = get_collage(id_message, type_collage='vertical')
    kb = []
    history_list_image = img_journal_get_image_list(id_message)
    history_list = []
    for image in history_list_image:
        image_name = image.get('file_name').split('/')[-1]
        file_send = image.get('file_send')
        kb.append([
            types.InlineKeyboardButton(text=f"Remove: {image_name}",
                                       callback_data=f"remove_img:{image_name}"),
            types.InlineKeyboardButton(text=f"State is send: {bool(file_send)}",
                                       callback_data=f"send_state_img:{image_name}")
        ])
        file_name = image.get("file_name").split('/')[-1]
        history_list.append(f'Image: <b>{file_name}</b> '
                            f'sending:<b> {bool(image.get("file_send"))}</b>')
    text_history_list = "\n".join(history_list)
    kb.append([types.InlineKeyboardButton(text="Cancel", callback_data=f'clear_keyboard')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    await callback_query.message.answer_photo(FSInputFile(path_collage),
                                              caption=text_history_list,
                                              reply_markup=keyboard)
    remove_img(path_collage)


@router.callback_query(lambda c: c.data and c.data.startswith('remove_img:'))
@auth_admin
async def command_remove_img(callback_query: CallbackQuery):
    img_name = callback_query.data.split(':')[-1]
    remove_img(img_name=img_name, img_path=None)
    await callback_query.answer(text=f'Removed {img_name}')
    await callback_query.message.delete()


@router.callback_query(lambda c: c.data and c.data.startswith('send_state_img:'))
@auth_admin
async def command_remove_img(callback_query: CallbackQuery):
    img_name = callback_query.data.split(':')[-1]
    img_journal_is_send_json_file(img_name.split('_')[0], img_name)
    await callback_query.answer(text=f'Change state is send {img_name}')
    await callback_query.message.delete()
    await callback_query.message.answer(text=f'Change state is send {img_name}')


@router.callback_query(lambda c: c.data and c.data.startswith('mess_enable:'))
@auth_admin
async def command_message_enable(callback_query: CallbackQuery):
    message_id = callback_query.data.split(':')[-1]
    message_enable(message_id)
    await callback_query.answer(text=f'Enable message id: {message_id}')
    kb = []
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(lambda c: c.data and c.data.startswith('mess_disable:'))
@auth_admin
async def command_message_enable(callback_query: CallbackQuery):
    message_id = callback_query.data.split(':')[-1]
    message_disable(message_id)
    await callback_query.answer(text=f'Disable message id: {message_id}')
    kb = []
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(lambda c: c.data and c.data.startswith('mess_replace:'))
@auth_admin
async def command_message_replace(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(FormReplaceMess.state)
    FormReplaceMess.mess_id = callback_query.data.split(':')[-1]
    await callback_query.message.answer(f"Enter new message from save ID: {callback_query.data.split(':')[-1]}")


@router.message(FormReplaceMess.state)
@auth_admin
async def process_mess_replace(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    message_flag = message_update_text(FormReplaceMess.mess_id, message.text)
    if message_flag:
        await message.answer('Replace')
    else:
        logger.error(f"Err Replace")
        await message.answer('Error')
    return await state.clear()


@router.message(Command(commands=['create']))
@auth_admin
async def command_add_message(message: Message, state: FSMContext):
    await state.set_state(FormAddMess.text_message)
    await message.answer(f"Enter new message from save")


@router.message(FormAddMess.text_message)
@auth_admin
async def process_mess_add(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    message_text = add_message(message.text)
    img_journal_create_json_file(images=(f'{message_text.split("=")[-1].strip()}', []))
    await message.answer(message_text)
    return await state.clear()


@router.message(Command(commands=['upload']))
@auth_admin
async def command_upload_image(message: Message, state: FSMContext):
    FormGetIdImg.mess_text = None
    await state.set_state(FormGetIdImg.mess_id)
    await message.answer(f"Upload file and Enter ID message:")


@router.message(FormGetIdImg.mess_id)
@auth_admin
async def process_mess_add_img(message: Message, state: FSMContext):
    if FormGetIdImg.mess_text is None:
        FormGetIdImg.mess_text = message.caption
    await state.update_data(name=message.text)
    if message.content_type == 'photo' and FormGetIdImg.mess_text is not None:
        file_id = message.photo[-1].file_id
        result = download_img(bot_token=bot_token, file_id=file_id, mess_id=FormGetIdImg.mess_text)
        await message.answer(f"{result}")
    else:
        logger.error(f"Err: You not enter ID message")
        await message.answer("⚠ You not enter ID message")
    return await state.clear()


@router.callback_query(lambda c: c.data == 'clear_keyboard')
@auth_admin
async def process_control_admins(callback_query: CallbackQuery):
    kb = []
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
