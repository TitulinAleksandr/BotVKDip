def search_person(id): # кукла функуции берущей id vk и отдающей список id vk подобных персонажей (для закидывания в базу на рассмотрение)
   new_id = (id, '123453', '23456', '36812', '23145', '76237')
   return new_id

def postDB_user(id, status_code: dict):  #add_user() Функция добавляет пользователя бота с id и статусом
    pass   #
# ____________________
# м: ? зачем dict (не понял логику)
# ____________________
def users_DB(id, status_code): #add_persons() Функция добавляет в БД найденных "персонажей"
    pass
# ____________________
# м: ok - add_person(id, st): присваивает персонажу(кандидату) статус и привязывает к vk id таблице - from db.db_orm import add_person
# ____________________
def get_user_fromDB(): #post_user() Функция возвращает id случайного (можно и не случайного) "персонажа"
    pass    # Условие, функция при последующем вызове возвращает нового пользователя со статусом 0
# ____________________
# м: ok - from db.db_orm import get_user_fromDB
# генератор:
# get_user_fromDB(status) - выдает id из DB по статусу
# [!] синтаксис генераторов:
#                zzz = get_user_fromDB(0) - одно обращение, а дальше перебор:
#                print(next(zzz)) ... >id1
#                print(next(zzz)) ... >id2
#                print(next(zzz)) - без next() выдаст <generator object get_user_fromDB at ...>
# ____________________
def restatus(id, num_status): # Функция меняет у пользователя с переданным id статус код на указанный num_status
    pass
# ____________________
# м: ok - restatus(uid, status): - получает id vk - меняет статус на нужный  - from db.db_orm import restatus
# ____________________
# Примечание, после функции указано альтернативное название функции