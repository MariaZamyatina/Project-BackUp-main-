import time
import requests
from tqdm import tqdm
import json


class VK:
    def __init__(self, access_token_vk, user_id, count, version='5.131'):
        self.token_vk = access_token_vk
        self.id = user_id
        self.version = version
        self.count = int(count)
        self.params = {'access_token': self.token_vk, 'v': self.version}

    def get_users_photo(self, album_id):
        """ Метод возвращает словарь с фото профиля или стены пользователя ВК или сохраненные пользователем"""
        if album_id == 'all':
            url = 'https://api.vk.com/method/photos.getAll'
            params = {
                      'count': self.count,
                      'owner_id': self.id,
                      'no_service_albums': 1,
                      'extended': 1,
                      'photo_sizes': 1
                      }
        else:
            url = 'https://api.vk.com/method/photos.get'
            params = {
                      'count': self.count,
                      'owner_id': self.id,
                      'album_id': album_id,
                      'extended': 1,
                      'photo_sizes': 1
                      }
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def get_headers(self):
        """ Метод возвращает заголовок запроса"""
        return {'Content-Type': 'application/json', 'Authorization': f'OAuth {self.token_vk}'}

    def get_photos(self, album_id):
        """ Метод возвращает словарь с названиями и URL фото """
        dict_photo = {'url': [], 'name': [], 'likes_count': [], 'size': []}
        user_photos = vk.get_users_photo(album_id)
        if 'error' in user_photos.keys():
            print('access denied')
            return False
        if user_photos.get('response').get('count') == 0:
            print('нет фото')
            return False
        for item in user_photos.get('response').get('items'):
            dict_photo['url'].append(item.get('sizes')[-1].get('url'))
            dict_photo['size'].append(item.get('sizes')[-1].get('type'))
            if item.get('likes').get('count') in dict_photo.get('likes_count'):
                dict_photo['name'].append(str(item.get('likes').get('count')) + '_' + str(item.get('date')))
            else:
                dict_photo['name'].append(str(item.get('likes').get('count')))
            dict_photo.get('likes_count').append(item.get('likes').get('count'))
        return dict_photo


class YaDisk:
    def __init__(self, access_token_ya):
        self.token_ya = access_token_ya
        self.params = {'access_token': self.token_ya}

    def get_headers(self):
        """ Метод возвращает заголовок запроса"""
        return {'Content-Type': 'application/json', 'Authorization': f'OAuth {self.token_ya}'}

    def get_link_YaDisk(self, disk_file_path):
        """Метод возвращает путь с яндекс диска до файла"""
        url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = self.get_headers()
        p = {'path': disk_file_path, 'overwrite': 'true'}
        response = requests.get(url, headers=headers, params=p)
        return response.json()

    def create_folder(self, folder):
        """ Метод создает папку на яндекс диске"""
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {'path': folder, 'overwrite': 'true'}
        requests.put(url, headers=headers, params=params)

    def upload_photos_to_disk(self, folder, album_id):
        dict_photo = vk.get_photos(album_id)
        print(dict_photo)
        if dict_photo is False:
            print('error')
            return False
        else:
            ya.create_folder(folder)
            list_photos = []
            list_photos_json = []
            i = 0
            length = len(dict_photo.get('name'))
            while i <= length - 1:
                list_photos.append([dict_photo.get('name')[i],
                                    dict_photo.get('url')[i]])
                i += 1
            del dict_photo['url']
            del dict_photo['likes_count']
            list_photos_json.append(dict_photo)

            with open('result.json', 'w', encoding='utf-8') as file:
                json.dump(list_photos_json, file, ensure_ascii=False, indent=4)
            for data in tqdm(list_photos, desc='Загрузка фото: ', unit=' photo ',
                             unit_scale=1, leave=False, colour='red'):
                time.sleep(0.05)
                response_file = requests.get(data[1], params={**self.params})
                href = self.get_link_YaDisk(disk_file_path=f'{folder}/{data[0]}.jpg').get('href', '')
                requests.put(href, data=response_file.content)
            print('Фото из ВК записаны на яндекс диск успешно. Данные фото записаны в result.json')


if __name__ == '__main__':
    access_token_vk = input('Введите ТОКЕН ВК: ')
    vk_user_id = input('Введите id пользователя ВК: ')
    access_token_ya = input('Введите ТОКЕН YaDisk: ')
    dict_album_id = {'wall': 'a', 'profile': 'b', 'saved': 'c', 'all': 'd'}
    while True:
        var = input('- записать фото со стены профиля: a \n - записать фото профиля: b \n '
                    '- записать сохраненные пользователем фотографии: c \n '
                    ' - записать фотографии и из других альбомов: d \n'
                    'Откуда будете сохранять фото: ')
        count = 0
        album_id = ''
        for k, v in dict_album_id.items():
            if var == v:
                album_id = k
                count += 1
        if count != 1:
            print('error')
            break
        variant = input('По умолчанию сохраняется не больше 5-ти фотографий. '
                        'Нужно сохранить другое количество? (yes/no): ')
        count = ''
        if variant == 'yes':
            count = input('Введите нужное количество фотографий: ')
        elif variant == 'no':
            count = 5
        else:
            print('error')
            break

        vk = VK(access_token_vk, vk_user_id, count)
        folder = input('Введите название папки, в которую будет производиться загрузка фото: ')
        ya = YaDisk(access_token_ya)
        ya.upload_photos_to_disk(folder, album_id)
        variant = input('Еще будете скачивать из VK? (yes/no): ')
        if variant != 'yes':
            break
