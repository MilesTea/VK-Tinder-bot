import random
import vk
import sql
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def search_by_params(search_offset: int, search_count: int, search_params, bot, event, settings) -> list:
    """
    поиск пользователей по заданным параметрам
    :param search_offset: offset
    :param search_count:  count
    :param search_params: параметры поиска
    :param bot: бот из vk.py
    :param event: event
    :param settings: settings
    :return: перетасованный список найденых пользователей
    """
    print('начинаю поиск')
    users = bot.users_search(search_params=search_params, offset=search_offset, count=search_count)
    if users:
        filtered_users = vk.filter_users(users)
        random.shuffle(filtered_users)
        print('поиск удачный')
        return filtered_users
    else:
        bot.messages_send(event.user_id, settings['token_expired'])
        new_user_token = wait_for_response(event.user_id, bot)
        bot.update_user_token(new_user_token)
        print('поиск не удачный, начинаю новый поиск')
        return search_by_params(search_offset, search_count, search_params, bot, event, settings)


def wait_for_response(user_id, bot) -> str:
    """
    ожидание ответа пользователя; добавление событий от других пользователей в очередь
    :param user_id: id пользователя
    :param bot: бот из vk.py
    :return: ответ пользователя
    """
    for new_event in bot.longpoll.listen():
        if new_event.type == vk.VkEventType.MESSAGE_NEW:
            if new_event.to_me:
                if new_event.user_id == user_id:
                    return new_event.text.lower()
                else:
                    bot.longpoll.add_to_queue(new_event)


def get_user(sorted_users, bot, event, db, keyboard) -> True or False:
    """
    :param sorted_users: список пользователей
    :param bot: бот из vk.py
    :param event: event
    :param db: доступ к базе данных
    :param keyboard: клавиатура для бота
    :return: если пользователь найден - True, иначе - False
    """
    while sorted_users:
        user = sorted_users[-1]
        photos = vk.get_top_photos(bot.photos_get(user['id']))
        sorted_users.pop()

        if db.is_on:
            in_db = db.check(user['id'])
        else:
            in_db = False
            print('Внимание, база данных недоступна')

        if photos and not in_db:
            user_name = user['first_name'] + ' ' + user['last_name']
            url = f'https://vk.com/id{user["id"]}'
            message = f'{user_name}\n{url}'
            photos = ','.join(photos)
            print(user_name)
            bot.messages_send(user_id=event.user_id,
                              message=message,
                              optional_params={'keyboard': keyboard.get_keyboard(),
                                               'attachment': photos})
            db.add(user['id'])
            return True
    print('подходящих в списке нет')
    return False


def get_params(params, settings):
    """
    :param params: параметры пользователя
    :param settings: settings
    :return: параметры поиска
    """
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


def check_params(event, params, bot) -> None:
    """
    проверка параметров пользователя на заполнение; их дозаполнение в случае отсутсвия
    :param event: event
    :param params: параметры пользователя
    :param bot: бот из vk.py
    :return: None
    """
    if 'sex' not in params:
        temp_keyboard = VkKeyboard(inline=True, one_time=False)
        temp_keyboard.add_button('Мужской', color=VkKeyboardColor.SECONDARY)
        temp_keyboard.add_button('Женский', color=VkKeyboardColor.PRIMARY)
        bot.messages_send(event.user_id, 'Ваш пол?\nМужской/Женский',
                          optional_params={'keyboard': temp_keyboard.get_keyboard()})
        sex = wait_for_response(event.user_id, bot)
        if sex == 'мужской':
            params['sex'] = 2
        elif sex == 'женский':
            params['sex'] = 1
        else:
            bot.messages_send(event.user_id, 'неверное значение, будут отображаться партнёры любого пола')

    if 'age' not in params:
        bot.messages_send(event.user_id, 'Сколько вам лет?')
        age = wait_for_response(event.user_id, bot)
        if age.isdigit():
            params['age'] = int(age)
        else:
            bot.messages_send(event.user_id, 'неверное значение, будут отображаться партнёры любого возраста')

    if 'country' not in params:
        bot.messages_send(event.user_id, 'Название вашей страны?')
        country = wait_for_response(event.user_id, bot)
        for item in bot.database_get_countries():
            if item['title'].lower() == country:
                params['country'] = item['id']
                break

    if 'country' not in params:
        bot.messages_send(event.user_id, 'неверное значение, будут отображаться партнёры из любой точки мира')

    if 'country' in params and 'city' not in params:
        bot.messages_send(event.user_id, 'Название вашего города?')
        city = wait_for_response(event.user_id, bot)
        city_id = bot.database_get_cities(city, params['country'])
        if not city_id:
            bot.messages_send(event.user_id, 'неверное значение, будут отображаться партнёры со всей страны')


