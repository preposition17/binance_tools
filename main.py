import time

from utils import print_table
from utils import get_sales_list

from boxes import Boxes
from single_mode_class import SingleMode
from autobuy import AutoBuy


sales_list = get_sales_list()

modes = [
    '[0] Get all boxes',
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

    if selected_mode == 0:
        def get_all_boxes():
            boxes = Boxes(selected_sale_serial_num)
            all_boxes = boxes.get_all_boxes_list()
            print_table(all_boxes)
            is_reload = input("Reload? (y/n) ")
            if is_reload == 'y':
                get_all_boxes()
        get_all_boxes()


    if selected_mode == 1:
        batch_size = int(input("Enter minimum batch size: ")) - 1
        boxes = Boxes(selected_sale_serial_num)
        is_bot = False
        if input("Use a telegram bot? (y/n) ").lower() == "y":
            is_bot = True
            boxes.send_to_telegram(batch_size=batch_size)
        else:
            def get_batched_boxes():

                all_batched_boxes = boxes.get_batch_boxes(batch_size)
                print_table(all_batched_boxes)

            while True:
                get_batched_boxes()
                time.sleep(3)


    if selected_mode == 2:
        if input("Use a telegram bot? (y/n) ").lower() == "y":
            parser = SingleMode(sale_serial_number=selected_sale_serial_num, use_bot=True)
            parser.start_parsing()
        else:
            parser = SingleMode(sale_serial_number=selected_sale_serial_num, use_bot=False)
            parser.start_parsing()


    if selected_mode == 3:
        box_num = int(input("Enter box num: "))
        auto_buy = AutoBuy(sale_id=selected_sale_id, box_num=box_num)
        auth_successful = auto_buy.auth()
        # auto_buy.sale_start_time = time.time()*1000+2000
        auto_buy.purchase()
