import os
import json
from datetime import datetime

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


def print_dict(_dict):
    # Print readable dict from <_dict>

    print(json.dumps(_dict, indent=4, sort_keys=True))


def print_table(_list: list):
    # Print readable table from <_list>

    for _dict in _list:
        try:
            header = _dict.keys()
            rows = [x.values() for x in _list if x is not None]
            print(tabulate.tabulate(rows, header))
            break
        except:
            continue


def get_cookies(cookies_string: str) -> list:
    # Get list of cookies from cookie string
    # [ [name, value], ... ]

    _cookies_list = cookies_string.split("; ")
    cookies_list = [[cookie.split("=")[0], cookie.split("=")[1]] for cookie in _cookies_list]
    return cookies_list


def get_proxy_list(filename: str) -> list:
    # Return proxy list from <filename> file

    with open(filename, "r") as file:
        proxy_list = file.read().splitlines()
        return proxy_list


def proxy_generator(proxy_list):
    # Infinity consistently returning proxy from <proxy_list>

    proxy_num = 0
    while True:
        yield proxy_list[proxy_num]
        proxy_num += 1
        if proxy_num == len(proxy_list):
            proxy_num = 0


def get_time():
    _time = datetime.now().strftime("%H:%M:%S.%f")[:-4]
    return _time
