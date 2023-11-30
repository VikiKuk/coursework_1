import json
import time
import requests
from datetime import datetime
import sys

class VK:

    def __init__(self, access_token, user_id, version='5.131'):
       self.token = access_token
       self.id = user_id
       self.version = version
       self.params = {'access_token': self.token, 'v': self.version}

    def profile_photos(self):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id, 'album_id': 'profile'}
        response = requests.get(url, params={**self.params, **params})
        if 'error' in response.json():
            print("Возникла ошибка при работе с API VK. Пожалуйста, повторите запрос позже или напишите в поддержку.")
            sys.exit()
        if response.json()['response']['count'] == 0:
            print("Профиль не содержит фото. Не могу продолжить выполнение программы.")
            sys.exit()
        size_photo_vk = {
            'w': 1,
            'z': 2,
            'y': 3,
            'r': 4,
            'q': 5,
            'p': 6,
            'o': 7,
            'x': 8,
            'm': 9,
            's': 10
        }
        photo = []
        for i_items in response.json()['response']['items']:
            dic = {}
            user_photo_size = []
            dic['item_id'] = i_items['id']
            dic['timestamp'] = i_items['date']
            for i in i_items['sizes']:
                user_photo_size.append([i['type'], size_photo_vk[i['type']]])
            sorted_user_photo_size = sorted(user_photo_size, key=lambda x: x[1])
            dic['size'] = sorted_user_photo_size[0][0]
            for i in i_items['sizes']:
                if i['type'] == dic['size']:
                    dic['url'] = i['url']
            photo.append(dic)


        self.profile_likes(photo)

        file_name = {}
        for count_like in photo:
            if count_like['likes'] not in file_name.keys():
                file_name[count_like['likes']] = 1
            else:
                file_name[count_like['likes']] += 1
        file_name = dict(filter(lambda item: item[1]>1, file_name.items()))

        for likes_for_name in photo:
            if likes_for_name['likes'] in file_name.keys():
                likes_for_name['file_name'] = str(likes_for_name['likes']) + '_' + str(
                    datetime.utcfromtimestamp(likes_for_name['timestamp'])).replace(':', '_') + '.jpg'
            else:
                likes_for_name['file_name'] = likes_for_name['likes']

        final_list = []
        for list in photo:
            final_list.append({'file_name': list['file_name'], 'size': list['size']})
        with open('result.json', 'w') as json_file:
            json.dump(final_list, json_file)

        return photo

    def profile_likes(self, photo):
        url = 'https://api.vk.com/method/likes.getList'
        progress_bar = PROGRESSBAR(len(photo),'Загрузка лайков. ')
        progress_bar.progress()
        errors = []
        for m in photo:
            params = {'type': 'photo', 'owner_id': self.id, 'item_id': m['item_id'], 'page_url': m['url']}
            response = requests.get(url, params={**self.params, **params})
            if response.status_code in [200]:
                m['likes'] = response.json()['response']['count']
                time.sleep(100 / 1000.0)
                progress_bar.progress()
            else:
                errors.append(response.json()['message'])
                progress_bar.progress()
        if len(errors) != 0:
            print()
            print('При получении данных о лайках фото возникла проблема. Перечень ошибок:')
            for item in errors:
                print(item)
        else:
            print()
            print('Перечень лайков успешно получен.')


    def get_content(self, url):
        response = requests.get(url)
        content = response.content
        return content


class YANDEX:

    def __init__(self, access_token_ya, path):
        self.token = 'OAuth ' + access_token_ya
        self.headers = {'Authorization': self.token}
        self.path = path

    def create_folder(self):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {'path': self.path}
        response = requests.put(url, params=params, headers=self.headers)
        errors = []
        if response.status_code in [200, 201, 202, 409]:
            print('--------')
            print('Папка для фото успешно создана.')
        else:
            print(response)
            errors.append(response.json()['message'])
        if len(errors) != 0:
            print()
            print('--------')
            print('При создании папки возникли проблемы. Перечень ошибок:')
            for item in errors:
                print(item)

    def photo_to_yandex_upload(self, photo, vk):
        print('--------')
        progress_bar2 = PROGRESSBAR(len(photo),'Загрузка фото на Яндекс диск. ')
        progress_bar2.progress()
        errors = []
        for name in photo:
            params = {'path': self.path + '/' + str(name['file_name'])}
            response = requests.get('https://cloud-api.yandex.net/v1/disk/resources/upload',
                                   params=params,
                                   headers = self.headers)
            if response.status_code in [200, 201, 202]:
                url_for_upload = response.json()['href']
                content = vk.get_content(name['url'])
                response = requests.put(url_for_upload, content)
                if response.status_code in [200, 201]:
                    progress_bar2.progress()
                else:
                    errors.append(response.status_code)
                    progress_bar2.progress()
            else:
                errors.append(response.json()['message'])
                progress_bar2.progress()
        if len(errors) != 0:
            print()
            print('При загрузке возникли проблемы. Перечень ошибок:')
            for item in errors:
                print(item)
        else:
            print()
            print('Фото успешно загружены.')


class PROGRESSBAR:
    def __init__(self, count_items, name):
        self.count_items = count_items
        self.name = name
        self.n = 0

    def progress (self):
        if self.count_items == 0:
           print ('Не могу запустить прогресс бар.')
        else:
            sys.stdout.write("\r" + f'{self.name}Прогресс: {int(self.n/self.count_items*100)}%')
            self.n += 1


if __name__ == '__main__':

    access_token = 'vk_token'
    user_id = 'user_id'
    vk = VK(access_token, user_id)
    photo_with_likes = vk.profile_photos()

    access_token_ya = 'ya_token'
    path = 'VK_photo'
    ya = YANDEX(access_token_ya, path)
    ya.create_folder()
    ya.photo_to_yandex_upload(photo_with_likes, vk)



