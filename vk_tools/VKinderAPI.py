import requests
import time
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from config import TOKEN_API #Получание токенов VkAPI
from datetime import datetime

user_status = {}

class VKinderAPI:
    def __init__(self, TOKEN_, version='5.131'):
        self.token = TOKEN_
        self.version = version
        self.param = {'access_token': self.token, 'v': self.version}
        self.users = []

    def get_myself(self, id): #Метод принимает id пользователя и вытаскивает данные о рождении, городе и гендере
        url = 'https://api.vk.com/method/users.get'

        self.id = id

        param = {
            'user_ids': self.id,
        }

        response_bdate = requests.get(url, params={**self.param, **param, 'fields': 'bdate'})
        response_city = requests.get(url, params={**self.param, **param, 'fields': 'city'})
        response_sex = requests.get(url, params={**self.param, **param, 'fields': 'sex'})

        self.bdate_user = response_bdate.json()['response'][0]['bdate'] #
        self.city_user = response_city.json()['response'][0]['city'] # {'id': 'city_id', 'title': 'name_city'}
        self.sex_user = response_sex.json()['response'][0]['sex'] # 0 - male, 1 - female, 2 - nothing
        print(response_city.json())
        return response_sex.json()['response'][0]['first_name']

    def _bdate(self): # Получение возраста с допустимой погрешностью
        self.date_now = str(datetime.now()).split()[0].split('-')[0]
        bd_user = str(self.bdate_user).split('.')[2]
        return int(self.date_now) - int(bd_user) - 1

    def _sex(self):
        if self.sex_user == 0:
            return 1
        elif self.sex_user == 1:
            return 0
        else:
            return 2

    def _get_users(self) -> dict: #Получение пользователей в соответствии с параметрами полученные в результате get_myself()
        url = 'https://api.vk.com/method/users.search'
        user_info = []

        params = {
            'count': 1000,
            'sex': self._sex(),
            'city': self.city_user['id'],
            'status': 1,
            'age_from': 18,
            'age_to': self._bdate(),
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

        return user_info #Получен 1000 пользователей в соответсвии с заданными параметрами
                        #[{id_1: , 'first_name'_1: , 'last_name'_1: , 'status_code': },
                            #...
                        #, {id_n: , 'first_name'_n: , 'last_name'_n: , 'status_code': }]

    def _sorted_photo(self, photos_info: list) -> list: #Сортировка фотографий по количеству лайков
        return sorted(photos_info, key=lambda x: x['likes'], reverse=True)

    def select(self, var_sex):  # Перевод введенных данных в параметры для поиска в API
        sex = {0: 'мужской',
               1: 'женский',
               2: 'не указано'}
        return sex[var_sex]

    def get_photos(self, user: dict) -> dict: #Получение фотографий каждого найденого пользователя по id
        url = 'https://api.vk.com/method/photos.get'
        user_photos = {}
        if user['status_code'] == 0:
            info_about_photo = []
            params = {
                'owner_id': user['id'],
                'album_id': 'profile',
                'extended': 1,
                'feed_type': 'photo',
                'count': 10,
            }
            response = requests.get(url, params={**self.param, **params})
            photos = response.json()

            for photo_info in photos['response']['items']:
                photo_url = photo_info['sizes'][2]['url']
                likes = photo_info['likes']['count']
                info_about_photo.append({
                    'url': photo_url,
                    'likes': likes,
                })
                user_photos[user['id']] = self._sorted_photo(info_about_photo)[0:3]

        return user_photos[user['id']] #[{'url': 'link//', 'likes': likes}, ...]

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

    def run(self):
        self.log = False
        self.start = False
        api = VKinderAPI(TOKEN_API)

        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    msg = event.text.lower()
                    id = event.user_id
                    print(id)
                    firstName_User = api.get_myself(id=id)
                    ## postDB_user(id, timeConnect) - 1 Метка функции записи пользователя бота в бд
                    # users_BD() - Запись всех найденых пользователей в БД
                    users = api._get_users()
                    city = api.city_user['title']

                    count = 0 # Счетчик для демонстрации работоспособности

                    if msg == '/старт': #Запуск бота
                        self._sender(id, f'Привет, {firstName_User}!\nЯ бот для поиска людей по параметрам твоего профиля.\n'
                                         f'Вот что мы нашли:\n'
                                         f'- Твой город: {city}\n'
                                         f'- Твой пол: {self.select(var_sex=api.sex_user)}\n'
                                         f'- Твой дата рождения: {api.bdate_user}')

                    if msg == '/показать' and self.log == False:
                        # get_user_fromBD() - получение одного пользователя из БД с нулевым статусом
                        info_user = users[count]
                        if info_user['status_code'] == 0:
                            photos = api.get_photos(user=info_user)
                        else:
                            count += 1
                            info_user = users[count]
                            photos = api.get_photos(user=info_user)

                        for user_photo in photos:
                            person_id = f'https://vk.com/id' + str(info_user['id']) + '/'
                            self._sender(id, f'Вот нашли')
                            print(user_photo)
                            self.vk_bot.method("messages.send",
                                               {"peer_id": id, "message": person_id, "attachment": user_photo['url'],
                                                "random_id": 0})

                            time.sleep(0.35)
                            self.log = True

                    elif msg == '/далее' and self.log == True:
                        # get_user_fromBD() - получение одного пользователя из БД с нулевым статусом
                        info_user['status_code'] = 1
                        count += 1
                        info_user = users[count]
                        if info_user['status_code'] == 0:
                            photos = api.get_photos(user=info_user)
                        else:
                            count += 1
                            info_user = users[count]
                            photos = api.get_photos(user=info_user)

                        for user_photo in photos:
                            person_id = f'https://vk.com/id' + str(info_user['id']) + '/'
                            self._sender(id, f'{person_id}')
                            self._sender(id, f'Вот нашли')
                            self.vk_bot.method("messages.send",
                                               {"peer_id": id, "message": person_id, "attachment": user_photo['url'],
                                                "random_id": 0})
                            print(info_user['status_code'])
                            time.sleep(0.35)
