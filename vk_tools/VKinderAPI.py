import requests
import time
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from config import TOKEN_API #Получание токенов VkAPI
#from db.db_orm import *
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
            'fields': 'bdate',
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
                        'bdate': user['bdate'],
                        'status_code': 0,
                    })
        except KeyError:
            pass

        return user_info #Получен 1000 пользователей в соответсвии с заданными параметрами
                        #[{id_1: , 'first_name'_1: , 'last_name'_1: , 'bdate'_1: dd.mm.yyyy, 'status_code': },
                            #...
                        #, {id_n: , 'first_name'_n: , 'last_name'_n: , 'bdate'_n: dd.mm.yyyy, 'status_code': }]

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
            print(photos)
            for photo_info in photos['response']['items']:
                photo_url = photo_info['sizes'][2]['url']
                likes = photo_info['likes']['count']
                info_about_photo.append({
                    'url': photo_url,
                    'id': photo_info['id'],
                    'owner_id': photo_info['owner_id'],
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

    def _send_photoMessage(self, info_user: dict, id: int, photos: dict) -> None:
        person_id = f'https://vk.com/id' + str(info_user['id']) + '/'
        first_name = info_user['first_name']
        last_name = info_user['last_name']
        bdate = info_user['bdate']
        self._sender(id, 'Вот нашел фотографии!')
        self._sender(id, f'Вот ссылка на профиль: {person_id}\n'
                         f'Зовут: {first_name} {last_name}\n'
                         f'Дата рождения: {bdate}')
        count = {
            0: 'Первая',
            1: 'Вторая',
            2: 'Третья',
        }
        count_ = 0
        for photo in photos:
            count_photo = count[count_]
            step = photo['url']
            id_ = photo['id']
            owner_id = photo['owner_id']
            print(id_, owner_id)
            print(photo)
            self.vk_bot.method("messages.send",
                               {"peer_id": id, "message": f'{count_photo} фотография', "attachment": f'photo{owner_id}_{id_}',
                                "random_id": 0})
            count_ += 1

    def run(self):
        self.log = False
        self.start = False
        api = VKinderAPI(TOKEN_API)
        DB_user = []

        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    msg = event.text.lower()
                    id = event.user_id
                    date = datetime.now()
                    ######################
                    #add_contacts(id, date) # Запись пользователя, первый контакт с ботом # Метка -------------------
                    ######################
                    print(id)
                    firstName_User = api.get_myself(id=id)
                    ## postDB_user(id, timeConnect) - 1 Метка функции записи пользователя бота в бд # Метка -------------------

                    if msg == '/старт' or msg == 'старт': #Запуск бота
                        keyboard = VkKeyboard(one_time=True)
                        keyboard.add_button('Показать', VkKeyboardColor.POSITIVE)

                        users = api._get_users()
                        city = api.city_user['title']

                        count = 0  # Счетчик для демонстрации работоспособности
                        info_user = users[count]

                        self._sender(id, f'Привет, {firstName_User}!\nЯ бот для поиска людей по параметрам твоего профиля.\n'
                                         f'Вот что мы нашли:\n'
                                         f'- Твой город: {city}\n'
                                         f'- Твой пол: {self.select(var_sex=api.sex_user)}\n'
                                         f'- Твоя дата рождения: {api.bdate_user}', keyboard=keyboard)

                    if (msg == '/показать' or msg == 'показать')and self.log == False and info_user['status_code'] == 0: # Метка -------------------
                        ##############################
                        #add_person(info_user['id'], 0) # Метка -------------------
                        ##############################
                        if info_user['status_code'] == 0: # Метка -------------------
                            photos = api.get_photos(user=info_user)
                        else:
                            count += 1
                            info_user = users[count]
                            photos = api.get_photos(user=info_user)

                        self._send_photoMessage(info_user=info_user, id=id, photos=photos)
                        time.sleep(0.35)
                        self.log = True
                        keyboard = VkKeyboard(one_time=False)
                        button = ['История', 'Убрать', 'Добавить','Далее']
                        button_color = [VkKeyboardColor.PRIMARY, VkKeyboardColor.NEGATIVE, VkKeyboardColor.SECONDARY,
                                        VkKeyboardColor.POSITIVE]

                        for btn, btn_color in zip(button, button_color):
                            keyboard.add_button(btn, btn_color)

                        self._sender(id, 'Выберите дейтские', keyboard)

                    elif (msg == '/далее' or msg == 'далее') and self.log == True:

                        keyboard = VkKeyboard(one_time=False)
                        button = ['История', 'Убрать', 'Добавить', 'Далее']
                        button_color = [VkKeyboardColor.PRIMARY, VkKeyboardColor.NEGATIVE, VkKeyboardColor.SECONDARY,
                                        VkKeyboardColor.POSITIVE]

                        for btn, btn_color in zip(button, button_color):
                            keyboard.add_button(btn, btn_color)

                        ##############################
                        #restatus(info_user['id'], 1) # Метка -------------------
                        ##############################
                        # get_user_fromBD() - получение одного пользователя из БД с нулевым статусом
                        count += 1
                        info_user = users[count]
                        ##############################
                        #add_person(info_user['id'], 0)
                        ##############################
                        if info_user['status_code'] == 0 and info_user['id'] not in DB_user:
                            photos = api.get_photos(user=info_user)
                            self._send_photoMessage(info_user=info_user, id=id, photos=photos)
                            info_user['status_code'] = 1
                            print(info_user)
                            DB_user.append(info_user['id'])
                            time.sleep(0.35)
                        else:
                            while info_user['id'] in DB_user: # Метка -------------------
                                count += 1
                                info_user = users[count]
                            if info_user['id'] not in DB_user:
                                photos = api.get_photos(user=info_user)
                                self._send_photoMessage(info_user=info_user, id=id, photos=photos)
                                info_user['status_code'] = 1
                                print(info_user)
                                ##############################
                                #add_person(info_user['id'], 1)
                                ##############################
                                DB_user.append(info_user['id']) # Метка -------------------
                                time.sleep(0.35)

                    elif msg == '/добавить' or msg == 'добавить':
                        keyboard = VkKeyboard()
                        button = ['История', 'Убрать', 'Далее']
                        button_color = [VkKeyboardColor.PRIMARY, VkKeyboardColor.NEGATIVE, VkKeyboardColor.POSITIVE]

                        for btn, btn_color in zip(button, button_color):
                            keyboard.add_button(btn, btn_color)

                        self._sender(id, 'Выберите действие', keyboard)
                        ############################
                        #restatus(info_user['id'], 2)
                        #############################

                    elif msg == '/убрать' or msg == 'убрать':
                        keyboard = VkKeyboard()
                        button = ['История', 'Добавить', 'Далее']
                        button_color = [VkKeyboardColor.PRIMARY, VkKeyboardColor.SECONDARY, VkKeyboardColor.POSITIVE]

                        for btn, btn_color in zip(button, button_color):
                            keyboard.add_button(btn, btn_color)

                        self._sender(id, 'Выберите дейтские', keyboard)
                        ############################
                        #restatus(info_user['id'], 2)
                        #############################

                    elif msg == '/история' or msg == 'история':
                        keyboard = VkKeyboard(one_time=True)
                        button = ['Далее']
                        keyboard.add_button('Далее', VkKeyboardColor.POSITIVE)

                        self._sender(id, 'Выберите дейтские', keyboard)
                        ##################
                        #get_user_fromDB(1)
                        ###################