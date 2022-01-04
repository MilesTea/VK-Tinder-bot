from pprint import pprint
import requests
import time

application_id = '8039929'
secret_key = '504Q0XHEYydfqbQ0kJ22'
service_key = 'e8cac700e8cac700e8cac700a3e8b06af9ee8cae8cac70089072939b8972aff1b7c96ea'
access_token = 'aca1367d5f73a5ebdc059bce045ccc2dc3f0bdce063f880bd207c49092ce1265089e9c62766845c766fa1'
base_params = {
    'access_token': access_token,
    'v': '5.131'
}

base_url = 'https://api.vk.com/method/'
def users_search(params):
    full_params = {**params, **base_params,
                   'sort': '0',
                   'fields': 'is_closed'
                   }
    url = base_url + 'users.search'
    response = requests.get(url=url, params=full_params).json()
    return response

def ids_from_users_search(response):
    ids = list()
    if 'response' not in response:
        print(response)
    for item in response['response']['items']:
        # print(item['id'], item['is_closed'])
        if not item['is_closed']:
            ids.append(item['id'])
    pprint(ids)
    return ids

def get_photos(id) -> list:
    params = {
        'owner_id': id,
        'album_id': 'profile',
        'extended': '1',
        'photo_sizes': '1'
    }
    full_params = {**base_params, **params}
    url = base_url + 'photos.get'
    response = requests.get(url=url, params=full_params).json()
    if 'error' in response:
        if response['error']['error_code'] == 6:
            time.sleep(1)
            return get_photos(id)
    if response['response']['count'] == 0:
        return list()
    response_photos = response['response']['items']
    response_sorted_photos = sorted(response_photos, key=lambda x: x['likes']['count'], reverse=True)
    response_top_photos = response_sorted_photos[0:3]
    # pprint(response_top_photos)
    top_photos = list()
    # for photo in response_top_photos:
    #     top_photos.append(photo['sizes'][-1]['url'])
    for photo in response_top_photos:
        top_photos.append('photo' + str(photo['owner_id']) + '_' + str(photo['id']))
    return top_photos

def get_multiple_photos(ids: list):
    photos_list = list
    for id in ids:
        photos_list.append(get_photos(id))
    return photos_list

if __name__ == '__ghain__':
    params = {
        'q': 'Василий'
    }
    ids = ids_from_users_search(users_search(params))
    for id in ids:
        pprint(get_photos(id))
        print()


if __name__ == '__main__':
    pprint(get_photos(200036391))
    response = requests.get('https://api.vk.com/method/photos.getAlbums', params={
        'owner_id': 200036391, **base_params, 'need_system': 1
    }).json()
    pprint(response)