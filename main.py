import requests
import random
import os
import sys

from urllib.parse import urlparse
from pathlib import Path
from dotenv import load_dotenv


class VKException(Exception):
    '''
    Ловим ответы с ошибками от vk
    '''
    def __init__(self, text):
        self.txt = text


def download_random_comic():
    ''' Скачиваем случайный комикс '''

    last_img_url = 'https://xkcd.com/info.0.json'
    response = requests.get(last_img_url)
    response.raise_for_status()
    last_num = response.json()['num']
    selected_num = random.randint(1, last_num)
    url = f'https://xkcd.com/{selected_num}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    comic_metadata = response.json()
    img_url = comic_metadata['img']
    img_path = urlparse(img_url).path
    img_filename = Path(img_path).name
    img_response = requests.get(img_url)
    img_response.raise_for_status()
    img = img_response.content
    comment = comic_metadata['alt']
    with open(img_filename, "wb") as file_img:
        file_img.write(img)
    return img_filename, comment


def get_upload_server_addr(token, group_id, ver):
    ''' Получаем адрес сервера для загрузки комикса в vk '''

    headers = {
        'Authorization': f'Bearer {token}'
        }
    params = {
        'group_id': group_id,
        'v': ver,
        }
    vk_url = 'https://api.vk.com/method/photos.getWallUploadServer'
    response = requests.get(vk_url, headers=headers, params=params)
    response.raise_for_status()
    is_response_good(response)
    return response.json()['response']['upload_url']


def is_response_good(response):
    '''
    Проверяем ответ от vk
    '''

    checking_response = response.json()
    if 'error' in checking_response:
        raise VKException(checking_response['error']['error_msg'])


def upload_photo(url, img_filename):
    ''' Загружаем картинку комикса на сервер vk '''

    with open(img_filename, 'rb') as file:
        vk_file = {
            'photo': file,
            }
        response = requests.post(url, files=vk_file)
    response.raise_for_status()
    is_response_good(response)
    response_params = response.json()
    photo = response_params["photo"]
    server = response_params["server"]
    vk_hash = response_params["hash"]
    return photo, server, vk_hash


def save_wall_photo(token, group_id, ver, photo, server, vk_hash):
    ''' Сохраняем загруженное изображение на сервере '''

    headers = {
        'Authorization': f'Bearer {token}'
        }
    params = {
        'group_id': group_id,
        'v': ver,
        'photo':  photo,
        'server':  server,
        'hash':  vk_hash,
        }
    url ='https://api.vk.com/method/photos.saveWallPhoto'
    response = requests.post(url, headers=headers, params=params)
    response.raise_for_status()
    is_response_good(response)
    response_params = response.json()
    owner_id = response_params["response"][0]["owner_id"]
    media_id = response_params["response"][0]["id"]
    return owner_id, media_id


def publish_comic_to_vk(token, group_id, owner_id, media_id, msg, ver):
    ''' Публикуем комикс в сообществе фанатов в vk '''

    headers = {
        'Authorization': f'Bearer {token}'
        }
    vk_params = {
        'v': ver,
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'message': msg,
        'attachments': f'photo{owner_id}_{media_id}',
        }
    url = 'https://api.vk.com/method/wall.post'
    response = requests.post(url, headers=headers, params=vk_params)
    response.raise_for_status()
    is_response_good(response)
    return response.json()


if __name__ == '__main__':
    ''' Собираем все вместе и выводим идентификатор нового поста в vk '''

    load_dotenv()
    vk_user_id = os.environ["VK_USER_ID"]
    vk_token = os.environ['VK_ACCESS_TOKEN']
    vk_ver = '5.131'
    vk_group_id = os.environ['VK_XKCD_ID']
    img_filename, comment = download_random_comic()
    try:
        upload_url = get_upload_server_addr(vk_token, vk_group_id, vk_ver)
        photo, server, vk_hash = upload_photo(upload_url, img_filename)
        owner_id, media_id = save_wall_photo(vk_token, vk_group_id, vk_ver,
            photo, server, vk_hash)
        post_id = publish_comic_to_vk(vk_token, vk_group_id, owner_id, media_id,
            comment, vk_ver)
        print(post_id)
    except VKException as error:
        print(error)
    finally:
        if os.path.isfile(img_filename):
            os.remove(img_filename)
