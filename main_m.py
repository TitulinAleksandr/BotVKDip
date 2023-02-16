from random import randrange
from box.vk_ut import token # в vk_ut.py (папка box) лежит токен VK
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import psycopg2
from db.db_orm import \
    add_vkid as add_id, \
    search_id as s_id, \
    add_contacts as add_c,\
    add_person as add_p, \
    search_count_persons as s_st, \
    restatus as rs, \
    list_person_status as list_ps, \
    search_vkid as s_vkid, \
    get_user_fromDB
from vk_tools.vk_tools import search_person as s_p
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

if __name__ == '__main__':
    vk = vk_api.VkApi(token=token)
    longpoll = VkLongPoll(vk)

    def write_msg(user_id, message):
        vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7),})

    for event in longpoll.listen(): #закинули "удочку"
        if event.type == VkEventType.MESSAGE_NEW:
            msg = event.text.lower()
            print(event.type)
            if msg == '/старт' or msg == 'старт':  # Запуск бота
                print('пуск клавиатуры')
                keyboard = VkKeyboard(one_time=True)
                keyboard.add_button('Показать', VkKeyboardColor.POSITIVE)

            if event.to_me: # "клюнуло" - кто-то сделал запись в чате
                request = event.text
                print(f'{event.datetime}   id{event.user_id} : {request}') #время записи в чате +idvk +текст
                x = str(event.user_id)

                if not s_id(x): #заносим id vk в базу если его там нет
                    add_id(event.user_id)
                    print("добавили id в базу")
                else: print("уже было")

                add_c(x, event.datetime) #записываем в таблицу контактов время чата и привязываем к vk id
                print("добавили в базу контактов")

                for i in s_p(x): #заброс списком новых id (условно: передали id написавшего в чат,
                    # с него функция делает отпечаток и возвращает список удовлетворяющий этому отпечатку)
                    s = 0
                    add_p(i, s) #заносим в базу статус нового персонажа и привязываем к vk id

                for i in [0,1,2,3,4]:
                    print(f'status {i}: {s_st(i)}') #вывод количества людей в базе с разными статусами(0-4)

                rs('23456', 1) #функция изменяющая статус в базе по id vk
                rs('76237', 4)

                stat = 0
                x = list_ps(stat) #вывод списка людей (vk id) с определенным статусом (0)
                for i in x:
                    print(f'status {stat} vk id{i}')

                print('-----------')
                zzz = get_user_fromDB(0)
                for z in zzz:
                    print(z)






