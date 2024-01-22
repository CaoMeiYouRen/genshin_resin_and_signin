import json
import subprocess
from paddleocr import PaddleOCR
from datetime import datetime
import traceback
import re
import time
import os
import tkinter as tk
from onepush import notify
import logging
import logreset
import yaml

package_name = "com.mihoyo.hyperion"

miyoushe_bbs = {
    "原神": "酒馆",
    "综合": "ACG",
    "星穹铁道": "候车室",
    "绝区零": "咖啡馆",
    "崩坏3": "甲板",
    "未定事件簿": "律所",
    "崩坏学园2": "学园",
}


def notify_me(title, content, notifier, params):
    if not notifier or not params:
        logging.info("未设置推送")
        return
    return notify(notifier, title=title, content=content, **params)


# 获取分辨率
def get_resolution():
    adb_command = "adb shell wm size"
    result = subprocess.check_output(adb_command, shell=True)

    # 解析输出以获取分辨率
    output_str = result.decode("utf-8")
    lines = output_str.strip().split("\n")
    resolution = None

    for line in lines:
        if "Physical size:" in line:
            resolution = line.split(":")[1].strip()
    if resolution:
        logging.info(f"设备分辨率: {resolution}")
    else:
        raise "未能获取设备分辨率"
    res_list = [int(x) for x in resolution.split("x")]
    return res_list


# 获取 DPI
def get_density():
    adb_command = "adb shell wm density"
    result = subprocess.check_output(adb_command, shell=True)

    # 解析输出以获取分辨率
    output_str = result.decode("utf-8")
    lines = output_str.strip().split("\n")
    density = None

    for line in lines:
        if "Physical density:" in line:
            density = line.split(":")[1].strip()
    if density:
        logging.info(f"设备DPI: {density}")
    else:
        raise "未能获取设备DPI"
    return int(density)


# ABD 点击，例如 [0,0]
def adb_tap(x, y):
    command = f"adb shell input tap {x} {y}"
    subprocess.run(command, shell=True)


# 计算中心点
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


# ABD 点击中心。
# coordinates = [
#     [1099.0, 1227.0],
#     [1279.0, 1227.0],
#     [1279.0, 1293.0],
#     [1099.0, 1293.0],
# ]
def adb_tap_center(
    coordinates,
    sleep_seconds=3,
):
    x, y = calculate_center(coordinates)
    command = f"adb shell input tap {x} {y}"
    subprocess.run(command, shell=True)
    time.sleep(sleep_seconds)


def adb_back():
    command = "adb shell input keyevent KEYCODE_BACK"
    subprocess.run(command, shell=True)
    time.sleep(3)


# x1, y1, x2, y2
def adb_swipe(x1, y1, x2, y2):
    command = f"adb shell input swipe {x1} {y1} {x2} {y2}"
    subprocess.run(command, shell=True)
    time.sleep(3)


# 获取截图
def get_screenshot():
    os.system("adb shell screencap -p /sdcard/screen.png")
    # datetime_now = datetime.now()
    # formatted_now = datetime_now.strftime("%d_%H_%M_%S")
    # screenshot_path = f"./screenshots/screen_{formatted_now}.png"
    screenshot_path = f"./screenshots/screen.png"
    os.system(f"adb pull /sdcard/screen.png {screenshot_path}")

    # todo 直接读取到内存
    return screenshot_path


# 获取 tab 的高度
def get_tab_height():
    result = get_new_screenshot_OCR_result()
    tabs = miyoushe_bbs.keys()
    for i in result:
        text = i[1][0]
        if text in tabs:
            x, y = calculate_center(i[0])
            return y
    return 0


# 处理主界面可能出现的弹窗
def handle_pop_up():
    result = get_new_screenshot_OCR_result()

    for i in result:
        if "我知道了" in i[1][0]:
            adb_tap_center(i[0])
        if "下次再说" in i[1][0]:
            adb_tap_center(i[0])
        if "确定" in i[1][0]:
            adb_tap_center(i[0])
        if "米游社没有响应" in i[1][0]:
            relaunch_APP()
        if "回顶部" in i[1][0]:
            adb_tap_center(i[0])
        # if "发现" in i[1][0]:
        #     center = i[0][0]
        #     os.system("adb shell input tap {} {}".format(center[0], center[1]))
        #     time.sleep(3)


