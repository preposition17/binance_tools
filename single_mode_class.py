import os
from datetime import datetime
from functools import partial
import random
from multiprocessing import Pool
from multiprocessing import Manager
import time
import datetime

import requests

from utils import get_box_url_from_id

import telebot


def get_proxy():
    with open("proxy_single.txt", "r") as file:
        proxy_list = file.read().splitlines()
        return random.choice(proxy_list)


def get_product_ids(product_id, ids_range: int):
    # Return list of ids from <product_id> to <ids_range>

    _product_ids = [str(int(product_id) + _id + 1) for _id in range(ids_range)]
    return _product_ids


class SingleMode:
    def __init__(self, sale_serial_number, use_bot):
        self.bot_token = "1986983151:AAHUnMm6IFFXrjpx-wsvOGrvtqkBWFWzqe0"
        self.chat_id = -414790413
        self.use_bot = use_bot
        self.parsing_time = 50

        self.sale_serial_number = sale_serial_number


    def get_single_product_data(self, product_id):
        # TODO Errors nice printing
        # Return single product data from <product_id> if request successful (need proxy)
        # Else return only { success: false }

        m_request_url = 'https://www.binance.com/bapi/nft/v1/friendly/nft/nft-trade/product-detail'
        m_payload = {"productId": str(product_id)}
        i = 0
        while True:
            try:
                _product_item_response = requests.post(url=m_request_url,
                                                       json=m_payload,
                                                       proxies={"http": get_proxy()})
                if _product_item_response.status_code != 200:
                    _product_item_response.raise_for_status()
                product_item_response = _product_item_response.json()

                if product_item_response and product_item_response["success"] and product_item_response["data"]["mysteryBoxProductDetailVo"] \
                and product_item_response["data"]["productDetail"]["tradeType"] == 0 \
                and product_item_response["data"]["productDetail"]["currency"] == "BUSD" \
                and product_item_response["data"]["productDetail"]["leftStockNum"] > 0 \
                and product_item_response["data"]["productDetail"]["nftType"] == 2 \
                and product_item_response["data"]["mysteryBoxProductDetailVo"]["serialsNo"] == self.sale_serial_number \
                and product_item_response["data"]["productDetail"]["status"] == 1:
                    product_id = product_item_response["data"]["productDetail"]["id"]
                    product_amount = round(float(product_item_response["data"]["productDetail"]["amount"]), 2)
                    product_batch_num = product_item_response["data"]["productDetail"]["batchNum"]
                    product_currency = product_item_response["data"]["productDetail"]["currency"]

                    if self.use_bot:
                        _bot = telebot.TeleBot(self.bot_token)

                        msg = f'New product {product_id}\n'
                        msg += f'Price: {product_amount} '\
                               f'{product_currency}\n'
                        if product_batch_num > 1:
                            msg += f'Batch num: {product_batch_num}\n'
                            msg += f'Price per one: {round(product_amount / product_batch_num)}'
                            msg += f'{product_currency}\n'
                        msg += f'URL: {get_box_url_from_id(product_id)}\n'
                        while True:
                            try:
                                _bot.send_message(chat_id=self.chat_id, text=msg, parse_mode='HTML')
                                break

                            # Telegram errors
                            except Exception as ex:
                                if "429" in str(ex):
                                    time_to_sleep = int(str(ex).split(" ")[-1])
                                    print(datetime.now().strftime('%H:%M:%S.%f')[:-4],
                                          os.getpid(),
                                          "Too Many Requests to Telegram. Waiting",
                                          time_to_sleep,
                                          "seconds.")
                                    time.sleep(time_to_sleep)
                                else:
                                    print(os.getpid(), "Error while sending message.")
                                    print(ex)
                                continue

                    else:
                        print(datetime.now().strftime('%H:%M:%S.%f')[:-4],
                              product_id,
                              product_batch_num,
                              product_amount,
                              float(product_amount) / float(product_batch_num),
                              product_currency,
                              get_box_url_from_id(product_id)
                              )
                    return str(product_id)
                else:
                    break

            # Global errors
            except Exception as ex:
                i += 1

                if i > 9:
                    print(datetime.now().strftime('%H:%M:%S.%f')[:-4],
                          os.getpid(),
                          "Global while product parsing!")
                    print(ex)
                    break
                else:
                    if "Max retries" in str(ex):
                        print(datetime.now().strftime('%H:%M:%S.%f')[:-4],
                              os.getpid(),
                              "Too Many Requests to Binance. Waiting", 10, "seconds.")
                        time.sleep(10)
                    else:
                        print(datetime.now().strftime('%H:%M:%S.%f')[:-4],
                              "Error while product parsing: ", i)
                        print(ex)

                    continue

    def get_all_parsed_products_data(self, product_ids: list, proc_num: int = 6, bot=None):
        # Get all products data from product_ids list with multiprocessing
        while True:
            with Pool(proc_num) as p:
                # parsed_products_data = [_box for _box in p.imap(partial(self.get_filtered_product),
                #                                                 product_ids) if _box is not None]
                parsed_products_data = []
                for _box in p.imap(self.get_single_product_data, product_ids):
                    if _box:
                        parsed_products_data.append(_box)

            return parsed_products_data

    def get_all_listed_products_id(self):
        # Return all listed products from <sale_id>

        payload = {"page": 1, "size": self.parsing_time,
                   "params": {"keyword": "",
                              "nftType": None,
                              "orderBy": "list_time",
                              "orderType": "-1",
                              "serialNo": [self.sale_serial_number],
                              "tradeType": None}
                   }

        try_count = 0
        while True:
            try:
                _all_products_list = requests.post('https://www.binance.com/bapi/nft/v1/public/nft/market-mystery'
                                                   '/mystery-list',
                                                   json=payload).json()["data"]["data"]

                _listed_product_ids = [product_data["productId"] for product_data in _all_products_list]
                return _listed_product_ids
            except:
                if try_count > 10:
                    print("Fatal error while parsing all listed products.")
                    exit()
                try_count += 1
                continue

    def get_latest_products(self, filtered_ids_list):
        # Finally function

        _listed_product_ids = self.get_all_listed_products_id()
        _generated_ids_list = get_product_ids(_listed_product_ids[0], self.parsing_time)
        __filtered_ids_list = list(set(_generated_ids_list) - set(_listed_product_ids))
        _filtered_ids_list = list(set(__filtered_ids_list) - set(filtered_ids_list))

        _latest_products_id = self.get_all_parsed_products_data(product_ids=_filtered_ids_list) + filtered_ids_list

        return _latest_products_id

    def start_parsing(self):
        latest_products_id = []
        while True:
            try:
                latest_products_id = self.get_latest_products(latest_products_id)
                # print(self.queue.get())
            except KeyboardInterrupt:
                break


if __name__ == '__main__':
    sale_id = str(133912760290440192)
    parser = SingleMode(sale_id, True)
    parser.start_parsing()
