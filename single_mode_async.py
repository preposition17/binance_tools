import os
from datetime import datetime
import random
import time
import asyncio
import aiohttp
import traceback

from utils import get_box_url_from_id

import telebot


def get_proxy_list():
    # Getting proxy list from file
    with open("proxy_single.txt", "r") as file:
        return file.read().splitlines()


def proxy_generator(proxy_list):
    # Infinity consistently returning proxy from <proxy_list>

    proxy_num = 0
    while True:
        yield proxy_list[proxy_num]
        proxy_num += 1
        if proxy_num == len(proxy_list):
            proxy_num = 0


def get_product_ids(product_id, ids_range: int):
    # Return list of ids from <product_id> to <ids_range>

    _product_ids = [str(int(product_id) + _id + 1) for _id in range(ids_range)]
    return _product_ids


class AioSingleMode:
    def __init__(self, sale_serial_number, use_bot, use_proxy):
        self.listed_products_url = 'https://www.binance.com/bapi/nft/v1/public/nft/market-mystery/mystery-list'
        self.single_product_data_url = 'https://www.binance.com/bapi/nft/v1/friendly/nft/nft-trade/product-detail'

        self.use_proxy = use_proxy
        proxy_list = get_proxy_list()
        self.proxy_generator = proxy_generator(proxy_list)

        self.bot_token = "1986983151:AAHUnMm6IFFXrjpx-wsvOGrvtqkBWFWzqe0"
        self.chat_id = -414790413
        self.use_bot = use_bot
        self.bot = None

        self.parsing_size = 50
        self.sale_serial_number = sale_serial_number
        self.is_listed_products_changed = False
        self.listed_products_id = list()
        self.market_low_price = None
        self.checked_products_id = list()
        self.checked_products_data = list()

        if self.use_bot:
            self.bot = telebot.AsyncTeleBot(token=self.bot_token)


    async def run(self):
        # Creating main tasks and running it
        async with aiohttp.ClientSession() as _session:
            tasks = [
                asyncio.create_task(self.get_market_low_price(session=_session), name="Low Price"),
                asyncio.create_task(self.get_listed_products_id(session=_session), name="Listed products"),
                asyncio.create_task(self.main_loop(session=_session), name="Main loop"),
            ]

            await asyncio.gather(*tasks)


    async def main_loop(self, session):
        # Main loop
        # Getting latest products and print it or send it to telegram

        while True:
            await self.get_latest_products(session=session)

            if self.use_bot:
                await self.send_checked_data_telegram()
            else:
                await self.print_checked_data()

            await asyncio.sleep(0.1)


    async def get_market_low_price(self, session):
        # Getting market low price from <sale_id> and put it to <self.market_low_price>

        payload = {"page": 1, "size": 1,
                   "params": {"keyword": "",
                              "nftType": "2",
                              "orderBy": "amount_sort",
                              "orderType": "1",
                              "serialNo": [self.sale_serial_number],
                              "tradeType": "0"}
                   }
        while True:
            try_count = 1
            while True:
                try:
                    async with session.post(self.listed_products_url, json=payload) as response:
                        _data = await response.json()
                        low_price = float(_data["data"]["data"][0]["amount"])
                        if low_price != self.market_low_price:
                            self.market_low_price = low_price

                    await asyncio.sleep(5)
                    break
                except Exception as ex:
                    try_count += 1
                    print("Error: ", ex)
                    print("Error count: ", try_count)
                    print(traceback.format_exc())
                    if try_count == 5:
                        print("Global error while getting low price, breaking...")
                        break


    async def get_listed_products_id(self, session):
        # Set all listed products from <sale_id> to <self.listed_products_id>

        payload = {"page": 1, "size": self.parsing_size,
                   "params": {"keyword": "",
                              "nftType": None,
                              "orderBy": "list_time",
                              "orderType": "-1",
                              "serialNo": [self.sale_serial_number],
                              "tradeType": None}
                   }
        while True:
            try_count = 1
            while True:
                try:
                    async with session.post(self.listed_products_url, json=payload) as response:
                        _data = await response.json()
                        listed_products_id = [product_data["productId"] for product_data in _data["data"]["data"]]
                        if sorted(listed_products_id) != sorted(self.listed_products_id):
                            self.is_listed_products_changed = True
                            self.listed_products_id = listed_products_id

                    await asyncio.sleep(5)
                    break
                except Exception as ex:
                    try_count += 1
                    print("Error: ", ex)
                    print("Error count: ", try_count)
                    print(traceback.format_exc())
                    if try_count == 5:
                        print("Global error while getting listed products data, breaking...")
                        break


    async def get_checked_product(self, session, product_id):
        # Set all checked ids and datas to <self.checked_products_id> and <self.checked_products_data>

        _product_data = await self.get_single_product_data(session=session, product_id=product_id)
        if _product_data and _product_data["success"]:
            self.checked_products_id.append(str(_product_data["data"]["productDetail"]["id"]))
            _checked_data = await self.check_product(data=_product_data)
            if _checked_data:
                self.checked_products_data.append(_checked_data)


    async def get_latest_products(self, session):
        # Run tasks for get latest products data

        if self.is_listed_products_changed:
            self.is_listed_products_changed = False
            _generated_ids_list = get_product_ids(self.listed_products_id[0], self.parsing_size)
            __filtered_ids_list = list(set(_generated_ids_list) - set(self.listed_products_id))
            _filtered_ids_list = list(set(__filtered_ids_list) - set(self.checked_products_id))

            tasks = []
            for _id in _filtered_ids_list:
                task = asyncio.create_task(self.get_checked_product(session, _id), name=_id)
                tasks.append(task)
            await asyncio.gather(*tasks)


    async def get_single_product_data(self, session, product_id):
        # TODO: Add proxy
        # Return single product data from <product_id> if request successful (need proxy)
        # Else return only { success: false }

        payload = {"productId": str(product_id)}

        try_count = 1
        while True:
            try:
                async with session.post(self.single_product_data_url,
                                        json=payload,
                                        proxy=f'http://{next(self.proxy_generator)}' if self.use_proxy else None) \
                        as response:
                    _data = await response.json()
                    return _data

            except Exception as ex:
                try_count += 1
                print("Error: ", ex)
                print("Error count: ", try_count)
                print(traceback.format_exc())
                if try_count == 5:
                    print("Global error while getting single product data, returning None...")
                    return None


    async def check_product(self, data: dict):
        # Check product from <data> and return if good criteria

        if (data and data["success"]
                and float(data["data"]["productDetail"]["amount"]) /
                data["data"]["productDetail"]["batchNum"] < self.market_low_price + 1
                and data["data"]["mysteryBoxProductDetailVo"]
                and data["data"]["productDetail"]["tradeType"] == 0
                and data["data"]["productDetail"]["currency"] == "BUSD"
                and data["data"]["productDetail"]["leftStockNum"] > 0
                and data["data"]["productDetail"]["nftType"] == 2
                and data["data"]["mysteryBoxProductDetailVo"]["serialsNo"] == self.sale_serial_number
                and data["data"]["productDetail"]["status"] == 1):
            product_id = data["data"]["productDetail"]["id"]
            product_amount = round(float(data["data"]["productDetail"]["amount"]), 2)
            product_batch_num = data["data"]["productDetail"]["batchNum"]
            product_currency = data["data"]["productDetail"]["currency"]
            return {
                "product_id": product_id,
                "product_amount": product_amount,
                "product_batch_num": product_batch_num,
                "product_currency": product_currency,
                "product_url": get_box_url_from_id(product_id)
            }
        else:
            return None


    async def print_checked_data(self):
        # Printing checked products and delete it from <self.checked_products_data>

        for num, data in enumerate(self.checked_products_data):
            print(self.checked_products_data.pop(num))


    async def send_checked_data_telegram(self):
        # Sending checked products to telegram and delete it from <self.checked_products_data>

        for num, data in enumerate(self.checked_products_data):
            msg = f'Market lowest price: {self.market_low_price} BUSD\n\n'
            msg += f'New product {data["product_id"]}\n'
            msg += f'Price: {data["product_amount"]} ' \
                   f'{data["product_currency"]}\n'
            if data["product_batch_num"] > 1:
                msg += f'Batch num: {data["product_batch_num"]}\n'
                msg += f'Price per one: {round(data["product_amount"] / data["product_batch_num"])}'
                msg += f' {data["product_currency"]}\n'
            msg += f'URL: {data["product_url"]}\n'
            self.bot.send_message(chat_id=self.chat_id, text=msg)
            self.checked_products_data.pop(num)
            await asyncio.sleep(0.25)


if __name__ == '__main__':
    async def main():
        a = AioSingleMode(str(133948907490164736), use_bot=True, use_proxy=False)
        await a.run()


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
