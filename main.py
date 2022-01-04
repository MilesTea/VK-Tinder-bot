from random import randrange
import datetime
import vk
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from pprint import pprint
import requests

params = {
    'bruh': 'bruh'
}

token = '45bca88e142e2816d4e1bf4b2796efe5c19f2c46445c2fd4d11db4a652e51a7965f1ca576906cad6ce46e'

vko = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vko)


settings = {
    'age_range': 2,

}

def get_info(user_id):
    return vko.method('users.get', {'user_id': user_id, 'fields': 'sex,bdate,city,country,relation'})


def get_server_time() -> list[str]:
    return datetime.date.fromtimestamp(vko.method('utils.getServerTime')).strftime('%d.%m.%Y').split('.')


def age_meter(date1: list, date2: list) -> int:
    """
    :param date1: в формате [D, M, YYYY]
    :param date2: в формате [D, M, YYYY]
    :return: int разницу в годах
    """
    day = int(date1[0]) - int(date2[0])
    month = int(date1[1]) - int(date2[1])
    if day < 1:
        month -= 1
    year = int(date1[2]) - int(date2[2])
    if month < 1:
        year -= 1
    return int(year)

def search(params, settings):
    age_from = params['age'] - settings['age_range']
    age_to = params['age'] + settings['age_range']
    if params['sex'] == 1: sex_params = 2
    elif params['sex'] == 2: sex_params = 1
    else: sex_params = 0
    final_params = {'age_from': age_from, 'age_to': age_to, 'sex': sex_params}
    final_params['city'] = params['city']
    pprint(final_params)
    ids = vk.ids_from_users_search(vk.users_search(final_params))
    users_dict = dict()
    for id in ids:
        users_dict[id] = vk.get_photos(id)
    return users_dict


def write_msg(user_id, message, optional_params=None):
    if optional_params is None:
        optional_params = {}
    vko.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7),
                                 **optional_params})

def wait_for_response(user_id):
    for new_event in longpoll.listen():
        if new_event.type == VkEventType.MESSAGE_NEW and new_event.to_me and new_event.user_id == user_id:
            new_variable = new_event.text
            return new_variable

waiting = False
waiting_from = None
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:

        if event.to_me:
            request = event.text.lower()

            if request == "привет":
                write_msg(event.user_id, f"Хай, {event.user_id}")
            elif request == 'поиск':
                bruh = search(search_params, settings)
                pprint(bruh)
                for i, user in enumerate(bruh):
                    message = f'https://vk.com/id{user}'
                    photos = list()
                    for attachment in bruh[user]:
                        photos.append(attachment)
                    photos = ','.join(photos)
                    if photos:
                        write_msg(event.user_id, message, optional_params={'attachment': photos})
            elif request == 'инфо':
                info = get_info(event.user_id)[0]
                search_params = dict()
                bdate, sex, city, occ = [None for i in range(4)]
                if 'bdate' in info:
                    now = get_server_time()
                    bdate = info['bdate'].split('.')
                    if len(bdate) == 3:
                        age = age_meter(get_server_time(), bdate)
                        # bdate = datetime.date(int(bdate[2]), int(bdate[1]), int(bdate[0]))
                        # age = get_server_time() - bdate
                        # print(age)
                        search_params['age'] = age
                if 'sex' in info:
                    search_params['sex'] = info['sex']
                if 'city' in info:
                    search_params['city'] = info['city']['id']
                if 'relation' in info:
                    search_params['relation'] = info['relation']
                # else:
                #     write_msg(event.user_id, 'Введите свой статус')
                #     occ = wait_for_response(event.user_id)
                us = search_params
                print(us)
                write_msg(event.user_id, us)

            elif request == "пока":
                write_msg(event.user_id, "Пока((")
            elif request == 'тест':
                print(type(get_server_time()))
            else:
                write_msg(event.user_id, "Не поняла вашего ответа...")