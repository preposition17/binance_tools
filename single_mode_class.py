from datetime import datetime
from functools import partial
import random
from multiprocessing import Pool

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

        self.sale_serial_number = sale_serial_number

    def get_single_product_data(self, product_id):
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
                product_item_response = _product_item_response.json()

                if product_item_response and product_item_response["success"] and product_item_response["data"] \
                        ["mysteryBoxProductDetailVo"]:
                    product_data = {
                        'sale_id': product_item_response["data"]["mysteryBoxProductDetailVo"]["serialsNo"],
                        'id': product_item_response["data"]["productDetail"]["id"],
                        'left_stock_num': product_item_response["data"]["productDetail"]["leftStockNum"],
                        'batch_num': product_item_response["data"]["productDetail"]["batchNum"],
                        'price': product_item_response["data"]["productDetail"]["amount"],
                        'price_per_one': float(product_item_response["data"]["productDetail"]["amount"]) / \
                                         float(product_item_response["data"]["productDetail"]["batchNum"]),
                        'currency': product_item_response["data"]["productDetail"]["currency"],
                        'nft_type': product_item_response["data"]["productDetail"]["nftType"],
                        'trade_type': product_item_response["data"]["productDetail"]["tradeType"],
                        'status': product_item_response["data"]["productDetail"]["status"],
                        'url': get_box_url_from_id(product_item_response["data"]["productDetail"]["id"]),
                        'success': True
                    }
                    return product_data
                else:
                    return {'success': False}

            except:
                i += 1
                if i > 10:
                    print("Global error")
                    break
                continue

    def filter_product(self, product_data: dict):
        # Filter product by criteria
        # Return product for user if criteria fit
        # Else return nones data

        # TODO: Nice printing

        if product_data["success"]:
            if product_data["trade_type"] == 0 \
                    and product_data["currency"] == "BUSD" \
                    and product_data["left_stock_num"] > 0 \
                    and product_data["nft_type"] == 2 \
                    and product_data["sale_id"] == self.sale_serial_number \
                    and product_data["status"] == 1:

                if self.use_bot:
                    _bot = telebot.TeleBot(self.bot_token)

                    msg = f'New product {product_data["id"]}\n'
                    msg += f'Price: {round(float(product_data["price"]), 2)} {product_data["currency"]}\n'
                    if product_data["batch_num"] > 1:
                        msg += f'Batch num: {product_data["batch_num"]}\n'
                        msg += f'Price per one: {round(float(product_data["price"]) / float(product_data["batch_num"]), 2)}'
                        msg += f'{product_data["currency"]}\n'
                    msg += f'URL: {get_box_url_from_id(product_data["id"])}'
                    _bot.send_message(chat_id=self.chat_id, text=msg)

                else:
                    print(datetime.now().strftime('%H:%M:%S.%f')[:-4],
                          product_data["id"],
                          product_data["batch_num"],
                          product_data["price"],
                          float(product_data["price"]) / float(product_data["batch_num"]),
                          product_data["currency"],
                          get_box_url_from_id(product_data["id"])
                          )
                return str(product_data["id"])

    def get_filtered_product(self, product_id, bot=None):
        # Print and return valid and filtered product from <sale_id>

        _product_data = self.get_single_product_data(product_id=product_id)
        return self.filter_product(product_data=_product_data)

    def get_all_parsed_products_data(self, product_ids: list, proc_num: int = 12, bot=None):
        # Get all products data from product_ids list with multiprocessing
        while True:
            with Pool(proc_num) as p:
                # parsed_products_data = [_box for _box in p.imap(partial(self.get_filtered_product),
                #                                                 product_ids) if _box is not None]
                parsed_products_data = []
                for _box in p.imap(partial(self.get_filtered_product), product_ids):
                    if _box:
                        parsed_products_data.append(_box)

            return parsed_products_data

    def get_all_listed_products_id(self):
        # Return all listed products from <sale_id>

        payload = {"page": 1, "size": 100,
                   "params": {"keyword": "",
                              "nftType": None,
                              "orderBy": "list_time",
                              "orderType": "-1",
                              "serialNo": [self.sale_serial_number],
                              "tradeType": None}
                   }
        # _all_products_list = requests.post('https://www.binance.com/bapi/nft/v1/public/nft/market-mystery/mystery-list',
        #                                    json=payload).json()["data"]["data"]

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
        _generated_ids_list = get_product_ids(_listed_product_ids[0], 100)
        __filtered_ids_list = list(set(_generated_ids_list) - set(_listed_product_ids))
        _filtered_ids_list = list(set(__filtered_ids_list) - set(filtered_ids_list))

        _latest_products_id = self.get_all_parsed_products_data(product_ids=_filtered_ids_list) + filtered_ids_list

        return _latest_products_id

    def start_parsing(self):
        latest_products_id = []
        while True:
            try:
                latest_products_id = self.get_latest_products(latest_products_id)
            except KeyboardInterrupt:
                break


if __name__ == '__main__':
    sale_id = str(133912760290440192)
    parser = SingleMode(sale_id, True)
    parser.start_parsing()
