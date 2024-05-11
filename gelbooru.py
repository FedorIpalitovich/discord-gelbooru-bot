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
    
    if not nsfw:
        for tag in tags_list:
            if tag.startswith('rating:'):
                raise NotNSFWchannel
        tags_list.append('rating:general')
    
    autocompleted_tags: list[str] = list()
    for tag in tags_list:
        _ = await autocomplete(tag)
        autocompleted_tags.append(_)
    
    # encode our query
    for tag in autocompleted_tags:
        tags += urllib.parse.quote(tag ,encoding='utf-8') + '+'
        
    request_url = f'https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit=1&pid={pid}&tags={tags}'
    
    if api_key and user_id:
        request_url += f'&api_key={api_key}&user_id={user_id}'
    
    response: requests.Response = requests.get(request_url)
    if response.status_code != 200:
        raise ConnectionError(f'Non-200 response from Gelbooru, got {response.status_code} instead')
    
    try:
        json_response: dict[str, ] = json.loads(response.text) # check for undefined tags
    except json.decoder.JSONDecodeError:
        raise Exception('JSONDecodeError')
    
    if 'post' not in json_response:
        raise NoPostsFound
    
    # some crutch idk (because of gelbooru json response)
    elif isinstance(json_response['post'], dict):
        content_data = [json_response['post']]
    else:
        content_data = json_response['post']
    
    for json_item in content_data:
        result: dict[str, ] = {
            'id': json_item['id'],
            'content_url': json_item['file_url'],
            'tags': ' '.join(autocompleted_tags),
        }
    
    return result


async def autocomplete(tag: str) -> str:
    if tag.startswith(('-', '~')) or tag.endswith('~') or '*' in tag:
        return tag

    encoded_tag = urllib.parse.quote(tag)
    request_url = f'https://gelbooru.com/index.php?page=autocomplete2&term={encoded_tag}'
    try:
        response: requests.Response = requests.get(request_url)
    except requests.ConnectionError:
        raise ConnectionError('no connection')
    if response.status_code != 200:
        raise ConnectionError(f'Non-200 response from Gelbooru, got {response.status_code} instead')

    try:
        autocompleted_tag_list: list[str] = list(_['value'] for _ in json.loads(response.text))
        # Do not autocomplete tag if it is already a valid tag
        if tag in autocompleted_tag_list:
            autocompleted_tag = tag
        else:
            # first (most popular) tag
            autocompleted_tag = autocompleted_tag_list[0]
    except (IndexError, KeyError, json.decoder.JSONDecodeError):
        raise NoPostsFound
    
    return autocompleted_tag

