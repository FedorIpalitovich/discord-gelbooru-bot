import json
import requests
import urllib.parse
from random import randint
from typing import Optional

# errors
class NotNSFWchannel(Exception): ...
class NoPostsFound(Exception): ...

async def connect_to_gelbooru(
    *,
    api_key: str,
    user_id: str,
    random: bool = False,
    tags: Optional[str] = None,
    nsfw: bool = False,
    pid: int = 0
) -> dict[str, ]:
    if tags is None:
        tags: str = '*' # tag for all posts
    
    tags_list = tags.split()
    tags = ''
    
    if random:
        pid = randint(0, 20000)
    
    if not nsfw:
        for tag in tags_list:
            if tag.startswith('rating:'):
                raise NotNSFWchannel
        tags_list.append('rating:general')
    
    # autocomplete query tags
    autocompleted_tags: list[str] = list()
    for tag in tags_list:
        _ = await autocomplete(tag)
        autocompleted_tags.append(_)
    
    # encode query tags
    for tag in autocompleted_tags:
        tags += urllib.parse.quote(tag, encoding='utf-8') + '+'        

    request_url = f'https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit=1&pid={pid}&tags={tags}'
    
    if api_key and user_id:
        request_url += f'&api_key={api_key}&user_id={user_id}'
    
    json_response = await get_response(request_url)
    
    if json_response['@attributes']['count'] == 0:
        raise NoPostsFound
    
    if 'post' not in json_response:
        max_pid: int = json_response['@attributes']['count'] - 1
        new_pid = int()
        
        if random:
            new_pid = randint(0, max_pid)
        else: new_pid = max_pid
        
        request_url = request_url.replace(f'&pid={pid}', f'&pid={new_pid}', 1)
        
        json_response = await get_response(request_url)
        
    # some crutch idk (because of gelbooru json response)
    if isinstance(json_response['post'], dict):
        content_data = [json_response['post']]
    else:
        content_data = json_response['post']
    
    for json_item in content_data:
        result: dict[str, ] = {
            'id': json_item['id'],
            'content_url': json_item['file_url'],
            'tags': ' '.join(autocompleted_tags),
            'pid': pid,
        }
    
    return result


async def autocomplete(tag: str) -> str:
    if tag.startswith(('-', '~')) or tag.endswith('~') or '*' in tag or 'rating:' in tag:
        return tag

    encoded_tag = urllib.parse.quote(tag, encoding='utf-8')
    request_url = f'https://gelbooru.com/index.php?page=autocomplete2&term={encoded_tag}'
    try:
        response: requests.Response = requests.get(request_url)
    except requests.ConnectionError:
        raise ConnectionError('no connection')
    if response.status_code != 200:
        raise ConnectionError(f'Non-200 response from Gelbooru, got {response.status_code} instead')

    try:
        autocompleted_tags: list[dict[str, ]] = json.loads(response.text)
        return autocompleted_tags[0]['value'] # autocompleted tag
    
    except (IndexError, KeyError,):
        return tag # returns normal tag if autocomplete returns none
    
    except json.decoder.JSONDecodeError:
        raise Exception('JSONDecodeError')
    

async def get_response(request_url: str) -> dict[str, ]:
    response: requests.Response = requests.get(request_url)
    if response.status_code != 200:
        raise ConnectionError(f'Non-200 response from Gelbooru, got {response.status_code} instead')

    try:
        json_response: dict[str, ] = json.loads(response.text)
    except json.decoder.JSONDecodeError:
        raise Exception('JSONDecodeError')
    
    return json_response