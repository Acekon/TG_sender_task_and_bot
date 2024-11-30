import fnmatch
import json
import os
import random
import string
from typing import Tuple

import requests
from PIL import Image, ImageDraw, ImageFont

from handlers.service import logger

full_path_img_dir = os.path.join(os.getcwd(), 'img/')


def get_collage(mess_id, type_collage=None):
    """Default: type_collage=none
     type_collage = vertical"""
    try:
        files_name = img_journal_get_image_list(str(mess_id))
        if files_name:
            images = []
            for file in files_name:
                images.append(file.get('file_name'))
            if type_collage == 'vertical':
                collage_path = create_vertical_collage(images)
                return collage_path
            collage_path = create_image_collage(images)
            return collage_path
    except FileNotFoundError:
        logger.error(f"FileNotFoundError: please create {full_path_img_dir} dir")
        return f'Error please create {full_path_img_dir} dir'


def remove_collage(collage_path):
    if os.path.isfile(collage_path):
        os.remove(collage_path)


def create_image_collage(image_paths):
    random_prefix_file = ''.join(random.choice(string.ascii_letters) for _ in range(6))
    output_path = f'{full_path_img_dir}collage_{random_prefix_file}.png'
    image_size = (200, 200)
    collage_size = (image_size[0] * len(image_paths), image_size[1])
    collage = Image.new('RGB', collage_size)
    for i, image_path in enumerate(image_paths):
        img_name = image_path.split('/')[-1]
        image = Image.open(image_path)
        image = image.resize(image_size)
        im = ImageDraw.Draw(image)
        im.text((15, 170), f"{img_name}", fill=(255, 0, 0), font=ImageFont.truetype("arial.ttf", 22))
        collage.paste(image, (i * image_size[0], 0))
    collage.save(output_path)
    return output_path


def create_vertical_collage(image_paths):
    width = 600
    random_prefix_file = ''.join(random.choice(string.ascii_letters) for _ in range(6))
    output_path = f'{full_path_img_dir}collage_{random_prefix_file}.png'
    image_size = (200, 200)
    collage_height = image_size[1] * len(image_paths)
    if len(image_paths) >= 5:
        width = len(image_paths) * 100
    collage_width = image_size[0] + width
    collage = Image.new('RGB', (collage_width, collage_height), (255, 255, 255))
    images_name = []
    for i, image_path in enumerate(image_paths):
        img_name = image_path.split('/')[-1]
        images_name.append(img_name)
        image = Image.open(image_path)
        image = image.resize(image_size)
        collage.paste(image, (0, i * image_size[1]))
        draw = ImageDraw.Draw(collage)
        text_x = image_size[0] + 55
        text_y = i * image_size[1] + image_size[1] // 2
        text_color = (0, 0, 0)
        font = ImageFont.truetype("arial.ttf", 20)
        draw.text((text_x, text_y), img_name, fill=text_color, font=font)
    collage.save(output_path)
    return output_path


def download_img(file_id, bot_token, mess_id):
    file_info = requests.get(f'https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}')
    file_path = file_info.json()['result']['file_path']
    response_img = requests.get(f'https://api.telegram.org/file/bot{bot_token}/{file_path}')
    random_prefix_file = ''.join(random.choice(string.ascii_letters) for _ in range(6))
    with open(f"img/{mess_id}_{random_prefix_file}.png", 'wb') as f:
        f.write(response_img.content)
        img_journal_append_json_file(json_file_mess_id=mess_id, new_image_name=f"{mess_id}_{random_prefix_file}.png")
    return f"File {mess_id}_{random_prefix_file}.png is uploads"


def remove_img(img_path, img_name=None):
    if img_name:
        logger.info(f"Try remove image name: ({img_name})")
        img_journal_pop_json_file(json_file_mess_id=img_name.split('_')[0], pop_image_name=img_name)
        os.remove(full_path_img_dir + img_name)
        return True
    if os.path.isfile(f'{img_path}'):
        logger.info(f"Try remove image path: ({img_path})")
        os.remove(img_path)
        return True
    else:
        logger.error(f"File not found: ({img_path})")
        return f"File not found: ({img_path})"


def remove_all_img(mess_id):
    """Examples: mess_id = 101"""
    matching_files = []
    files_name = []
    for file_name in os.listdir(full_path_img_dir):
        if fnmatch.fnmatch(file_name, f'{mess_id}_*.png'):
            matching_files.append(os.path.abspath(full_path_img_dir + file_name))
            files_name.append(file_name)
    if matching_files:
        for img_path in matching_files:
            remove_img(img_path)
        return files_name
    else:
        return False


def img_journal_remove_img_json_file(json_file_mess_id):
    """Remove json file
    Examples: mess_id = 101"""
    logger.info(f"Try to remove {json_file_mess_id}.json file")
    file_path = os.path.join(full_path_img_dir, f"{json_file_mess_id}.json")
    if not os.path.isfile(file_path):
        logger.error(f"File not found: ({json_file_mess_id}.json)")
        return False
    for file_name in os.listdir(full_path_img_dir):
        if fnmatch.fnmatch(file_name, f'{json_file_mess_id}_*.png'):
            logger.error(f"File not delete is found image: ({file_name})")
            return False
    try:
        os.remove(file_path)
        logger.info(f"Removed {file_path} file")
    except PermissionError as e:
        logger.error(f"Permission denied: {file_path} file")
        logger.error(e.strerror)


