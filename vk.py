import time
import vk_api
import utils
import datetime
import random
import requests
from vk_api.longpoll import VkLongPoll, VkEventType
from pprint import pprint


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


base_url = 'https://api.vk.com/method/'


def get_top_photos(photos) -> list or None:
    """
    получение топ 3 фотографий пользователя по лайкам
    :param photos: список фотографий пользователя
    :return: список из 3 фотографий пользователя вида photoOwner_id_Id
    """
    if photos:
        response_sorted_photos = sorted(photos, key=lambda x: x['likes']['count'], reverse=True)
        response_top_photos = response_sorted_photos[0:3]
        top_photos = list()
        for photo in response_top_photos:
            top_photos.append('photo' + str(photo['owner_id']) + '_' + str(photo['id']))
        return top_photos
    else:
        return None


def filter_users(users) -> list:
    """
    отсеивание пользователей с закрытым профилем
    :param users: список пользователей
    :return: список пользователей с открытым профилем
    """
    if users:
        filtered_users = list()
        for user in users:
            if user['is_closed']:
                continue
            filtered_users.append(user)
        return filtered_users


class Bot:

    def __init__(self, user_token, group_token, group_id=None):
        self.vk = vk_api.VkApi(token=group_token)
        self.longpoll = VkLongPollImproved(vk=self.vk, group_id=group_id)
        self.user_token = user_token
        self.group_token = group_token
        self.base_params = {
            'access_token': user_token,
            'v': '5.131'
        }

    def update_user_token(self, new_user_token) -> None:
        """
        обновляет токен пользователя
        :param new_user_token: новый токен пользователя
        :return: None
        """
        self.user_token = new_user_token
        self.base_params['access_token'] = new_user_token

    def utils_get_server_time(self) -> list[str, str, str]:
        return datetime.date.fromtimestamp(self.vk.method('utils.getServerTime')).strftime('%d.%m.%Y').split('.')

    def messages_send(self, user_id, message, optional_params=None) -> None:
        """
        отправка сообщений
        :param user_id: id пользователя, которому нужно отправить сообщение
        :param message: сообщение
        :param optional_params: опциональные параметры(например, вложения)
        :return: None
        """
        if optional_params is None:
            optional_params = {}
        self.vk.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': random.randrange(10 ** 7),
                                         **optional_params})

    def users_search(self, search_params, offset=0, count=10) -> list or None:
        """
        Поиск пользователей по заданным параметрам
        :param search_params: параметры поиска
        :param offset: смещение поиска
        :param count: максимальное количество результатов в ответе
        :return: если нет ошибки: список пользователей, иначе: None
        """
        full_params = {**search_params, **self.base_params,
                       'sort': '0',
                       'fields': 'is_closed,relation',
                       'count': count,
                       'offset': offset
                       }
        url = base_url + 'users.search'
        response = requests.get(url=url, params=full_params).json()
        if 'error' not in response:
            users = response['response']['items']
            return users
        elif response['error']['error_code'] == 6:
            time.sleep(1)
            return self.users_search(search_params, offset, count)
        else:
            pprint(response)
            return None

    def photos_get(self, user_id) -> list or None:
        """
        поиск всех фото профиля пользователя
        :param user_id: id пользователя
        :return: если нет ошибки: список фото пользователя, иначе: None
        """
        search_params = {
            'owner_id': user_id,
            'album_id': 'profile',
            'extended': '1',
            'photo_sizes': '1'
        }
        full_params = {**self.base_params, **search_params}
        url = base_url + 'photos.get'
        response = requests.get(url=url, params=full_params).json()
        if 'response' in response:
            return response['response']['items']
        elif response['error']['error_code'] == 6:
            time.sleep(1)
            return self.photos_get(user_id)
        else:
            pprint(response)
            return None

    def users_get(self, user_id) -> dict:
        """
        получение информации о пользователе
        :param user_id: id пользователя
        :return: словарь - информация о пользователе
        """
        return self.vk.method('users.get', {'user_id': user_id, 'fields': 'sex,bdate,city,country'})[0]

    def database_get_cities(self, q: str, country_id) -> int or None:
        """
        поиск города в стране по названию
        :param q: название города
        :param country_id: id страны
        :return: если найдено: id города, иначе: None
        """
        url = base_url + 'database.getCities'
        response = requests.get(url, params={'q': q, 'country_id': country_id, 'count': 1,
                                             'need_all': 0, **self.base_params}).json()
        if response['response']['count'] != 0:
            return response['response']['items'][0]['id']
        else:
            return None

    def database_get_countries(self) -> list:
        """
        Получение списка всех стран
        :return: список стран
        """
        url = base_url + 'database.getCountries'
        response = requests.get(url, params={'need_all': 1, 'count': 1000, **self.base_params}).json()
        return response['response']['items']

    def get_params(self, user_id) -> dict:
        """
        получение параметров поиска для заданного пользователя
        :param user_id: id пользователя
        :return: словарь - параметры
        """
        info = self.users_get(user_id)
        user_params = dict()
        if 'bdate' in info:
            now = self.utils_get_server_time()
            bdate = info['bdate'].split('.')
            if len(bdate) == 3:
                age = utils.age_meter(now, bdate)
                user_params['age'] = age
        if 'sex' in info:
            if info['sex'] in [1, 2]:
                user_params['sex'] = info['sex']
        if 'city' in info:
            user_params['city'] = info['city']['id']
        if 'country' in info:
            user_params['country'] = info['country']['id']
        return user_params

    def get_name(self, user_id) -> str:
        """
        получение имени пользователя
        :param user_id: id пользователя
        :return: имя пользователя
        """
        response = self.vk.method('users.get', {'user_ids': user_id})
        name = response[0]['first_name'] + ' ' + response[0]['last_name']
        return name
