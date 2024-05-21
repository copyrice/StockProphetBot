import asyncio, aiohttp, aiomoex
import urllib.parse
timeout = 10
num = 5
semaphore = asyncio.Semaphore(num)

index_boards = ['SNDX', 'RTSI', 'AGRO', 'SDII',
                'GNDX']

class MoexApiHandler:
    base_url = "https://iss.moex.com/iss"
    
    @staticmethod
    async def get_indeces_including_security(secid: str):
        endpoint = f'securities/{secid}/indices'
        return await MoexApiHandler._make_request_ISSClient(endpoint)
        
    @staticmethod
    async def get_security_data(secid: str, board='TQBR'):
        endpoint = f'engines/stock/markets/shares/boards/{board}/securities/{secid}'
        return await MoexApiHandler._make_request_ISSClient(endpoint)
    
    @staticmethod
    async def get_index_data(secid: str, base_board='SNDX'):
        for board in index_boards:
            endpoint = f'engines/stock/markets/index/boards/{board}/securities/{secid}'
            data = await MoexApiHandler._make_request_ISSClient(endpoint)
            if(data['securities']):
                return data
        endpoint = f'engines/stock/markets/index/boards/{base_board}/securities/{secid}'
        return await MoexApiHandler._make_request_ISSClient(endpoint)
    @staticmethod
    async def get_index_history(secid: str):
        async with semaphore:
            # https://iss.moex.com/iss/engines/stock/markets/index/boardgroups/stock_index/securities/IMOEX/candles
            async with aiohttp.ClientSession() as session:
                data = await aiomoex.get_market_candles(session, secid, market='index')
                return data
            
    @staticmethod
    async def get_share_history(secid: str):
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                data = await aiomoex.get_board_candles(session, secid)
                return data
            
    @staticmethod
    async def get_all_shares(limit: int = 100):
        endpoint = 'securitygroups/stock_shares/collections/stock_shares_all/securities'
        params = {
            'limit': limit
        }
        data = await MoexApiHandler._make_request_ISSClient(endpoint, params)
        items = data['securities']
        total = data['securities.cursor'][0]['TOTAL']
        tasks = []
        for i in range(total // limit + 1):
            params = {
                'limit': limit,
                'start': i * limit
            }
            task = asyncio.ensure_future(asyncio.create_task(MoexApiHandler._make_request_ISSClient(endpoint, params)))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        for resp in responses:
            additional_items = resp['securities']
            items += additional_items
        
        return items
    

    @staticmethod
    async def index():
        endpoint = 'index'
        return await MoexApiHandler._make_request_ISSClient(endpoint)
    

    @staticmethod
    async def get_board_name(board_id: str) -> str:
        data = await MoexApiHandler.index()
        for elem in data['boards']:
            if(elem['boardid']==board_id):
                return elem['board_title']
        return ''
    @staticmethod
    async def cast_to_dict(items: list, keys: list):
        dictionaries = []
        for i in range(len(items)):
            dct = {}
            for key in keys:
                dct[key] = items[i][keys.index(key)]
            dictionaries.append(dct)
        return dictionaries

    async def _make_request(endpoint, params = {}):
        url = f"{MoexApiHandler.base_url}/{endpoint}.json"
        try:
                async with semaphore:
                    async with aiohttp.ClientSession() as session:
                        # iss = aiomoex.ISSClient(session, url)
                        response = await session.request('GET', url, params=params)
                        data = await response.json()
                        return data
                        
        except asyncio.exceptions.TimeoutError:
            print(f'{url} request timed out')

        except aiohttp.client_exceptions.ContentTypeError:
                print('Server did not send the response')

    async def _make_request_ISSClient(endpoint, params = {}):
        url = f"{MoexApiHandler.base_url}/{endpoint}.json"
        if(params):
            encoded_params = urllib.parse.urlencode(params)
            url = f"{url}?{encoded_params}"
        try:
                async with semaphore:
                    async with aiohttp.ClientSession() as session:
                        iss = aiomoex.ISSClient(session, url)
                        data = await iss.get()
                        return data
                        
        except asyncio.exceptions.TimeoutError:
            print(f'{url} request timed out')

        except aiohttp.client_exceptions.ContentTypeError:
                print('Server did not send the response')