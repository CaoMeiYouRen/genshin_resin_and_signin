import os
import re
from datetime import datetime
from auto_miyoushe_signin import send_notify

import yaml

from paddleocr import PaddleOCR
import logging
import logreset


# def get_screenshot():
#     os.system("adb shell screencap -p /sdcard/screen.png")
#     os.system("adb pull /sdcard/screen.png .")
def calculate_center(coordinates):
    x_sum = 0
    y_sum = 0
    num_points = len(coordinates)

    for point in coordinates:
        x_sum += point[0]
        y_sum += point[1]

    center_x = x_sum / num_points
    center_y = y_sum / num_points

    return center_x, center_y


def get_screenshot():
    os.system("adb shell screencap -p /sdcard/screen.png")
    # datetime_now = datetime.datetime.now()
    # formatted_now = datetime_now.strftime("%d_%H_%M_%S")
    # screenshot_path = f"./screenshots/screen_{formatted_now}.png"
    screenshot_path = f"./screenshots/screen.png"
    os.system(f"adb pull /sdcard/screen.png {screenshot_path}")

    # todo 直接读取到内存
    return screenshot_path


def get_OCR_result(screenshot_path):
    ocr = PaddleOCR(
        use_angle_cls=True, lang="ch", show_log=False
    )  # need to run only once to download and load model into memory , bin=True
    result = ocr.ocr(screenshot_path, cls=True)
    result = result[0]
    return result


if __name__ == "__main__":
    logreset.reset_logging()  # before you logging setting
    # 使用logging模块配置日志输出格式和级别
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", level="INFO"
    )
    # print("开始识别")
    # screenshot_path = get_screenshot()
    # result = get_OCR_result(screenshot_path)
    # print(f"result: {result}")
    # pattern = r"(\d+)月已累计签到(\d+)天"
    # for i in result:
    #     text = i[1][0]
    #     match = re.search(pattern, text)
    #     if match:
    #         print(match.group(2))
    #         now = datetime.now().day
    #         print(now)
    #         print(i)
    #     # if "签到福利" in i[1][0]:
    #     #     logging.info(i)
    # with open("data.json", "w", encoding="utf-8") as file:
    #     json.dump(result, file, ensure_ascii=False)
    # last_sign_in_day = datetime.now().isoformat()
    # data = {"last_sign_in_day": last_sign_in_day}
    # with open("last_sign_in_day.json", "w", encoding="utf-8") as f:
    #     json.dump(data, f)

    # with open("last_sign_in_day.json", "r") as file:
    #     data = json.load(file)
    # # 将字符串转换为datetime对象
    # last_sign_in_day = data["last_sign_in_day"]
    # last_sign_in_day = datetime.fromisoformat(last_sign_in_day)

    # # 打印datetime对象
    # print(last_sign_in_day)

    # 创建两个datetime对象
    # date1 = datetime(2023, 8, 1, 10, 30)
    # date2 = datetime(2023, 8, 1, 15, 45)

    # # 比较两个datetime对象的日期部分
    # if date1.date() == date2.date():
    #     logging.info("两个datetime对象在同一天")
    # else:
    #     logging.info("两个datetime对象不在同一天")
    if os.path.exists(".env.local"):
        with open("config.yml", "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            logging.info(config)
    else:
        logging.error("未检测到 config.yml 配置文件，请配置后重试")
        exit(1)
    notify_message = "测试通知"
    send_notify("米游社签到通知", notify_message, config.get("ONEPUSH_CONFIG", []))
