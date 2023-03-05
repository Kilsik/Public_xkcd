import requests
import random
import os
import sys

from urllib.parse import urlparse
from pathlib import Path
from dotenv import load_dotenv


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


def get_upload_server_addr(headers, params):
    ''' Получаем адрес сервера для загрузки комикса в vk '''

    vk_url = 'https://api.vk.com/method/photos.getWallUploadServer'
    response = requests.get(vk_url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def upload_photo(url, img_filename):
    ''' Загружаем картинку комикса на сервер vk '''

    with open(img_filename, 'rb') as file:
        vk_file = {
            'photo': file,
            }
        response = requests.post(url, files=vk_file)
    response.raise_for_status()
    return response.json()


def save_wall_photo(headers, params, photo, server, vk_hash):
    ''' Сохраняем загруженное изображение на сервере '''

    params['photo'] = photo
    params['server'] = server
    params['hash'] = vk_hash
    url ='https://api.vk.com/method/photos.saveWallPhoto'
    response = requests.post(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def publish(headers, group_id, owner_id, media_id, msg, ver):
    ''' Публикуем комикс в сообществе фанатов в vk '''

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
    return response.json()


if __name__ == '__main__':
    ''' Собираем все вместе и выводим идентификатор нового поста в vk '''

    load_dotenv()
    vk_user_id = os.environ["VK_USER_ID"]
    vk_token = os.environ['VK_ACCESS_TOKEN']
    vk_ver = '5.131'
    vk_group_id = os.environ['VK_XKCD_ID']
    img_filename, comment = download_random_comic()
    vk_headers = {
        'Authorization': f'Bearer {vk_token}'
        }
    vk_params = {
        'group_id': vk_group_id,
        'v': vk_ver,
        }
    wall_upload_server = get_upload_server_addr(vk_headers, vk_params)
    try:
        upload_url = wall_upload_server['response']['upload_url']
    except KeyError:
        print(wall_upload_server['error']['error_msg'])
        os.remove(img_filename)
        sys.exit()
    try:
        upload_response = upload_photo(upload_url, img_filename)
    except (FileNotFoundError, KeyError):
        print(f'Image file {img_filename} not found')
    finally:
        os.remove(img_filename)
    photo = upload_response["photo"]
    server = upload_response["server"]
    vk_hash = upload_response["hash"]
    save_response = save_wall_photo(vk_headers, vk_params, photo, server,
        vk_hash)
    owner_id = save_response["response"][0]["owner_id"]
    media_id = save_response["response"][0]["id"]
    post_id = publish(vk_headers, vk_group_id, owner_id, media_id, comment,
        vk_ver)
    print(post_id)