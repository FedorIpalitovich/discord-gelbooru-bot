import aiohttp
from aiohttp.client_exceptions import ClientConnectionError
import urllib.parse
from random import randint


__all__ = ('GelbooruResponse',)

class NoPostsFound(Exception): ...

class GelbooruResponse:
    """class to get async responses from Gelbooru
    
    use:
        content: dict = await GelbooruResponse().get_post()
    """
    
    __slots__ = ('tags', 'pid', 'random')
    
    from settings import GELBOORU_API_KEY as __API_KEY
    from settings import GELBOORU_USER_ID as __USER_ID
        
    def __init__(self, *, tags: str = '*', pid: int = 0, random: bool = False) -> None:
        self.tags: str = tags
        if random:
            self.pid: int = randint(0, 20000)
        else:
            self.pid: int = pid
        self.random: bool = random
    
    async def get_post(self) -> dict[str, ]:
        autocompleted_tags: list[str] = await self.autocomplete(self.tags)
        request_url = f'https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit=1&pid={self.pid}&tags={await self.encode_tags(autocompleted_tags)}'
        if self.__API_KEY and self.__USER_ID:
            request_url += f'&api_key={self.__API_KEY}&user_id={self.__USER_ID}'
        response: dict[str, ] = await self.connect_gelbooru(request_url)
        if response['@attributes']['count'] == 0:
            raise NoPostsFound
        if 'post' not in response:
            max_pid: int = response['@attributes']['count'] - 1
            new_pid = int()
            if self.random:
                new_pid = randint(0, max_pid)
            else:
                new_pid = max_pid
            request_url = request_url.replace(f'&pid={self.pid}', f'&pid={new_pid}', 1)
            self.pid: int = new_pid
            response = await self.connect_gelbooru(request_url)
        # some check because of gelbooru json response
        if not isinstance(response['post'], dict):
            post: dict = response['post'][0]
        else:
            post: dict = response['post']
        try:
            while autocompleted_tags != []:
                autocompleted_tags.remove('*')
            autocompleted_tags.append('*')
        except ValueError:
            pass
        if post['file_url'].endswith(('.gif', '.webm', '.mp4')):
            is_video = True
        else:
            is_video = False
        result: dict[str, ] = {
            'id': post['id'],
            'file_url': post['file_url'],
            'tags': ' '.join(autocompleted_tags),
            'pid': self.pid,
            'is_video': is_video
            }
        return result
    
    async def autocomplete(self, tags: list[str] | str) -> list[str]:
        if isinstance(tags, str):
            tags: list[str] = tags.split()
        autocompleted_tags: list[str] = list()
        for tag in tags:
            if tag.startswith(('-', '~', 'rating:', 'id:')) or tag.endswith('~') or '*' in tag:
                autocompleted_tags.append(tag)
                continue
            for i in range(1, 4):
                if tag == '':
                    break
                encoded_tag: str = await self.encode_tags(tag)
                response: list = await self.connect_gelbooru(
                    f'https://gelbooru.com/index.php?page=autocomplete2&term={encoded_tag}')
                if len(response) == 0:
                    tag = tag[:-i]
                    continue
                break
            if len(response) == 0:
                autocompleted_tags.append('*')
                continue
            autocompleted_tags.append(response[0]['value'])
        return autocompleted_tags
    
    async def recent_tags(self) -> str:
        pass

    @staticmethod
    async def encode_tags(tags: list[str] | str) -> str:
        if isinstance(tags, str):
            return urllib.parse.quote(tags, encoding='utf-8')
        encoded_tags = str()
        for tag in tags:
            encoded_tags += urllib.parse.quote(tag, encoding='utf-8') + '+'
        return encoded_tags

    @staticmethod
    async def connect_gelbooru(url: str) -> dict[str, ] | list[dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as json_response:
                    response: dict = await json_response.json()
        except ClientConnectionError as e:
            raise e
        return response
