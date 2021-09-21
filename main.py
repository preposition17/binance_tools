import os
import time
import asyncio

from utils import print_table
from utils import get_sales_list

from batchmode import BatchMode
from singlemod import AioSingleMode
from autobuy import AioAutobuy


sales_list = get_sales_list()

modes = [
    '[1] Get batched boxes',
    '[2] Single parsing mode',
    '[3] AutoBuy mode'
]


if __name__ == '__main__':
    for i, sale in enumerate(sales_list[:10]):
        print(f'[{i}]', sale["name"])
    sale_number = int(input("Select sale: "))
    selected_sale_serial_num = sales_list[sale_number]["serial_num"]
    selected_sale_id = sales_list[sale_number]["id"]
    print("\nSelected sale: ", sales_list[sale_number]["name"], end="\n\n")

    for mode in modes:
        print(mode)
    selected_mode = int(input("Select mode: "))


    if selected_mode == 1:
        batch_size = int(input("Enter minimum batch size: ")) - 1
        batch_parser = BatchMode(selected_sale_serial_num)
        batch_parser.proxy_file = os.path.join("proxy", "proxy_batch.txt")
        is_bot = False
        if input("Use a telegram bot? (y/n) ").lower() == "y":
            is_bot = True
            batch_parser.send_to_telegram(batch_size=batch_size)
        else:
            def get_batched_boxes():
                all_batched_boxes = batch_parser.get_batch_boxes(batch_size)
                print_table(all_batched_boxes)

            while True:
                get_batched_boxes()
                time.sleep(3)


    if selected_mode == 2:
        if input("Use a telegram bot? (y/n) ").lower() == "y":
            single_parser = AioSingleMode(sale_serial_number=selected_sale_serial_num, use_bot=True, use_proxy=False)
        else:
            single_parser = AioSingleMode(sale_serial_number=selected_sale_serial_num, use_bot=False, use_proxy=False)

        single_parser.proxy_file = os.path.join("proxy", "proxy_single.txt")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(single_parser.run())


    if selected_mode == 3:
        box_num = int(input("Enter box num: "))

        async def autobuy_run():
            auto_buy = AioAutobuy(sale_id=selected_sale_id, box_num=box_num, use_proxy=True)
            auto_buy.logger_file = os.path.join("logs", "autobuy.log")
            auto_buy.env_file = ".env"
            auto_buy.proxy_file = os.path.join("proxy", "proxy_autobuy.txt")
            auto_buy.sale_start_time = time.time() * 1000 + 4000
            auto_buy.sec_to_stop = 5
            await auto_buy.run()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(autobuy_run())
