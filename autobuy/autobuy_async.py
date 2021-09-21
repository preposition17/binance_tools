import os
import logging
import traceback
import time
from datetime import datetime
from multiprocessing import Process
import asyncio

import aiohttp
from dotenv import load_dotenv
from fake_useragent import UserAgent

from utils import get_cookies
from utils import print_dict
from utils import get_time
from utils import get_proxy_list
from utils import proxy_generator


class AioAutobuy:
    def __init__(self, sale_id: str, box_num: int, use_proxy: bool = False):

        # User settings
        self.sale_id = sale_id
        self.box_num = box_num
        self.use_proxy = use_proxy

        # Files path
        self.logger_file = "../logs/autobuy.log"
        self.env_file = "../.env"
        self.proxy_file = "../proxy/proxy_autobuy.txt"

        # Logger
        self.logger = logging.getLogger("AioAutoBuy")
        logging.basicConfig(filename=self.logger_file, level=logging.DEBUG)
        logging.info(f'\n{get_time()}: Autobuy initialization.')

        # URLs
        self.auth_url = "https://www.binance.com/bapi/accounts/v1/public/authcenter/auth"
        self.sale_data_url = "https://www.binance.com/bapi/nft/v1/friendly/nft/mystery-box/detail"
        self.purchase_url = "https://www.binance.com/bapi/nft/v1/private/nft/mystery-box/purchase"

        # Session settings
        load_dotenv(self.env_file)
        __ua = UserAgent()
        self.user_agent = __ua.chrome
        self.__cookies_string = os.getenv('COOKIE')
        self.cookies = get_cookies(cookies_string=self.__cookies_string)
        self.csrf_token = os.getenv('CSRFTOKEN')

        # Proxy
        proxy_list = get_proxy_list(self.proxy_file)
        self.proxy_generator = proxy_generator(proxy_list)

        # Program vars
        self.sale_start_time = None
        self.sale_started = False
        self.is_auth = False

        # Debugging values
        self.requests_count = 0
        self.requests_start_time = None
        self.requests_end_time = None
        self.sec_to_stop = 0

    async def run(self):
        self.logger.info(f'{get_time()}: Main loop running...')

        _headers = {
            "csrftoken": self.csrf_token,
            "clienttype": "web",
            "user-agent": self.user_agent
        }
        _cookies = {cookie[0]: cookie[1] for cookie in self.cookies}

        self.logger.info(f'{get_time()}: Aiohttp session making.')
        async with aiohttp.ClientSession(headers=_headers,
                                         cookies=_cookies) as _session:
            tasks = [
                asyncio.create_task(self.auth(session=_session), name="Authentication"),
                asyncio.create_task(self.get_sale_start_time(session=_session), name="Start time getting"),
                asyncio.create_task(self.sale_waiting(), name="Sale waiting"),
                asyncio.create_task(self.run_async_purchasing(session=_session), name="Async purchasing"),
                asyncio.create_task(self.stop(), name="Stop process"),
            ]
            await asyncio.gather(*tasks)

    async def get_sale_start_time(self, session):
        # Get sale start time in unix time if response successful
        # Else return False

        self.logger.info(f'{get_time()}: Sale start time getting.')

        try_count = 1
        while True:
            try:
                async with session.get(self.sale_data_url,
                                       params={"productId": self.sale_id}) as _response:
                    data = await _response.json()

                    if data["success"]:
                        self.sale_start_time = data["data"]["startTime"]
                        break
                    else:
                        logging.error(f'{get_time()}: Sale start time getting unsuccessful.')
                        continue
            except Exception as ex:
                try_count += 1
                print("Error: ", ex)
                print("Error count: ", try_count)
                print(traceback.format_exc())
                if try_count == 5:
                    print("Global error while getting sale start time, exiting...")
                    exit()

    async def auth(self, session):
        # Try to auth on Binance
        # Return True if auth success
        # Else return False and print unsuccessful message

        self.logger.info(f'{get_time()}: Authentication.')

        try_count = 1
        while True:
            try:
                async with session.post(self.auth_url) as _response:
                    data = await _response.json()
                    if data["success"]:
                        logging.info(f'{get_time()}: Authentication successful.')
                        self.is_auth = True
                        break
                    else:
                        logging.error(f'{get_time()}: Authentication unsuccessful.')
                        print("Authentication unsuccessful.")
                        print("Message: ", data["message"])
                        exit()
            except Exception as ex:
                try_count += 1
                print("Error: ", ex)
                print("Error count: ", try_count)
                print(traceback.format_exc())
                if try_count == 5:
                    print("Global error while authentication, exiting...")
                    exit()

    async def sale_waiting(self):
        # Wait a sale and start purchase trying function
        # If buy is success quiting from loop

        self.logger.info(f'{get_time()}: Waiting to sale...')
        while True:
            if self.sale_started:
                break
            else:
                time_to_sale = self.sale_start_time - time.time() * 1000
                print("Time to sale: ", round(time_to_sale / 1000, 2), 'seconds')

                if time_to_sale < 2000:
                    logging.info(f'{get_time()}: Trying to purchase...')
                    print("Trying to purchase...")
                    self.sale_started = True

    async def run_async_purchasing(self, session):
        if self.sale_started:
            self.requests_start_time = time.time()
            self.logger.info(f'{get_time()}: Starting async purchasing.')
            tasks = []
            for i in range(20):
                tasks.append(self.purchase_request_loop(session=session))
            await asyncio.gather(*tasks)

    async def purchase_request_loop(self, session):
        # TODO: Add proxy
        while True:
            try_count = 1
            while True:
                try:
                    if self.use_proxy:
                        proxy = next(self.proxy_generator)
                    else:
                        proxy = ""
                    async with session.post(self.purchase_url,
                                            json={"number": self.box_num, "productId": self.sale_id},
                                            proxy=f'http://{proxy}') as _response:
                        with open("binance.html", "w") as file:
                            file.write(await _response.text())
                        data = await _response.json()
                        self.requests_count += 1
                        if data["success"]:
                            print("YYYYYYYYYEEEEEEEEEEEEAAAAAAAAAHHHHHHHHH")
                        self.logger.info(f'{get_time()}: {data["message"]}, '
                                         f'{data["success"]} on process #{os.getpid()}.')
                        print(f'{get_time()}: {data["message"]}, {data["success"]}')
                        break

                except Exception as ex:
                    try_count += 1
                    print("Error: ", ex)
                    print("Error count: ", try_count)
                    print(traceback.format_exc())
                    self.logger.error(f'{get_time()}: Error on process #{os.getpid()}.\n'
                                      f'{traceback.format_exc()}')
                    if try_count == 5:
                        print("Global error while authentication, exiting...")
                        exit()

    async def stop(self):
        if self.sec_to_stop:
            await asyncio.sleep(self.sec_to_stop)
            self.requests_end_time = time.time()

            requests_time = self.requests_end_time - self.requests_start_time

            print()
            print("Requests time: ", requests_time)
            print("Requests count: ", self.requests_count)
            print("RPS: ", self.requests_count / requests_time)
            print()
            print("Exiting...")
            exit()


if __name__ == '__main__':
    async def main():
        a = AioAutobuy(sale_id="135970432061947904", box_num=1, use_proxy=True)
        a.sale_start_time = time.time() * 1000 + 4000
        a.sec_to_stop = 5
        await a.run()

        print(a.sale_start_time)
        print(a.is_auth)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
