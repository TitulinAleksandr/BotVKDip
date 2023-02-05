import requests
import time
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from config import TOKEN_API #Получание токенов VkAPI

user_status = {}

class VKinderAPI:
    def __init__(self, TOKEN_, version='5.131'):
        self.token = TOKEN_
        self.version = version
        self.param = {'access_token': self.token, 'v': self.version}
        self.users = []

    def get_myself(self, id):
        url = 'https://api.vk.com/method/users.get'

        self.id = id

        param = {
            'user_ids': self.id,
        }

        response = requests.get(url, params={**self.param, **param})

        return response.json()['response'][0]

    def _get_users(self, sex=1, count=20, age_from=25) -> dict: #Получение пользователей в соответствии с параметрами
        url = 'https://api.vk.com/method/users.search'
        user_info = []

        params = {
            'count': count,
            'sex': sex,
            'status': 1,
            'age_from': age_from,
            'has_photo': 1,
        }
        response = requests.get(url, params={**self.param, **params})
        users = response.json()
        try:
            for user in users['response']['items']:
                if user['is_closed'] == False:
                    user_info.append({
                        'id': user['id'],
                        'first_name': user['first_name'],
                        'last_name': user['last_name'],
                        'status_code': 0,
                    })
        except KeyError:
            pass

        return user_info #Получен №#  #

    def _sorted_photo(self, photos_info: list) -> list: #Сортировка фотографий по количеству лайков
        return sorted(photos_info, key=lambda x: x['likes'], reverse=True)

    def get_photos(self, sex=0, count=10, age_from=18) -> dict: #Получение фотографий каждого найденого пользователя
        url = 'https://api.vk.com/method/photos.get'
        user_photos = {}
        photos = {}
        users = self._get_users(sex, count, age_from)
        for user in users:
            if user['status_code'] == 0:
                info_about_photo = []
                params = {
                    'owner_id': user['id'],
                    'album_id': 'profile',
                    'count': 3,
                    'extended': 1,
                    'feed_type': 'photo',
                }
                response = requests.get(url, params={**self.param, **params})
                photos = response.json()
                photos_ = {}
                step_ = []
                for photo_info in photos['response']['items']:
                    photo_url = photo_info['sizes'][2]['url']
                    likes = photo_info['likes']['count']
                    info_about_photo.append({
                        'url': photo_url,
                        'likes': likes,
                    })
                    user_photos[user['id']] = self._sorted_photo(info_about_photo)[0:3]
                user['status_code'] = 1
            time.sleep(0.25)
        return user_photos

class VkBot(VKinderAPI): #Класс бота
    def __init__(self, token_bot):
        super().__init__(self)
        self.vk_bot = vk_api.VkApi(token=token_bot)
        self.session = self.vk_bot.get_api()
        self.longpoll = VkLongPoll(self.vk_bot)

    def _sender(self, id, text, keyboard=None): # Метод отправки сообщения от бота
        dict_msg = {
            'user_id': id,
            'message': text,
            'random_id': 0
        }
        if keyboard != None:
            dict_msg["keyboard"] = keyboard.get_keyboard()

        self.vk_bot.method('messages.send', dict_msg)


    def select(self, var_sex, var_age): # Перевод введенных данных в параметры для поиска в API
        sex = {'мужчина': 0,
               'женщина': 1,
               'неважно': 2}
        age = int(var_age)
        return sex[var_sex], age

    def run(self):
        self.sex = None
        self.age = None
        self.log = False
        self.start = False
        api = VKinderAPI(TOKEN_API)

        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    msg = event.text.lower()
                    id = event.user_id

                    if msg == '/старт':
                        self._sender(id, 'Введите пол и возраст\nПример: Женщина, 25')
                        self.start = True

                    elif msg and self.start and not self.log:
                        try :
                            self.sex, self.age = msg.split(',')
                        except ValueError:
                            self.sex, self.age = msg.split()
                        self.sex, self.age = self.select(self.sex, self.age)

                        photos = api.get_photos(sex=self.sex, count=100, age_from=self.age)
                        for id_, urls in photos.items():
                            person_id = f'https://vk.com/id' + str(id_) + '/'
                            self._sender(id, f'{person_id}')
                            self.vk_bot.method("messages.send",
                                               {"peer_id": id, "message": person_id, "attachment": urls[0]['url'],
                                                "random_id": 0})
                            time.sleep(0.25)





