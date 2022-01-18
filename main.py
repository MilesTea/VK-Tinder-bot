import random
import vk
import sql
from pprint import pprint
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def search(search_offset, search_count):
    print('начинаю поиск')
    users = Bot.users_search(search_params=search_params, offset=search_offset, count=search_count)
    if users:
        filtered_users = vk.filter_users(users)
        random.shuffle(filtered_users)
        print('поиск удачный')
        return filtered_users
    else:
        Bot.messages_send(event.user_id, settings['token_expired'])
        new_user_token = wait_for_response(event.user_id)
        Bot.update_user_token(new_user_token)
        print('поиск не удачный, начинаю новый поиск')
        return search(search_offset, search_count)


def wait_for_response(user_id):
    for new_event in Bot.longpoll.listen():
        if new_event.type == vk.VkEventType.MESSAGE_NEW:
            if new_event.to_me:
                if new_event.user_id == user_id:
                    return new_event.text.lower()
                else:
                    Bot.longpoll.add_to_queue(new_event)


def get_user(sorted_users):
    while sorted_users:
        user = sorted_users[-1]
        photos = vk.get_top_photos(Bot.photos_get(user['id']))
        sorted_users.pop()
        if photos and not Db.check(user['id']):
            user_name = user['first_name'] + ' ' + user['last_name']
            url = f'https://vk.com/id{user["id"]}'
            message = f'{user_name}\n{url}'
            photos = ','.join(photos)
            print(user_name)
            Bot.messages_send(user_id=event.user_id,
                              message=message,
                              optional_params={'keyboard': start_keyboard.get_keyboard(),
                                               'attachment': photos})
            Db.add(user['id'])
            return True
    print('подходящих в списке нет')
    return False


def get_params(params):
    search_params = dict()
    if 'sex' in params:
        if params['sex'] == 1:
            search_params['sex'] = 2
        elif params['sex'] == 2:
            search_params['sex'] = 1
        else:
            search_params['sex'] = 0
    if 'age' in params:
        search_params['age_from'] = params['age'] - settings['age_range']
        search_params['age_to'] = params['age'] + settings['age_range']
    if 'city' in params:
        search_params['city'] = params['city']
    if 'country' in params:
        search_params['country'] = params['country']
    print('Параметры поиск:\n', search_params)
    return search_params


def check_params(event, params) -> None:
    if 'sex' not in params:
        temp_keyboard = VkKeyboard(inline=True, one_time=False)
        temp_keyboard.add_button('Мужской', color=VkKeyboardColor.SECONDARY)
        temp_keyboard.add_button('Женский', color=VkKeyboardColor.PRIMARY)
        Bot.messages_send(event.user_id, 'Ваш пол?\nМужской/Женский',
                          optional_params={'keyboard': start_keyboard.get_keyboard()})
        sex = wait_for_response(event.user_id)
        if sex == 'мужской':
            params['sex'] = 2
        elif sex == 'женский':
            params['sex'] = 1
        else:
            Bot.messages_send(event.user_id, 'неверное значение, будут отображаться партнёры любого пола')

    if 'age' not in params:
        Bot.messages_send(event.user_id, 'Сколько вам лет?')
        age = wait_for_response(event.user_id)
        if age.isdigit():
            params['age'] = int(age)
        else:
            Bot.messages_send(event.user_id, 'неверное значение, будут отображаться партнёры любого возраста')

    if 'country' not in params:
        Bot.messages_send(event.user_id, 'Название вашей страны?')
        country = wait_for_response(event.user_id)
        for item in Bot.database_get_countries():
            if item['title'].lower() == country:
                params['country'] = item['id']
                break

    if 'country' not in params:
        Bot.messages_send(event.user_id, 'неверное значение, будут отображаться партнёры из любой точки мира')
    else:
        Bot.messages_send(event.user_id, 'Название вашего города?')
        city = wait_for_response(event.user_id)
        city_id = Bot.database_get_cities(city, params['country'])
        if not city_id:
            Bot.messages_send(event.user_id, 'неверное значение, будут отображаться партнёры со всей страны')


user_token = ''
group_token = ''
app_id = ''

main_keyboard = VkKeyboard(inline=True, one_time=False)
main_keyboard.add_button('Очистка', color=VkKeyboardColor.SECONDARY)
main_keyboard.add_button('Далее', color=VkKeyboardColor.PRIMARY)


start_keyboard = VkKeyboard(inline=True, one_time=False)
start_keyboard.add_button('Очистка', color=VkKeyboardColor.SECONDARY)
start_keyboard.add_button('Поиск', color=VkKeyboardColor.PRIMARY)


if __name__ == "__main__":
    Db = sql.UsersDb()
    readed = False
    shuffled_users = None
    searched = False
    count = 100
    offset = 0
    if not group_token or user_token or app_id:
        print('Для работы бота требуется ключ доступа группы и id вашего приложения ВК')
        app_id = input('Введите id вашего приложения\n')
        group_token = input('Введите ключ доступа вашей группы\n')
        token_link = f'https://oauth.vk.com/authorize?client_id={app_id}&redirect_uri=https://oauth.vk.com/blank.html&response_type=token&v=5.131'
        print(f'Получите токен по ссылке\n{token_link}')
        user_token = input('Введите полученный токен\n')
        print('Бот готов к работе')
    token_link = f'https://oauth.vk.com/authorize?client_id={app_id}&redirect_uri=https://oauth.vk.com/blank.html&response_type=token&v=5.131'

    settings = {
        'age_range': 2,
        'relation': [1, 6, 0],
        'info': 'Этот бот умеет искать тебе вторую половинку\n'
                'Для начала работы с ним нажми "Поиск"\n'
                'Для очистки просмотренных пользователей нажми "Очистка"',
        'token_expired': f'Ваш токен устарел, пожалуйста, введите новый токен\nСсылка для токена:\n{token_link}'
    }

    Bot = vk.Bot(user_token, group_token)
    for event in Bot.longpoll.improved_listen():
        if event.type == vk.VkEventType.MESSAGE_NEW:
            if event.to_me:
                name = Bot.get_name(event.user_id)
                request = event.text.lower()
                if request == "start":
                    Bot.messages_send(event.user_id, f"Привет, {name}\n{settings['info']}",
                                      optional_params={'keyboard': start_keyboard.get_keyboard()})
                    print(f'Здраствуйте, {name}')
                elif request == 'поиск':
                    warn = False
                    # читаем параметры поиска
                    if not readed:
                        search_params = get_params(Bot.get_params(event.user_id))
                        readed = True

                    # проверка на поиск
                    if not searched:
                        shuffled_users = search(offset, count)
                        searched = True
                    if shuffled_users:
                        while not get_user(shuffled_users):
                            if not warn:
                                Bot.messages_send(event.user_id, 'Выполняется поиск, пожалуйста, подождите')
                                warn = True
                            offset += count
                            shuffled_users = search(offset, count)

                elif request == "очистка":
                    Db.delete_all()
                    Bot.messages_send(event.user_id, 'Очистка выполнена',
                                      optional_params={'keyboard': start_keyboard.get_keyboard()})
                elif request == "пока":
                    Bot.messages_send(event.user_id, 'Пока')
                else:
                    Bot.messages_send(event.user_id, 'Команда не распознанна')
