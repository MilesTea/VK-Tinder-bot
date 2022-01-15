from random import randrange
import datetime
import vk
import vk_api
import sql
from vk_api.longpoll import VkLongPoll, VkEventType
from pprint import pprint
import requests


"""keyboard = '''{
    "one_time": false,
    "inline": true,
    "buttons": [
        [
        {
        "action": {
            "type": "text",
            "label": "vladimir bruh",
            "payload": null
        },
        "color": "primary"
    }
    ]
    ]
}'''
keyboard = keyboard.replace(' ', '')
keyboard = keyboard.replace('\n', '')
print(keyboard)
"""

from vk_api.keyboard import VkKeyboard, VkKeyboardColor
main_keyboard = VkKeyboard(inline=True, one_time=False)
main_keyboard.add_button('Очистка', color=VkKeyboardColor.SECONDARY)
main_keyboard.add_button('Далее', color=VkKeyboardColor.PRIMARY)


start_keyboard = VkKeyboard(inline=True, one_time=False)
start_keyboard.add_button('Очистка', color=VkKeyboardColor.SECONDARY)
start_keyboard.add_button('Поиск', color=VkKeyboardColor.PRIMARY)


class VkLongPollImproved(VkLongPoll):
    """
    Попытка добавления очереди событий
    """

    def __init__(self, vk, wait=25, mode=vk_api.longpoll.DEFAULT_MODE,
                 preload_messages=False, group_id=None):
        super().__init__(vk, wait, mode, preload_messages, group_id)
        self.queue = list()

    def add_to_queue(self, event):
        """
        добавление события в очередь для последующей обработки
        :param event: event
        :return:
        """
        self.queue.append(event)

    def improved_listen(self):
        """
        работает также, как и self.listen, за исключением того, что сначала обрабатываются события из очереди self.queue
        :return: event
        """
        while True:
            # print('queue')
            if len(self.queue) >= 1:
                # print('queue in')
                for queued_event in self.queue:
                    yield queued_event
                self.queue.clear()
            # print('not queue')
            for event in self.check():
                # print(event)
                yield event


params = {
    'bruh': 'bruh'
}

token = '45bca88e142e2816d4e1bf4b2796efe5c19f2c46445c2fd4d11db4a652e51a7965f1ca576906cad6ce46e'

vko = vk_api.VkApi(token=token)
longpoll = VkLongPollImproved(vko)


token_url = 'https://oauth.vk.com/authorize?client_id=8039929&display=page&redirect_uri=https://oauth.vk.com/blank.html&response_type=token&v=5.131'
settings = {
    'age_range': 2,
    'relation': [1, 6, 0],
    'info': 'Этот бот умеет искать тебе вторую половинку\n'
            'Для начала работы с ним нажми "Поиск"\n'
            'Для очистки просмотренных пользователей нажми "Очистка"',
    'token_expired': 'Ваш токен устарел'
}


def get_server_time() -> list[str]:
    return datetime.date.fromtimestamp(vko.method('utils.getServerTime')).strftime('%d.%m.%Y').split('.')


def get_name(user_id) -> str:
    response = vko.method('users.get', {'user_ids': user_id})
    name = response[0]['first_name'] + ' ' + response[0]['last_name']
    return name


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


def read_info(event):
    info = vko.method('users.get', {'user_id': event.user_id, 'fields': 'sex,bdate,city,country,relation'})[0]
    search_params = dict()
    bdate, sex, city, occ = [None for i in range(4)]
    if 'bdate' in info:
        now = get_server_time()
        bdate = info['bdate'].split('.')
        if len(bdate) == 3:
            age = age_meter(get_server_time(), bdate)
            search_params['age'] = age
        else:
            write_msg(event.user_id, 'Введите ваш возраст')
            search_params['age'] = int(wait_for_response(event.user_id))
    else:
        write_msg(event.user_id, 'Введите ваш возраст')
        search_params['age'] = int(wait_for_response(event.user_id))
    if 'sex' in info:
        if info['sex'] in [1, 2]:
            search_params['sex'] = info['sex']
    else:
        write_msg(event.user_id, 'Введите ваш пол\nМ\\Ж')
        sex = wait_for_response(event.user_id)
        if sex == 'м':
            sex = 2
        elif sex == 'ж':
            sex = 1
        if sex in [1, 2]:
            search_params['sex'] = sex
    if 'city' in info:
        search_params['city'] = info['city']['id']
    # if 'relation' in info:
    #     search_params['relation'] = info['relation']
    # else:
    pprint(search_params)
    return search_params


