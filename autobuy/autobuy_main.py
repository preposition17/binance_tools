import os
import logging
import traceback
import time
from datetime import datetime
from multiprocessing import Process

import requests
from dotenv import load_dotenv
from fake_useragent import UserAgent

from utils import get_cookies


def get_time():
    _time = datetime.now().strftime("%H:%M:%S.%f")[:-4]
    return _time


class AutoBuy:
    def __init__(self, sale_id: str, box_num: int):
        self.logger = logging.getLogger("AutoBuy")
        logging.basicConfig(filename="logs/autobuy.log", level=logging.INFO)
        logging.info(f'\n{get_time()}: Autobuy initialization.')

        self.sale_id = sale_id
        self.box_num = box_num
        self.auth_url = "https://www.binance.com/bapi/accounts/v1/public/authcenter/auth"
        self.sale_data_url = f'https://www.binance.com/bapi/nft/v1/friendly/nft/mystery-box/detail'
        self.purchase_url = "https://www.binance.com/bapi/nft/v1/private/nft/mystery-box/purchase"

        load_dotenv(".env")
        __ua = UserAgent()
        self.user_agent = __ua.chrome
        self.__cookies_string = os.getenv('COOKIE')
        self.cookies = get_cookies(cookies_string=self.__cookies_string)
        self.csrf_token = os.getenv('CSRFTOKEN')
        self.__session = self.make_session()

        self.sale_start_time = self.get_sale_start_time()


    @staticmethod
    def get_proxy_list(looger):
        # Get list of proxies from <proxy.txt>

        logger.info(f'{get_time()}: Proxy list getting.')
        with open("proxy_autobuy.txt", "r") as file:
            proxy_list = file.read().splitlines()
            return proxy_list

    def make_session(self):
        # Make new session with tuned useragent, csrf token and cookies

        self.logger.info(f'{get_time()}: Requests session making.')
        _session = requests.Session()
        _session.headers.update({"csrftoken": self.csrf_token})
        _session.headers.update({"clienttype": "web"})
        _session.headers.update({"user-agent": self.user_agent})
        for cookie in self.cookies:
            _session.cookies.set(cookie[0], cookie[1])

        return _session

    def get_session(self):
        # Return generated session with <make_session> if exist
        # Else generate session and return it

        self.logger.info(f'{get_time()}: Requests session getting.')
        if self.__session:
            return self.__session
        else:
            self.__session = self.make_session()
            return self.__session

    def auth(self):
        # Try to auth on Binance
        # Return True if auth success
        # Else return False and print unsuccessful message

        self.logger.info(f'{get_time()}: Authentication.')
        _session = self.get_session()
        _response = _session.post(self.auth_url)
        if _response.json()["success"]:
            logging.info(f'{get_time()}: Authentication successful.')
            return True
        else:
            logging.error(f'{get_time()}: Authentication unsuccessful.')
            print("Authentication unsuccessful.")
            print("Message: ", _response.json()["message"])
            exit()

    def get_sale_start_time(self):
        # Get sale start time in unix time if response successful
        # Else return False

        self.logger.info(f'{get_time()}: Sale start time getting.')
        _session = self.get_session()
        _response = _session.get(self.sale_data_url, params={"productId": self.sale_id})
        if _response.json()["success"]:
            return _response.json()["data"]["startTime"]
        else:
            logging.error(f'{get_time()}: Sale start time getting unsuccessful.')
            return False

    def purchase(self):
        # Start purchase trying function
        # If buy is success quiting from loop
        self.logger.info(f'{get_time()}: Waiting to sale...')
        while True:
            time_to_sale = self.sale_start_time - time.time() * 1000
            print("Time to sale: ", round(time_to_sale / 1000, 2), 'seconds')

            if time_to_sale < 1500:
                logging.info(f'{get_time()}: Trying to purchase...')
                print("Trying to purchase...")
                self.purchase_trying()

    def purchase_trying(self):
        # Trying to purchase box with multiprocessing
        # Many times per seconds try to purchase

        proxy_list = self.get_proxy_list(looger=self.logger)
        self.logger.info(f'{get_time()}: Starting purchase with {len(proxy_list)} processes.')

        _session = self.get_session()
        processes = []
        for _proxy in proxy_list:
            process = Process(target=self.purchase_loop, args=(_proxy, _session))
            processes.append(process)
            process.start()

        for _process in processes:
            _process.join()


    def purchase_loop(self, _proxy, _session):
        # Purchasing loop for mp

        self.logger.info(f'{get_time()}: Starting purchasing loop on process #{os.getpid()}.')
        while True:
            try:
                self.logger.info(f'{get_time()}: Trying purchase on process #{os.getpid()}.')
                self.purchase_request(_session, _proxy=_proxy)
                break
            except Exception as ex:
                self.logger.error(f'{get_time()}: Unsuccessful purchase on process #{os.getpid()}.'
                              f'\n{traceback.format_exc()}')
                print(f'{get_time()}: Error.')
                print(ex)
                continue
            except KeyboardInterrupt:
                self.logger.info(f'{get_time()}: Exiting on process #{os.getpid()}.')
                exit()



    def purchase_request(self, _session, _proxy: str):
        _response = _session.post(self.purchase_url,
                                  json={"number": self.box_num, "productId": self.sale_id},
                                  proxies={"http": _proxy})

        try:
            if _response.json()["success"]:
                print("YYYYYYYYYEEEEEEEEEEEEAAAAAAAAAHHHHHHHHH")
            self.logger.info(f'{get_time()}: {_response.json()["message"]}, {_response.json()["success"]} on process #{os.getpid()}.')
            print(f'{get_time()}: {_response.json()["message"]}, {_response.json()["success"]}')
        except Exception as ex:
            self.logger.error(f'{get_time()}: Error on process #{os.getpid()}.'
                          f'\n{traceback.format_exc()}')
            print(f'{datetime.now().strftime("%H:%M:%S.%f")[:-4]}: No data.')


if __name__ == '__main__':
    auto_buy = AutoBuy(sale_id="134493380666328064", box_num=1)
    auth_successful = auto_buy.auth()
    auto_buy.sale_start_time = time.time() * 1000 + 5000
    # auto_buy.sale_start_time = 1631458260000
    auto_buy.purchase()