def turn2main_page():
    # 启动应用程序
    activity_name = ".main.HyperionMainActivity"
    subprocess.call(
        [
            "adb",
            "shell",
            "am",
            "start",
            "-n",
            f"{package_name}/{package_name + activity_name}",
        ]
    )
    time.sleep(8)
    # 确保在 首页
    # match_text_and_click("首页", 5)
    # 向右拖动tab，确保签到顺序
    x, y = get_resolution()
    height = get_tab_height()
    adb_swipe(0, height, x, height)
    time.sleep(3)


def relaunch_APP():
    logging.info("relaunch APP")
    subprocess.call(["adb", "shell", "am", "force-stop", f"{package_name}"])
    time.sleep(8)
    turn2main_page()
    time.sleep(3)


def get_OCR_result(screenshot_path):
    ocr = PaddleOCR(
        use_angle_cls=True, lang="ch", show_log=False
    )  # need to run only once to download and load model into memory
    result = ocr.ocr(screenshot_path, cls=False)
    result = result[0]

    return result


# 获取最新截图，并返回识别结果
def get_new_screenshot_OCR_result():
    screenshot_path = get_screenshot()
    result = get_OCR_result(screenshot_path)
    return result


# 从识别结果中匹配指定字符串，成功则返回坐标数组，失败返回 None
def match_text_by_result(result, text, strict=False):
    if strict:
        for i in result:
            if text == i[1][0]:
                return i[0]
        return None
    for i in result:
        if text in i[1][0]:
            return i[0]
    return None


# 获取最新截图，并匹配文本，返回文本的坐标
def match_text_by_OCR_result(text, strict=False):
    result = get_new_screenshot_OCR_result()
    match_result = match_text_by_result(result, text, strict)
    return match_result


# 获取最新截图，匹配文本及点击
def match_text_and_click(text, sleep_seconds=3, strict=False):
    match_result = match_text_by_OCR_result(text, strict)
    if match_result is None:
        return False
    adb_tap_center(match_result, sleep_seconds)
    return True


# 米游社的游戏福利签到，兼容 原神、崩坏：星穹铁道、崩坏3 等
# miyoushe
def sign_in_by_game_benefits(tab_name, clock_in_bbs=True):
    global miyoushe_bbs
    clock_in_bbs_result = False
    logging.info(f"正在签到 {tab_name}")

    handle_pop_up()
    # 切换 tab
    result = match_text_and_click(tab_name, 8)
    if not result:  # 未匹配到文本，跳过执行
        logging.info(f"未检测到 {tab_name} tab，已跳过")
        return False, False

    if clock_in_bbs:
        # 如果要米游社论坛签到，则先执行
        # 切换到对应的论坛tab
        bbs_tab_name = miyoushe_bbs[tab_name]
        result = match_text_and_click(bbs_tab_name, sleep_seconds=5, strict=True)
        if result:
            # 处理可能出现的弹窗
            handle_pop_up()
            # 判断是否已打卡
            result = match_text_by_OCR_result("已打卡")
            if not result:  # 如果未打卡，则打卡
                result = match_text_and_click("打卡")
                if result:
                    clock_in_bbs_result = True
                    logging.info(f"{tab_name} {bbs_tab_name} 打卡成功！")
            else:
                clock_in_bbs_result = True
                logging.info(f"{tab_name} {bbs_tab_name} 已打卡，跳过本次打卡")

    # 点击 签到福利页面
    result = match_text_and_click("签到福利", 8) or match_text_and_click(
        "每日签到", 8
    )  # 崩坏学园2 的是“每日签到”
    if not result:  # 未匹配到文本，跳过执行
        return False, clock_in_bbs_result

    result = get_new_screenshot_OCR_result()

    pattern = r"第\d+天"
    pattern_sign = r"(\d+)月已累计签到(\d+)天"
    now_day = datetime.now().day
    for i in result:
        text = i[1][0]
        match = re.search(pattern_sign, text)  # 判断已签到天数
        if match:
            signed_days = int(match.group(2))
            logging.info(f"{tab_name} 已签到天数 {signed_days}；当前日期 {now_day}")
            # 判断是否已签到
            if signed_days == now_day:
                logging.info(f"{tab_name} 已签到，跳过本次执行")
                adb_back()  # 返回到上一页
                return True, clock_in_bbs_result
        if "请选择角色" in text:
            logging.info(f"{tab_name} 未绑定任何角色，跳过本次签到")
            adb_back()  # 返回到上一页
            return False, clock_in_bbs_result
        if re.search(pattern, text):  # 遍历所有的 第x天
            coordinates = i[0]
            adb_tap_center(coordinates, 3)
            result = match_text_by_OCR_result("签到成功")
            if result:
                logging.info(f"{tab_name} 签到成功")
                adb_back()  # 返回到上一页
                return True, clock_in_bbs_result

    logging.info(f"{tab_name} 签到失败")
    adb_back()  # 返回到上一页
    return False, clock_in_bbs_result


