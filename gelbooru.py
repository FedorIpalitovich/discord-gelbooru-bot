import aiohttp
from aiohttp.client_exceptions import ClientConnectionError
import urllib.parse
from random import randint
from errors import NoPostsFound


__all__ = ('Response',)

class Response:
    """class to get async responses from Gelbooru
    
    usage:
        response = Response()\n
        content = await response.get_post()
    """
    
    __slots__ = ('tags', 'pid', 'random', 'autocompleted_tags')
    
    from settings import GELBOORU_API_KEY as __API_KEY
    from settings import GELBOORU_USER_ID as __USER_ID
        
    def __init__(self, *, tags: str | list[str] = '*', pid: int = 0, random: bool = False) -> None:
        if isinstance(tags, str):
            self.tags: list[str] = tags.split()
        else:
            self.tags: list[str] = tags
        if random:
            self.pid: int = randint(0, 20000)
        else:
            self.pid: int = pid
        self.random: bool = random
        self.autocompleted_tags: list[str] = list()
    
    async def get_post(self) -> dict[str, ]:
        await self.autocomplete_tags()
        request_url = f'https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit=1'
        request_url += f'&pid={self.pid}&tags={await __class__.encode_tags(self.autocompleted_tags)}'
        
        if self.__API_KEY and self.__USER_ID:
            request_url += f'&api_key={self.__API_KEY}&user_id={self.__USER_ID}'
            
        response: dict[str, ] = await __class__.connect_gelbooru(request_url)
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
            response = await __class__.connect_gelbooru(request_url)
        
        # some check because of gelbooru json response
        if not isinstance(response['post'], dict):
            post: dict = response['post'][0]
        else:
            post: dict = response['post']
        
        try:
            self.autocompleted_tags.remove('*')
        except ValueError:
            pass
        
        result: dict[str, ] = {
            'id': post['id'],
            'file_url': post['file_url'],
            'tags': ' '.join(self.autocompleted_tags),
            'pid': self.pid,
            }
        return result
    
    async def autocomplete_tags(self) -> None:
        for tag in self.tags:
            if tag.startswith(('-', '~', 'rating:', 'id:')) or tag.endswith('~') or '*' in tag:
                self.autocompleted_tags.append(tag)
                continue
            
            encoded_tag: str = await __class__.encode_tags(tag)
            response: list[dict] = await __class__.connect_gelbooru(
                f'https://gelbooru.com/index.php?page=autocomplete2&term={encoded_tag}')
            if len(response) == 0:
                continue
            self.autocompleted_tags.append(response[0]['value'])
    
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
