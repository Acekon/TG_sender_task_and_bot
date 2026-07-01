import datetime
import logging
import random
import sqlite3
import sys
import time
import threading

import requests
import schedule
from conf import bot_token, db_path
from handlers.db import get_sendto, mess_reset, get_admins_list, get_start_times
from handlers.img import img_journal_get_image_list, img_journal_is_send_json_file, img_journal_generate_json_file
from handlers.logger_setup import logger


def send_photo(file_path, caption, send_to):
    with open(file_path, 'rb') as img_file:
        logger.info(f'Try sending photo')
        img = {'photo': ('_', img_file, 'image/jpeg')}
        url = f'https://api.telegram.org/bot{bot_token}/sendPhoto?chat_id={send_to}&caption={caption}'
        response = requests.post(url, files=img, timeout=10)
        logger.info(response.json())
        return response.text


def send_text(message_text, send_to):
    logger.info(f'Try sending text')
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    response = requests.post(url, json={'chat_id': send_to, 'parse_mode': 'html', 'text': message_text}, timeout=10)
    logger.info(response.json())
    return response.text


def send_random_message():
    channel_id = get_sendto()[0]
    conn = sqlite3.connect(db_path())
    c = conn.cursor()
    c.execute('SELECT * FROM messages WHERE last_send is NULL AND enable is True')
    messages_db = c.fetchall()
    if len(messages_db) < 1:  # min count not send in db
        admins = get_admins_list()
        mess_text = mess_reset()
        for admin in admins:
            send_text(mess_text, admin[0])
    c.execute('SELECT ids, text_message, last_send  FROM messages WHERE last_send is NULL AND enable is True')
    messages_db = c.fetchall()
    message_db = messages_db[random.randint(0, len(messages_db) - 1)]
    message_id, text, last_sent = message_db
    img_mess = open_random_image(message_id)
    send_message(message_text=text, img_path=img_mess, channel_id=channel_id)
    c.execute('UPDATE messages SET last_send=? WHERE ids=?',
              (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), message_id))
    conn.commit()
    conn.close()


def send_manual_message(message_id):
    channel_id = get_sendto()[0]
    conn = sqlite3.connect(db_path())
    c = conn.cursor()
    sql_query = f'SELECT text_message FROM messages WHERE ids ={message_id}'
    c.execute(sql_query)
    messages_db = c.fetchone()
    img_mess = open_random_image(message_id)
    send_message(message_text=messages_db[0], img_path=img_mess, channel_id=channel_id)


def send_message(message_text, img_path, channel_id):
    if img_path:
        send_photo(file_path=img_path, caption=message_text, send_to=channel_id)
    else:
        send_text(message_text, send_to=channel_id)


def open_random_image(message_id):
    img_files = img_journal_get_image_list(message_id)
    not_send_images = []
    send_images = []
    if img_files:
        for image in img_files:
            if image.get('file_send') == 0:
                not_send_images.append(image)
            if image.get('file_send') == 1:
                send_images.append(image)
        if not_send_images == send_images:
            return False
        images = not_send_images
        if len(images) == 0:
            img_journal_generate_json_file(message_id)
            images = send_images
        tmp_random_image = []
        for _ in range(10):
            tmp_random_image.append(random.randrange(0, len(images)))
        img = images[tmp_random_image[random.randrange(0, 8)]]
        img_journal_is_send_json_file(message_id, img.get('file_name').split('/')[-1])
        return img.get('file_name')
    return False


def reschedule_tasks(start_times):
    schedule.clear()
    for times in start_times:
        schedule.every().day.at(times).do(send_random_message)


def update_start_times():
    while True:
        start_times = get_start_times()
        print(f'Task will sending times: {start_times}')
        reschedule_tasks(start_times)
        time.sleep(60*60)


def main_run():
    start_times = get_start_times()
    reschedule_tasks(start_times)
    update_thread = threading.Thread(target=update_start_times)
    update_thread.daemon = True
    update_thread.start()

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR, stream=sys.stdout)
    main_run()
