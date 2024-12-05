import sqlite3

from conf import db_path
from handlers.logger_setup import logger


def check_last_sent_status() -> tuple:
    conn = sqlite3.connect(db_path())
    c = conn.cursor()
    c.execute(f'SELECT COUNT(ids) as total,'
              f'COUNT(last_send) as not_send, '
              f'COUNT(ids) - COUNT(last_send) as send '
              f'FROM messages;')
    lats_sent = c.fetchone()
    conn.commit()
    conn.close()
    return lats_sent


def mess_reset() -> str:
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        c.execute('UPDATE messages SET last_send = NULL;')
        conn.commit()
        conn.close()
        return f'History sending messages is reset, new iteration started.'
    except sqlite3.OperationalError as err:
        logger.error(f"Not reset! Error: {err}")
        return f"Not reset! Error: {err}"


def search_mess(mess_text):
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        sql = f'SELECT ids, text_message FROM messages WHERE text_message like "%{mess_text}%"'
        c.execute(sql)
        messages = c.fetchall()
        conn.commit()
        conn.close()
        if not messages:
            logger.error(f"Not found")
            return [("", "Message: Not found")]
        return messages
    except sqlite3.OperationalError as err:
        logger.error(f"Error: {err}")
        return [("", f"Error: {err}")]


def get_message_id(mess_id):
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        c.execute(f'SELECT ids, text_message, enable FROM messages WHERE ids="{mess_id}"')
        mess = c.fetchone()
        conn.commit()
        conn.close()
        if not mess:
            return None
        return mess
    except sqlite3.OperationalError as err:
        logger.error(f"Error: {err}")
        return f"Error: {err}"


def add_message(text_message):
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        text_message = text_message.replace("'", '`')
        c.execute(
            f"INSERT INTO messages (text_message, enable) VALUES ('{text_message}', '1')")
        conn.commit()
        c.execute('SELECT ids FROM messages ORDER BY ids DESC LIMIT 1')
        lats_sent = c.fetchone()
        conn.commit()
        conn.close()
        return f"Saved! last ID= {lats_sent[0]}"
    except sqlite3.OperationalError as err:
        logger.error(f"Not Save! Error: {err}")
        return f"Not Save! Error: {err}"


def remove_message(id_mess):
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        count = c.execute(f'DELETE FROM messages WHERE ids = "{id_mess}"').rowcount
        conn.commit()
        conn.close()
        if count != 0:
            return True
        else:
            return False
    except sqlite3.OperationalError as err:
        logger.error(f"Error: {err}")
        return f"Error: {err}"


def get_admins_list():
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        admins = c.execute(f'SELECT value, description FROM settings WHERE name = "admin_id"')
        conn.commit()
        admins = admins.fetchall()
        conn.close()
        res_admins = []
        for adm in admins:
            res_admins.append([int(adm[0]), adm[1]])
        return res_admins
    except sqlite3.OperationalError as err:
        logger.error(f"Error: {err}")
        return f"Error: {err}"


def add_admin_list(admin_id, description):
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        c.execute(f"INSERT INTO settings (name,value,description) VALUES ('admin_id','{admin_id}','{description}')")
        conn.commit()
        conn.close()
        return True
    except sqlite3.OperationalError as err:
        logger.error(f"Error: {err}")
        return f"Error: {err}"


def remove_admin_list(admin_id):
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        count = c.execute(f'DELETE FROM settings WHERE value = "{admin_id}"').rowcount
        conn.commit()
        conn.close()
        if count != 0:
            return True
        else:
            logger.error(f"Not Save! Error: {admin_id}")
            return False
    except sqlite3.OperationalError as err:
        logger.error(f"Error: {err}")
        return f"Error: {err}"


def create_all_table():
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        c.execute(f'CREATE TABLE "messages" '
                  f'("ids"INTEGER,'
                  f'"text_message"TEXT NOT NULL,'
                  f'"last_send" TEXT DEFAULT NULL,'
                  f'"enable" BLOB DEFAULT 1,'
                  f'PRIMARY KEY("ids" AUTOINCREMENT))')
        c.execute(f'CREATE TABLE "settings" ('
                  f'"id" INTEGER NOT NULL UNIQUE,'
                  f'"name" TEXT,'
                  f'"value"	TEXT,'
                  f'"description" TEXT,'
                  f'PRIMARY KEY("id" AUTOINCREMENT))')
        conn.commit()
        conn.close()
    except sqlite3.OperationalError as err:
        logger.error(f"Error: {err}")
        return f"Error: {err}"


def get_sendto():
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        send_to = c.execute(f'SELECT value, description FROM settings WHERE name = "send_to"')
        conn.commit()
        send_to = send_to.fetchone()
        if not send_to:
            logger.error(f"Not Save! Error: {send_to}")
            return False
        conn.close()
        return send_to
    except sqlite3.OperationalError as err:
        logger.error(f"Error: {err}")
        return f"Error: {err}"


def add_sendto(chanel_id, description):
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        c.execute(f"INSERT INTO settings (name,value,description) VALUES ('send_to','{chanel_id}','{description}')")
        conn.commit()
        conn.close()
        return True
    except sqlite3.OperationalError as err:
        logger.error(f"Error: {err}")
        return f"Error: {err}"


def remove_sendto():
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        count = c.execute(f'DELETE FROM settings WHERE name = "send_to";').rowcount
        conn.commit()
        conn.close()
        if count != 0:
            return True
        else:
            return False
    except sqlite3.OperationalError as err:
        logger.error(f"Error: {err}")
        return f"Error: {err}"


def message_disable(message_id):
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        count = c.execute(f'UPDATE messages SET "enable"=0 WHERE "_rowid_"="{message_id}"').rowcount
        conn.commit()
        conn.close()
        if count != 0:
            return True
        else:
            logger.error(f"Not Save! Error: {message_id}")
            return False
    except sqlite3.OperationalError as err:
        logger.error(f"Error: {err}")
        return f"Error: {err}"


def message_enable(message_id):
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        count = c.execute(f'UPDATE messages SET "enable"=1 WHERE "_rowid_"="{message_id}"').rowcount
        conn.commit()
        conn.close()
        if count != 0:
            return True
        else:
            logger.error(f"Not Save! Error: {message_id}")
            return False
    except sqlite3.OperationalError as err:
        logger.error(f"Error: {err}")
        return f"Error: {err}"


def message_update_text(message_id, mess_text: str):
    try:
        conn = sqlite3.connect(db_path())
        c = conn.cursor()
        mess_text = mess_text.replace("'", '`')
        count = c.execute(f'UPDATE messages '
                          f'SET "text_message"="{mess_text}" '
                          f'WHERE "_rowid_"="{message_id}"').rowcount
        conn.commit()
        conn.close()
        if count != 0:
            return True
        else:
            logger.error(f"Not Save! Error: {message_id}")
            return False
    except sqlite3.OperationalError as err:
        logger.error(f"Error: {err}")
        return f"Error: {err}"
