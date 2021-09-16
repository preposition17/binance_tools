import os
import json

import requests
import tabulate
from dotenv import load_dotenv


def get_box_url_from_id(box_id):
    box_url = f'https://www.binance.com/ru/nft/goods/blindBox/detail?productId={box_id}&isOpen=false&isProduct=1'
    return box_url


def get_sales_list():
    _sales_list = requests.get(
        url="https://www.binance.com/bapi/nft/v1/public/nft/mystery-box/list?page=1&size=100").json()["data"]
    sales_list = [{
        'name': sale_data["name"],
        'serial_num': sale_data["serialsNo"],
        'id': sale_data["productId"],
        'start_time': sale_data["startTime"]
    } for sale_data in _sales_list]
    return sales_list


def print_dict(m_dict):
    print(json.dumps(m_dict, indent=4, sort_keys=True))


def print_table(_list: list):
    # header = _list[0].keys()
    # rows = [x.values() for x in _list]

    # for _dict in _list:
    #     if _dict:
    #         header = _dict.keys()
    #         rows = [x.values() for x in _list if x]
    #         # rows = []
    #         # for __dict in _list:
    #         #     if __dict:
    #         #         rows.append(__dict.values())
    #         break
    #     else:
    #         continue

    for _dict in _list:
        try:
            header = _dict.keys()
            rows = [x.values() for x in _list if x is not None]
            print(tabulate.tabulate(rows, header))
            break
        except:
            continue




def get_cookies(cookies_string):
    _cookies_list = cookies_string.split("; ")
    cookies_list = [[cookie.split("=")[0], cookie.split("=")[1]] for cookie in _cookies_list]
    return cookies_list


if __name__ == '__main__':
    pass
