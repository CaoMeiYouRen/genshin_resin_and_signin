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

    print("开始识别")
    screenshot_path = get_screenshot()
    result = get_OCR_result(screenshot_path)
    print(f"result: {result}")
    pattern = r"(\d+)月已累计签到(\d+)天"
    for i in result:
        text = i[1][0]
        match = re.search(pattern, text)
        if match:
            print(match.group(2))
            now = datetime.now().day
            print(now)
            print(i)
        # if "签到福利" in i[1][0]:
        #     logging.info(i)
    with open("data.json", "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False)
    # for i in result:
    #     coordinates = i[0]
    #     center_x, center_y = calculate_center(coordinates)
    #     logging.info("中心点坐标：({}, {})".format(center_x, center_y))

    # coordinates = [
    #     [1099.0, 1227.0],
    #     [1279.0, 1227.0],
    #     [1279.0, 1293.0],
    #     [1099.0, 1293.0],
    # ]

    # center_x, center_y = calculate_center(coordinates)
    # logging.info("中心点坐标：({}, {})".format(center_x, center_y))

# """离线百度文本识别"""
# ocr = PaddleOCR(
#     use_angle_cls=True, lang="ch"
# )  # need to run only once to download and load model into memory
# img_path = "screen.png"
# result = ocr.ocr(img_path, cls=True)
# result = result[0]

# debug   显示结果
# image = Image.open(img_path).convert('RGB')
# boxes = [line[0] for line in result]
# txts = [line[1][0] for line in result]
# scores = [line[1][1] for line in result]
# im_show = draw_ocr(image, boxes, txts, scores, font_path='./fonts/simfang.ttf')
# im_show = Image.fromarray(im_show)
# im_show.save('result.jpg')

# for i in result:
#     if "回顶部" in i[1][0]:
#         center = i[0][0]
#         break
# os.system("adb shell input tap {} {}".format(center[0], center[1]))


"""联网百度文本识别"""
# result = subprocess.check_output("paddleocr --image_dir screen.png", shell=True)