def img_journal_create_json_file(images: Tuple[str, list]):
    """Create json file to list images"""
    file_data = {}
    result_files_list = []
    file_list = images[1]
    file_path = os.path.join(full_path_img_dir, f"{images[0]}.json")
    for img in file_list:
        file_data['file_name'] = img
        file_data['file_send'] = 0
        result_files_list.append(file_data)
        file_data = {}
    with open(file_path, 'w', encoding='UTF-8') as file:
        json.dump({images[0]: result_files_list}, file)
        file.close()


def img_journal_generate_json_file(mess_id):
    """Find all images for message_id in folder"""
    files_name = []
    images_list = {}
    current_id = ''
    for file_name in os.listdir(full_path_img_dir):
        if current_id == '':
            current_id = mess_id
        if fnmatch.fnmatch(file_name, f'{mess_id}_*.png'):
            files_name.append(file_name)
    images_list[current_id] = files_name
    for image in images_list.items():
        img_journal_create_json_file(image)


def img_journal_regenerate_all_json_file():
    """Regenerate all json files in folder"""
    id_lists = []
    for file_name in os.listdir(full_path_img_dir):
        if fnmatch.fnmatch(file_name, f'*_*.png'):
            message_id = file_name.split('_')[0]
            if len(id_lists) == 0:
                id_lists.append(message_id)
                continue
            if id_lists[-1] != message_id:
                id_lists.append(message_id)
    for id_list in id_lists:
        img_journal_generate_json_file(id_list)


def img_journal_append_json_file(json_file_mess_id, new_image_name):
    file_path = os.path.join(full_path_img_dir, f"{json_file_mess_id}.json")
    if not os.path.isfile(file_path):
        return False
    with open(file_path, 'r', encoding='UTF-8') as file:
        dict_file = {'file_name': new_image_name, 'file_send': 0}
        images_list = json.load(file)
        image_id = list(images_list.keys())[0]
        new_image_list = images_list.get(image_id)
        new_image_list.append(dict_file)
    with open(file_path, 'w', encoding='UTF-8') as file:
        images_list[image_id] = new_image_list
        json.dump(images_list, file)
        file.close()


def img_journal_pop_json_file(json_file_mess_id, pop_image_name):
    """Pop images from json file"""
    logger.info(f'Try to pop image ({pop_image_name}) from json ({json_file_mess_id})')
    file_path = os.path.join(full_path_img_dir, f"{json_file_mess_id}.json")
    if not os.path.isfile(file_path):
        logger.error(f"File not found: ({file_path})")
        return False
    with open(file_path, 'r', encoding='UTF-8') as file:
        new_image_list = []
        images_list = json.load(file)
        image_id = list(images_list.keys())[0]
        current_image_list = images_list.get(image_id)
        for image in current_image_list:
            if pop_image_name != image['file_name']:
                new_image_list.append(image)
    if new_image_list != current_image_list:
        logger.info(f'Image popped from json ({pop_image_name})')
    else:
        logger.info(f'Image not popped from json ({pop_image_name})')
    with open(file_path, 'w', encoding='UTF-8') as file:
        images_list[image_id] = new_image_list
        json.dump(images_list, file)
        file.close()


def img_journal_is_send_json_file(json_file_mess_id, image_name):
    """Marked is send image on json file"""
    file_path = os.path.join(full_path_img_dir, f"{json_file_mess_id}.json")
    if str(json_file_mess_id).split('.')[0] != image_name.split('_')[0]:
        logger.error(f"File ({json_file_mess_id}) not equal to image ({image_name})")
        return False
    if not os.path.isfile(file_path):
        logger.error(f"File not found: ({file_path})")
        return False
    with open(file_path, 'r', encoding='UTF-8') as file:
        new_image_list = []
        images_list = json.load(file)
        image_id = list(images_list.keys())[0]
        current_image_list = images_list.get(image_id)
        for image in current_image_list:
            if image_name == image['file_name']:
                if image['file_send'] == 0:
                    image['file_send'] = 1
                else:
                    image['file_send'] = 0
            new_image_list.append(image)
        with open(file_path, 'w', encoding='UTF-8') as file_write:
            images_list[image_id] = new_image_list
            json.dump(images_list, file_write)
            file_write.close()


def img_journal_get_image_list(json_file_mess_id):
    file_path = os.path.join(full_path_img_dir, f"{json_file_mess_id}.json")
    full_path_image_list = []
    image_data = {'file_name': '', 'file_send': ''}
    if not os.path.isfile(file_path):
        logger.error(f"File not found: ({file_path})")
        return False
    with open(file_path, 'r', encoding='UTF-8') as file:
        images_list = json.load(file)
        for image in images_list.get(str(json_file_mess_id)):
            path = os.path.join(full_path_img_dir, image.get('file_name'))
            if not os.path.isfile(path):
                logger.error(f"Image not found: ({path})")
            image_data['file_name'] = path
            image_data['file_send'] = image.get('file_send')
            full_path_image_list.append(image_data)
            image_data = {}
    return full_path_image_list


if __name__ == '__main__':
    pass
