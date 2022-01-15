from pprint import pprint
import requests
import time
token_url = 'https://oauth.vk.com/authorize?client_id=8039929&display=page&redirect_uri=https://oauth.vk.com/blank.html&response_type=token&v=5.131'

application_id = '8039929'
secret_key = '504Q0XHEYydfqbQ0kJ22'
service_key = 'e8cac700e8cac700e8cac700a3e8b06af9ee8cae8cac70089072939b8972aff1b7c96ea'
access_token = '942d2ebb5de1f828c4879c1aa7f473a30672a5de6d58e3030497ac606d0a65b3ea98ccd88c6ac86f9f17e'
base_params = {
    'access_token': access_token,
    'v': '5.131'
}

base_url = 'https://api.vk.com/method/'


def users_search_old(search_params, offset=0, count=20):
    full_params = {**search_params, **base_params,
                   'sort': '0',
                   'fields': 'is_closed',
                   'count': count,
                   'offset': offset
                   }
    url = base_url + 'users.search'
    response = requests.get(url=url, params=full_params).json()
    pprint(response)
    return response


def users_search(search_params, offset=0, count=1):
    full_params = {**search_params, **base_params,
                   'sort': '0',
                   'fields': 'is_closed,relation',
                   'count': count,
                   'offset': offset
                   }
    url = base_url + 'users.search'
    response = requests.get(url=url, params=full_params).json()
    if 'error' not in response:
        pprint(response)
        if response['response']['items']:
            if response['response']['items'][0]['is_closed']:
                return users_search(search_params, offset=offset+1)
            else:
                return response
        else:
            return users_search(search_params, offset=offset+1)
    elif response['error']['error_code'] == 6:
        time.sleep(1)
        return users_search(search_params)
    elif response['error']['error_code'] == 5:
        print(f'токен просрочен, перейдите по ссылке: {token_url}')
        return 'error'
    else:
        pprint(response)
        raise Exception(response['error']['error_msg'])


def ids_from_users_search(response) -> list:
    user_ids = list()
    if 'response' not in response:
        print(response)
    if 'error' in response:
        if response['error']['error_code'] == 5:
            print(f'токен просрочен, перейдите по ссылке: {token_url}')
    for item in response['response']['items']:
        # print(item['id'], item['is_closed'])
        if not item['is_closed']:
            user_ids.append(item['id'])
    pprint(user_ids)
    return user_ids


def id_from_users_search(response) -> int:
    # pprint(response)
    if 'error' in response:
        if response['error']['error_code'] == 5:
            print(f'токен просрочен, перейдите по ссылке: {token_url}')
            raise Exception('token expired')
        else:
            raise Exception(response['error'])
    if 'response' not in response:
        pprint(response)
    user_id = response['response']['items'][0]['id']
    pprint(user_id)
    return user_id


def get_photos(user_id) -> list:
    """
    :param user_id: id человека
    :return: список из 3 самых популярных фото человека
    """
    search_params = {
        'owner_id': user_id,
        'album_id': 'profile',
        'extended': '1',
        'photo_sizes': '1'
    }
    full_params = {**base_params, **search_params}
    url = base_url + 'photos.get'
    response = requests.get(url=url, params=full_params).json()
    if 'error' in response:
        if response['error']['error_code'] == 6:
            time.sleep(1)
            return get_photos(user_id)
    if response['response']['count'] == 0:
        print('no photos')
        return list()
    response_photos = response['response']['items']
    response_sorted_photos = sorted(response_photos, key=lambda x: x['likes']['count'], reverse=True)
    response_top_photos = response_sorted_photos[0:3]
    top_photos = list()
    for photo in response_top_photos:
        top_photos.append('photo' + str(photo['owner_id']) + '_' + str(photo['id']))
    return top_photos


def get_multiple_photos(user_ids: list):
    photos_list = list
    for user_id in user_ids:
        photos_list.append(get_photos(user_id))
    return photos_list


def database_get_countries(q: str) -> int:
    url = base_url + 'database.getCountries'
    response = requests.get(url, params={'q': q, 'count': 1, **base_params, 'need_all': 0}).json()
    return response['response']['items'][0]['id']


def database_get_cities(q: str, country_id) -> int:
    url = base_url + 'database.getCities'
    response = requests.get(url, params={'q': q, 'country_id': country_id, 'count': 1, **base_params, 'need_all': 0}).json()
    return response['response']['items'][0]['id']


if __name__ == '__hello__':
    params = {
        'q': 'Василий'
    }
    ids = ids_from_users_search(users_search(params))
    for id in ids:
        pprint(get_photos(id))
        print()


if __name__ == '__main__':
    pprint(database_get_cities('санкт', database_get_countries('россия')))