def start(bot, event, settings, name, db, keyboard):
    bot.messages_send(event.user_id, f"Привет, {name}\n{settings['info']}",
                      optional_params={'keyboard': keyboard.get_keyboard()})
    print(f'Здраствуйте, {name}')
    if not db.is_on():
        bot.messages_send(event.user_id, 'Внимание, база данных недоступна, результаты поиска могут повторяться')


def search(search_params: dict, shuffled_users: list, bot, event, settings, db, keyboard):
    if not search_params:
        params = bot.get_params(event.user_id)
        check_params(event, params, bot)
        search_params = get_params(params, settings)
    if not shuffled_users:
        shuffled_users = search_by_params(settings['offset'], settings['count'], search_params, bot, event, settings)

    warn = False
    while not get_user(shuffled_users, bot, event, db, keyboard):
        if not warn:
            bot.messages_send(event.user_id, 'Выполняется поиск, пожалуйста, подождите')
            warn = True
        settings['offset'] += settings['count']
        shuffled_users = search_by_params(settings['offset'], settings['count'], search_params, bot, event, settings)
    return search_params, settings


def clean(bot, db, event, keyboard):
    if db.is_on():
        db.delete_all()
        bot.messages_send(event.user_id, 'Очистка выполнена',
                          optional_params={'keyboard': keyboard.get_keyboard()})


def main():
    user_token = ''
    group_token = ''
    Db = sql.UsersDb()
    shuffled_users = list()
    search_params = dict()
    if not group_token or user_token:
        group_token = input('Введите ключ доступа вашей группы\n')
        user_token = input('Введите ключ доступа пользователя\n')
        print('Бот готов к работе')

    settings = {
        'age_range': 2,
        'relation': [1, 6, 0],
        'info': 'Этот бот умеет искать тебе вторую половинку\n'
                'Для начала работы с ним нажми "Поиск"\n'
                'Для очистки просмотренных пользователей нажми "Очистка"',
        'token_expired': f'Ваш токен устарел, пожалуйста, введите новый токен',
        'offset': 0,
        'count': 100
    }

    keyboard = VkKeyboard(inline=True, one_time=False)
    if Db.is_on():
        keyboard.add_button('Очистка', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('Поиск', color=VkKeyboardColor.PRIMARY)

    Bot = vk.Bot(user_token, group_token)
    for event in Bot.longpoll.improved_listen():
        if event.type == vk.VkEventType.MESSAGE_NEW:
            if event.to_me:
                name = Bot.get_name(event.user_id)
                request = event.text.lower()
                if request == "start":
                    start(Bot, event, settings, name, Db, keyboard)
                elif request == 'поиск':
                    search_params, offset = search(search_params, shuffled_users, Bot, event, settings, Db, keyboard)
                elif request == "очистка":
                    clean(Bot, Db, event, keyboard)
                elif request == "пока":
                    Bot.messages_send(event.user_id, 'Пока')
                else:
                    Bot.messages_send(event.user_id, 'Команда не распознанна')


if __name__ == "__main__":
    main()
