import requests
import random
import os

from urllib.parse import urlparse
from pathlib import Path
from dotenv import load_dotenv


def download_comic():
    ''' Скачиваем случайный комикс '''

    url_last_img = 'https://xkcd.com/info.0.json'
    response = requests.get(url_last_img)
    response.raise_for_status()
    last_num = response.json()['num']
    select_num = random.randint(1, last_num)
    url = f'https://xkcd.com/{select_num}/info.0.json'
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
    return {'img_filename': img_filename, 'comment': comment}

def get_photo_adr(token, group_id, ver):
    ''' Получаем адрес сервера для загрузки комикса в vk '''

    vk_headers = {
        'Authorization': f'Bearer {token}'
        }
    vk_params = {
        'v': ver,
        'group_id': group_id
        }
    vk_url = 'https://api.vk.com/method/photos.getWallUploadServer'
    response = requests.get(vk_url, headers=vk_headers, params=vk_params)
    response.raise_for_status()
    return response.json()['response']['upload_url']

def upload_photo(url, photo):
    ''' Загружаем картинку комикса на сервер vk '''

    with open(photo, 'rb') as file:
        vk_file = {
            'photo': file,
            }
        response = requests.post(url, files=vk_file)
        response.raise_for_status()
    return response.json()

def save_wall_photo(token, group_id, upload_data, ver):
    ''' Сохраняем загруженное изображение на сервере '''

    photo = upload_data["photo"]
    server = upload_data["server"]
    vk_hash = upload_data["hash"]
    vk_headers = {
        'Authorization': f'Bearer {token}'
        }
    vk_params = {
        'v': ver,
        'group_id': group_id,
        'photo': photo,
        'server': server,
        'hash': vk_hash,
        }
    url ='https://api.vk.com/method/photos.saveWallPhoto'
    response = requests.post(url, headers=vk_headers, params=vk_params)
    response.raise_for_status()
    return response.json()

def publish(token, group_id, upload_response, msg, ver):
    ''' Публикуем комикс в сообществе фанатов в vk '''

    owner_id = upload_response["response"][0]["owner_id"]
    media_id = upload_response["response"][0]["id"]
    vk_headers = {
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
    response = requests.post(url, headers=vk_headers, params=vk_params)
    response.raise_for_status()
    return response.json()

if __name__ == '__main__':
    ''' Собираем все вместе и выводим идентификатор нового поста в vk '''

    load_dotenv()
    vk_user_id = os.environ["VK_USER_ID"]
    vk_token = os.environ['VK_ACCESS_TOKEN']
    vk_ver = '5.131'
    vk_group_id = os.environ['VK_XKCD_ID']
    comic = download_comic()
    img_filename = comic['img_filename']
    comment = comic['comment']
    wall_upload_server = get_photo_adr(vk_token, vk_group_id, vk_ver)
    upload_response = upload_photo(wall_upload_server, img_filename)
    save_response = save_wall_photo(vk_token, vk_group_id, upload_response,
        vk_ver)
    post_id = publish(vk_token, vk_group_id, save_response, comment, vk_ver)
    os.remove(img_filename)
    print(post_id)