import json
import os
import re
from datetime import datetime
import subprocess
from auto_miyoushe_signin import (
    adb_swipe,
    get_OCR_result,
    get_resolution,
    get_screenshot,
    get_tab_height,
    send_notify,
)

import yaml

from paddleocr import PaddleOCR
import logging
import logreset


# def get_screenshot():
#     os.system("adb shell screencap -p /sdcard/screen.png")
#     os.system("adb pull /sdcard/screen.png .")
if __name__ == "__main__":
    logreset.reset_logging()  # before you logging setting
    # 使用logging模块配置日志输出格式和级别
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", level="INFO"
    )
    folder_name = "screenshots"
    os.makedirs(folder_name, exist_ok=True)
    # print("开始识别")
    screenshot_path = get_screenshot()
    result = get_OCR_result(screenshot_path)
    # print(f"result: {result}")
    # pattern = r"(\d+)月已累计签到(\d+)天"
    # for i in result:
    #     text = i[1][0]
    #     match = re.search(pattern, text)
    #     if match:
    #         signed_days = match.group(2)
    #         logging.info(f"已签到天数 {signed_days}")
    # #         now = datetime.now().day
    #         print(now)
    #         print(i)
    #     # if "签到福利" in i[1][0]:
    #     #     logging.info(i)
    with open("data.json", "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False)
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
    # if os.path.exists("config.yml"):
    #     with open("config.yml", "r", encoding="utf-8") as file:
    #         config = yaml.safe_load(file)
    #         logging.info(config)
    # else:
    #     logging.error("未检测到 config.yml 配置文件，请配置后重试")
    #     exit(1)
    # notify_message = "测试通知"
    # send_notify("米游社签到通知", notify_message, config.get("ONEPUSH_CONFIG", []))
    # 运行ADB命令以获取屏幕分辨率
    # print(get_resolution())
    # 先判断tab 的位置，然后拖拽
    # x, y = get_resolution()
    # height = get_tab_height()
    # logging.info(f"height: {height}")
    # adb_swipe(0, height, x // 2, height)
    # adb_swipe(0, 116, x // 2, 116)