def search_users(event, search_params, settings):
    age_from = search_params['age'] - settings['age_range']
    age_to = search_params['age'] + settings['age_range']
    if search_params['sex'] == 1: sex_params = 2
    elif search_params['sex'] == 2: sex_params = 1
    else: sex_params = 0
    final_params = {'age_from': age_from, 'age_to': age_to, 'sex': sex_params}
    final_params['city'] = search_params['city']
    pprint(final_params)
    ids = vk.ids_from_users_search(vk.users_search(final_params))
    users_dict = dict()
    for id in ids:
        users_dict[id] = vk.get_photos(id)
    for i, user in enumerate(users_dict):
        message = f'https://vk.com/id{user}'
        photos = list()
        for attachment in users_dict[user]:
            photos.append(attachment)
        photos = ','.join(photos)
        if photos:
            write_msg(event.user_id, message, optional_params={'attachment': photos})


def search_user(event, search_params, settings, offset=0):
    age_from = search_params['age'] - settings['age_range']
    age_to = search_params['age'] + settings['age_range']
    if search_params['sex'] == 1: sex_params = 2
    elif search_params['sex'] == 2: sex_params = 1
    else: sex_params = 0
    final_params = {'age_from': age_from, 'age_to': age_to, 'sex': sex_params}
    final_params['city'] = search_params['city']
    pprint(final_params)
    i = offset
    print(i)
    while True:
        print(i)
        while True:
            print(i)
            result = vk.users_search(final_params, count=1, offset=i)
            if result == 'error':
                message = f'токен просрочен, перейдите по ссылке: {token_url}'
                write_msg(event.user_id, message, keyboard=main_keyboard)
                return 'error'
            id = vk.id_from_users_search(result)
            print(id)
            i += 1
            if not Db.check(id):
                break
        photos_list = vk.get_photos(id)
        name = result['response']['items'][0]['first_name'] + ' ' + result['response']['items'][0]['last_name']
        message = f'{name}\nhttps://vk.com/id{id}'
        photos = ','.join(photos_list)
        try:
            if result['response']['items'][0]['relation'] in settings['relation']:
                free = True
            else:
                free = False
        except KeyError:
            free = True
        if photos and free:
            write_msg(event.user_id, message, keyboard=main_keyboard, optional_params={'attachment': photos})
            Db.add(id)
            return i
        else:
            i += 1


'''
    for i, user in enumerate(users_dict):
        message = f'https://vk.com/id{user}'
        photos = list()
        for attachment in users_dict[user]:
            photos.append(attachment)
        photos = ','.join(photos)
        if photos:
            write_msg(event.user_id, message, optional_params={'attachment': photos})
            Db.add(id[0])
        else:
'''


def write_msg(user_id, message, keyboard=start_keyboard, optional_params=None):
    if optional_params is None:
        optional_params = {}
    vko.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7),
                                 'keyboard': keyboard.get_keyboard(), **optional_params})


def wait_for_response(user_id):
    for new_event in longpoll.listen():
        if new_event.type == VkEventType.MESSAGE_NEW and new_event.to_me and new_event.user_id == user_id:
            new_variable = new_event.text.lower()
            return new_variable
        else:
            # print('added event')
            longpoll.add_to_queue(new_event)


def process(event):
    pass


if __name__ == "__main__":
    Db = sql.UsersDb()
    readed = False
    for event in longpoll.improved_listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                request = event.text.lower()

                if request == "start":
                    write_msg(event.user_id, f"Привет, {get_name(event.user_id)}\n{settings['info']}")
                    pprint(get_name(event.user_id))
                elif request == 'поиск':
                    if not readed:
                        search_params = read_info(event)
                        readed = True
                    offset = search_user(event, search_params, settings)
                # elif request == 'инфо':
                #     search_params = read_info(event)
                elif request == "далее":
                    print(offset)
                    search_user(event, search_params, settings, offset=offset)
                elif request == "очистка":
                    Db.delete_all()
                    write_msg(event.user_id, "Очистка выполнена")
                elif request == "пока":
                    write_msg(event.user_id, "Пока((")
                elif request == 'тест':
                    print(type(get_server_time()))
                else:
                    write_msg(event.user_id, "Не поняла вашего ответа...")
                    print(request)
