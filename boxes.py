import random
import time

import requests

from utils import print_dict
from utils import get_box_url_from_id

import telebot

bot_token = "1958791777:AAEetFm6ZWzm8pUvrJbeSQXk0s3LbI7BM-c"
chat_id = -1001524854248


class Boxes:
    def __init__(self, serial_number):
        # self.__serial_number = "131943993880671232"
        self.__serial_number = str(serial_number)
        self.__all_boxes = None
        self.__all_batched_boxes = None


    @staticmethod
    def get_proxy():
        with open("proxy_batch.txt", "r") as file:
            proxy_list = file.read().splitlines()
            return random.choice(proxy_list)


    def get_all_boxes_list(self, size=10000):
        payload = {"page": "1",
                   "size": size,
                   "params": {"keyword": "",
                              "nftType": "2",
                              "orderBy": "amount_sort",
                              "orderType": "1",
                              "serialNo": [self.__serial_number],
                              "tradeType": "0"}
                   }
        all_boxes_list = requests.post('https://www.binance.com/bapi/nft/v1/public/nft/market-mystery/mystery-list',
                                       json=payload,
                                       proxies={"http": self.get_proxy()}).json()["data"]["data"]
        self.__all_boxes = all_boxes_list
        return all_boxes_list

    def get_batch_boxes(self, batch_size, size=10000):
        all_boxes_list = self.get_all_boxes_list(size=size)
        all_batch_boxes = []
        for box_item in all_boxes_list:
            if int(box_item["batchNum"]) > batch_size and box_item["currency"] == "BUSD":
                _box_item = {
                    'id': box_item["productId"],
                    'batch_num': box_item["batchNum"],
                    'price': box_item["amount"],
                    'price_per_one': float(box_item["amount"]) / float(box_item["batchNum"]),
                    'currency': box_item["currency"],
                    'url': get_box_url_from_id(box_item["productId"])
                }
                all_batch_boxes.append(_box_item)
        batch_boxes_sorted = sorted(all_batch_boxes, key=lambda k: k['price_per_one'], reverse=True)
        return batch_boxes_sorted


    def send_to_telegram(self, batch_size):
        bot = telebot.TeleBot(bot_token)

        while True:
            batch_boxes = self.get_batch_boxes(batch_size=batch_size)[-10:]
            msg = '-------------------------------------------------\n'
            for batch_box in batch_boxes:
                msg += f'Batch num: {batch_box["batch_num"]}\n'
                msg += f'Price per one: {batch_box["price_per_one"]} {batch_box["currency"]}\n'
                msg += f'URL:                    <a href="{batch_box["url"]}">BINANCE</a>\n'
                msg += '-------------------------------------------------\n'
                # print(msg)
            bot.send_message(chat_id, text=msg, parse_mode='html')
            time.sleep(2)


if __name__ == '__main__':
    boxes = Boxes("131643184307554304")
    boxes.send_to_telegram(batch_size=3)