def pop_up_windows(str):
    # 创建一个Tk对象
    root = tk.Tk()
    root.withdraw()
    # 获取屏幕的宽度和高度
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # 创建一个Toplevel窗口，并将它置顶
    top = tk.Toplevel(root)
    top.title("Title")
    top.lift()
    top.attributes("-topmost", True)

    # 计算Toplevel窗口的位置，使其居中显示
    top_width = 200
    top_height = 100
    x = (screen_width - top_width) // 2
    y = (screen_height - top_height) // 2
    top.geometry("{}x{}+{}+{}".format(top_width, top_height, x, y))

    # 在Toplevel窗口中显示一段字符串
    label = tk.Label(top, text=str)
    label.pack()

    # 设置Toplevel窗口关闭时，同时关闭root窗口
    def on_closing():
        root.destroy()

    top.protocol("WM_DELETE_WINDOW", on_closing)

    # 进入Tk事件循环，等待事件处理
    root.mainloop()


# 推送消息
def send_notify(title, text, config):
    logging.info(f"{title}\n{text}")
    for item in config:
        response = notify_me(title, text, item["notifier"], item["params"])
        logging.info(response.text)


if __name__ == "__main__":
    logreset.reset_logging()  # before you logging setting
    # 使用logging模块配置日志输出格式和级别
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", level="INFO"
    )
    # 读取YAML文件
    if os.path.exists("config.yml"):
        with open("config.yml", "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
    else:
        logging.error("未检测到 config.yml 配置文件，请配置后重试")
        exit(1)

    ADB_PORT = config.get("ADB_PORT", 16384)
    CLOCK_IN_BBS = config.get("CLOCK_IN_BBS", True)
    SIGNIN_GAMES = config.get("SIGNIN_GAMES", [])
    os.system(f"adb connect 127.0.0.1:{ADB_PORT}")
    os.system("adb devices")
    # 修改当前模拟器 分辨率，避免分辨率过高或过低。如果OCR效率较低，可以考虑降低分辨率 1080x1920
    os.system("adb shell wm size 1080x1920")
    # 修改当前模拟器 DPI，解决DPI过高时 tab 栏缩一块了
    os.system("adb shell wm density 360")
    # 创建截图文件夹
    folder_name = "screenshots"
    os.makedirs(folder_name, exist_ok=True)
    # 检查今天是否已经签到
    # 加载上次签到的日期
    try:
        with open("last_sign_in_day.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            last_sign_in_day = datetime.fromisoformat(data["last_sign_in_day"])
    except Exception:
        last_sign_in_day = None
    # 获取当前时间
    now = datetime.now()

    # 如果当前时间是今天，并且上次签到不是今天，则执行签到
    if (not last_sign_in_day) or (now.date() != last_sign_in_day.date()):
        try:
            # 启动应用程序
            turn2main_page()
            notify_message = ""
            for key in SIGNIN_GAMES:
                try:
                    result, clock_in_bbs_result = sign_in_by_game_benefits(
                        key, CLOCK_IN_BBS
                    )
                    if result:
                        notify_message = f"{notify_message}{key} 签到成功\n"
                    else:
                        notify_message = f"{notify_message}{key} 签到失败\n"

                    if clock_in_bbs_result:
                        notify_message = (
                            f"{notify_message}{key} - {miyoushe_bbs[key]} 打卡成功\n"
                        )
                    else:
                        notify_message = (
                            f"{notify_message}{key} - {miyoushe_bbs[key]} 打卡失败\n"
                        )

                except Exception as e:
                    logging.info(e)
            last_sign_in_day = datetime.now()
            notify_message = notify_message.strip()
            try:
                send_notify("米游社签到通知", notify_message, config.get("ONEPUSH_CONFIG", []))
            except:
                pop_up_windows(notify_message)
            # 保存签到日期到磁盘上
            with open("last_sign_in_day.json", "w", encoding="utf-8") as f:
                if last_sign_in_day:
                    json.dump({"last_sign_in_day": last_sign_in_day.isoformat()}, f)
        except Exception as e:
            traceback.logging.info_exc()
