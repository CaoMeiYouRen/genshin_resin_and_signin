import os
import re
from datetime import datetime

from paddleocr import PaddleOCR
import json


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
    # 使用logging模块配置日志输出格式和级别

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
    date1 = datetime(2023, 8, 1, 10, 30)
    date2 = datetime(2023, 8, 1, 15, 45)

    # 比较两个datetime对象的日期部分
    if date1.date() == date2.date():
        print("两个datetime对象在同一天")
    else:
        print("两个datetime对象不在同一天")
