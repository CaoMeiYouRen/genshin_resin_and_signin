import json
import pickle
import subprocess

from paddleocr import PaddleOCR
import datetime
import traceback
from copy import deepcopy
import re

import cv2
import time
import os

import numpy as np

import tkinter as tk

# 定义截图函数
from jmetal.algorithm.multiobjective import NSGAII
from jmetal.core.problem import FloatProblem
from jmetal.core.solution import FloatSolution
from jmetal.operator import PolynomialMutation, SBXCrossover
from jmetal.util.comparator import DominanceComparator
from jmetal.util.termination_criterion import StoppingByTime
from matplotlib import pyplot as plt
from tqdm import tqdm

std_confidence = 0.9
package_name = "com.mihoyo.hyperion"


def get_soc():
    """获取电量"""
    # 使用 ADB 命令获取电池电量
    adb_command = 'adb shell dumpsys battery | findstr "level"'
    battery_info = os.popen(adb_command).read()

    # 提取电量百分比
    battery_level = None
    for line in battery_info.splitlines():
        if "level" in line:
            parts = line.strip().split(":")
            if len(parts) == 2:
                battery_level = int(parts[1].strip())
                break

    if battery_level is not None:
        print("电池电量：{}%".format(battery_level))
    else:
        raise "无法获取电池电量信息"
    return battery_level


def get_resolution():
    # 运行ADB命令以获取屏幕分辨率
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
        print(f"设备分辨率: {resolution}")
    else:
        raise "未能获取设备分辨率"
    return resolution


# ABD 点击，例如 [0,0]
def adb_tap(x, y):
    command = f"adb shell input tap {x} {y}"
    subprocess.run(command, shell=True)


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
def adb_tap_center(coordinates):
    x, y = calculate_center(coordinates)
    command = f"adb shell input tap {x} {y}"
    subprocess.run(command, shell=True)


def adb_back():
    command = "adb shell input keyevent KEYCODE_BACK"
    subprocess.run(command, shell=True)


class ImageResizer:
    def __init__(self, scale0, scale1, direction):
        self.scale0 = scale0
        self.scale1 = scale1
        self.direction = direction

    def resize(self, *args):
        scale0 = self.scale0
        scale1 = self.scale1
        if self.direction == 0:
            shape = args[0].shape
            resized_img = cv2.resize(
                args[0], (int(shape[1] * scale1), int(shape[0] * scale0))
            )
            return resized_img, args[1]
        elif self.direction == 1:
            shape = args[1].shape
            resized_img = cv2.resize(
                args[1], (int(shape[1] * scale1), int(shape[0] * scale0))
            )
            return args[0], resized_img

    def restore_coordinates(self, coord):
        if self.direction == 1:
            return [coord[0] / self.scale1, coord[1] / self.scale0]
        else:
            return coord


class ResolutionScaleProblem(FloatProblem):
    """Class representing problem Srinivas."""

    def __init__(self, template, screenshot, direction):
        """
        :param direction:
            0: 缩小template
            1：缩小screenshot
        """
        super().__init__()
        self.number_of_variables = 2
        self.number_of_objectives = 1
        self.number_of_constraints = 0

        self.obj_directions = [self.MINIMIZE]
        self.obj_labels = ["similarity"]

        self.lower_bound = [0.1, 0.1]
        self.upper_bound = [1, 1]

        self.template = template
        self.screenshot = screenshot
        self.direction = direction

    def evaluate(self, solution: FloatSolution) -> FloatSolution:
        template = self.template
        screenshot = self.screenshot

        scale0 = solution.variables[0]
        scale1 = solution.variables[1]

        template_ = deepcopy(template)
        screenshot_ = deepcopy(screenshot)
        image_resizer = ImageResizer(scale0, scale1, self.direction)
        resized_tuple = image_resizer.resize(template_, screenshot_)
        # 模板匹配
        try:
            result = cv2.matchTemplate(
                resized_tuple[0], resized_tuple[1], cv2.TM_CCOEFF_NORMED
            )
            # 找到匹配位置
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            solution.objectives[0] = -max_val
        except:
            solution.objectives[0] = 0

        return solution

    def get_name(self):
        return "solve_resolution_scale"


def solve_resolution_scale(template, screenshot, direction, max_seconds):
    problem = ResolutionScaleProblem(template, screenshot, direction)
    algorithm = NSGAII(
        problem=problem,
        population_size=20,
        offspring_population_size=20,
        mutation=PolynomialMutation(
            probability=1.0 / problem.number_of_variables, distribution_index=20.0
        ),
        crossover=SBXCrossover(probability=0.9, distribution_index=20.0),
        termination_criterion=StoppingByTime(max_seconds=max_seconds),
        dominance_comparator=DominanceComparator(),
    )

    print(f"正在适配分辨率，持续{max_seconds}s")

    algorithm.start_computing_time = time.time()
    algorithm.solutions = algorithm.create_initial_solutions()
    algorithm.solutions = algorithm.evaluate(algorithm.solutions)
    algorithm.init_progress()

    with tqdm(total=max_seconds, desc="Time Progress") as pbar:
        start_time = time.time()
        while not algorithm.stopping_condition_is_met():
            elapsed_time = time.time() - start_time
            pbar.update(int(elapsed_time - pbar.n))  # 更新进度条
            algorithm.step()
            front = algorithm.get_result()
            best_objective_val = np.inf
            best_solution = front[0]
            for solution in front:
                if solution.objectives[0] < best_objective_val:
                    best_solution = solution
                    best_objective_val = -solution.objectives[0]
            algorithm.update_progress()
            pbar.set_description(f"best confidence {best_objective_val:.2f}")
            if best_objective_val > 0.95:
                break

    algorithm.total_computing_time = time.time() - algorithm.start_computing_time
    print("Algorithm (continuous problem): " + algorithm.get_name())
    print("Problem: " + problem.get_name())
    print("Computing time: " + str(algorithm.total_computing_time))
    # print("optimization result: cycle=", cycle, "best_objective_val=", best_objective_val)

    return (
        ImageResizer(best_solution.variables[0], best_solution.variables[1], direction),
        best_objective_val,
    )


def get_screenshot():
    os.system("adb shell screencap -p /sdcard/screen.png")
    # datetime_now = datetime.datetime.now()
    # formatted_now = datetime_now.strftime("%d_%H_%M_%S")
    # screenshot_path = f"./screenshots/screen_{formatted_now}.png"
    screenshot_path = f"./screenshots/screen.png"
    os.system(f"adb pull /sdcard/screen.png {screenshot_path}")

    # todo 直接读取到内存
    return screenshot_path


# 定义模板匹配函数
def match_and_click(template_path, save_coordinates=True):
    global std_confidence
    # 加载模板
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    # 截图
    screenshot_path = get_screenshot()
    # 加载截图
    screenshot = cv2.imread(screenshot_path)
    # 转为灰度图像
    gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    resolution = get_resolution()

    def calibration():
        # 尺度校准
        for desctiption, direction in {"缩小截图": 1, "缩小模板": 0}.items():
            # if direction ==0:continue
            print("尝试", desctiption)
            image_resizer, confidence = solve_resolution_scale(
                template, gray, direction, 10  # 60
            )
            std_confidence = confidence - 0.05  # 增加0.05的容错率
            std_resolution = get_resolution()
            if confidence > 0.95:
                break
        if confidence < 0.95:
            raise "分辨率适配失败，重试有概率解决问题"
        if not os.path.exists("scale_info.pkl"):
            with open("scale_info.pkl", "wb") as f:
                scale_dict = {
                    "default": [std_resolution, image_resizer, std_confidence]
                }
                pickle.dump(scale_dict, f)
        else:
            with open("scale_info.pkl", "rb") as f:
                scale_dict = pickle.load(f)
            for desctiption, direction in {"缩小截图": 1, "缩小模板": 0}.items():
                print("尝试", desctiption)
                image_resizer, confidence = solve_resolution_scale(
                    template, gray, direction, 10  # 60
                )
                std_confidence = confidence - 0.05  # 增加0.05的容错率
                std_resolution = get_resolution()
                if confidence > 0.95:
                    break
            if confidence < 0.95:
                raise "分辨率适配失败，重试有概率解决问题"
            print(f"为模板{template_path}添加专用分辨率参数")
            scale_dict[template_path] = [std_resolution, image_resizer, std_confidence]
            with open("scale_info.pkl", "wb") as f:
                pickle.dump(scale_dict, f)
        return image_resizer, std_confidence

    """第一次机会"""
    if os.path.exists("scale_info.pkl"):
        with open("scale_info.pkl", "rb") as f:
            scale_dict = pickle.load(f)
            if template_path in scale_dict.keys():
                [std_resolution, image_resizer, std_confidence] = scale_dict[
                    template_path
                ]
            else:
                [std_resolution, image_resizer, std_confidence] = scale_dict["default"]
        if std_resolution != resolution:
            image_resizer, std_confidence = calibration()
    else:
        image_resizer, std_confidence = calibration()
    resized_tuple = image_resizer.resize(template, gray)
    # 模板匹配
    result = cv2.matchTemplate(resized_tuple[0], resized_tuple[1], cv2.TM_CCOEFF_NORMED)
    # 找到匹配位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    confidence = max_val
    print("CONFIDENCE1", confidence)
    top_left = list(max_loc)

    # debug 创建一个图形窗口并显示截图
    # fig, ax = plt.subplots()
    # ax.imshow(screenshot)
    # ax.plot(max_loc[0], max_loc[1], 'ro')
    # plt.savefig("test.jpg")
    # plt.show()
    # plt.close()

    """第二次机会"""
    if max_val < std_confidence:
        print("默认参数失效，尝试更新参数")
        calibration()
        if os.path.exists("scale_info.pkl"):
            with open("scale_info.pkl", "rb") as f:
                scale_dict = pickle.load(f)
                if template_path in scale_dict.keys():
                    [std_resolution, image_resizer, std_confidence] = scale_dict[
                        template_path
                    ]
                else:
                    [std_resolution, image_resizer, std_confidence] = scale_dict[
                        "default"
                    ]
            if std_resolution != resolution:
                image_resizer, std_confidence = calibration()
        else:
            image_resizer, std_confidence = calibration()
        resized_tuple = image_resizer.resize(template, gray)
        # 模板匹配
        result = cv2.matchTemplate(
            resized_tuple[0], resized_tuple[1], cv2.TM_CCOEFF_NORMED
        )
        # 找到匹配位置
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        confidence = max_val
        print("CONFIDENCE2", confidence)
        top_left = list(max_loc)
        if max_val < std_confidence:
            raise "匹配失败，未知错误"

    # debug
    # fig, ax = plt.subplots()
    # ax.imshow(gray)
    # ax.scatter(top_left[0], top_left[1], s=100, c='red', marker='o')
    # fig.savefig("test.jpg")
    # plt.show()
    # plt.close()
    h, w = template.shape
    bottom_right = (top_left[0] + w, top_left[1] + h)
    center = [(top_left[0] + bottom_right[0]) / 2, (top_left[1] + bottom_right[1]) / 2]
    center = image_resizer.restore_coordinates(center)

    if confidence > std_confidence:
        # debug 创建一个图形窗口并显示截图
        if save_coordinates:
            fig, ax = plt.subplots()
            ax.imshow(screenshot)
            ax.plot(center[0], center[1], "ro")
            plt.savefig("test.jpg")
            # plt.show()
            plt.close()

        # 点击模板中心位置
        os.system("adb shell input tap {} {}".format(center[0], center[1]))
        time.sleep(2)
        return True
    else:
        print("NOT FOUND")
        return False


# 处理主界面可能出现的弹窗
def handle_pop_up():
    result = get_new_screenshot_OCR_result()

    for i in result:
        if "我知道了" in i[1][0]:
            # try:
            #     print("try skipping update")
            #     match_and_click("./templates/skip_update.png")
            # except Exception as e:
            #     warnings.warn("意料之外的识别错误: {}".format(str(e)))
            adb_tap_center(i[0])
            time.sleep(3)
        # if "青少年模式" in i[1][0]:
        #     # try:
        #     #     print("try confirming teenager mode")
        #     #     match_and_click("./templates/i_get_it.png")
        #     # except Exception as e:
        #     #     warnings.warn("意料之外的识别错误: {}".format(str(e)))
        #     adb_tap_center(i[0])
        #     time.sleep(3)
        if "下次再说" in i[1][0]:
            # try:
            #     print("try skipping update")
            #     match_and_click("./templates/skip_update.png")
            # except Exception as e:
            #     warnings.warn("意料之外的识别错误: {}".format(str(e)))
            adb_tap_center(i[0])
            time.sleep(3)
        if "米游社没有响应" in i[1][0]:
            relaunch_APP()
        if "回顶部" in i[1][0]:
            center = i[0][0]
            os.system("adb shell input tap {} {}".format(center[0], center[1]))
            time.sleep(3)
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


def turn2resin_page():
    turn2main_page()
    match_and_click("./templates/myself.png")

    result = get_new_screenshot_OCR_result()

    for i in result:
        if "成就达成数" in i[1][0]:
            center = i[0][0]
            os.system("adb shell input tap {} {}".format(center[0], center[1]))
            break
    time.sleep(20)


def relaunch_APP():
    print("relaunch APP")
    subprocess.call(["adb", "shell", "am", "force-stop", f"{package_name}"])
    time.sleep(8)
    turn2main_page()
    time.sleep(3)


def get_OCR_result(screenshot_path):
    ocr = PaddleOCR(
        use_angle_cls=True, lang="ch"
    )  # need to run only once to download and load model into memory
    result = ocr.ocr(screenshot_path, cls=False)
    result = result[0]

    # debug   显示结果
    # image = Image.open(img_path).convert('RGB')
    # boxes = [line[0] for line in result]
    # txts = [line[1][0] for line in result]
    # scores = [line[1][1] for line in result]
    # im_show = draw_ocr(image, boxes, txts, scores, font_path='./fonts/simfang.ttf')
    # im_show = Image.fromarray(im_show)
    # im_show.save('result.jpg')

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
    adb_tap_center(match_result)
    time.sleep(sleep_seconds)
    return True


def monitor_resin():
    """从截图上识别体力值"""
    # 截图

    result = get_new_screenshot_OCR_result()

    result = str(result)
    result = result.replace(" ", "")

    """联网百度文本识别"""
    # result = subprocess.check_output("paddleocr --image_dir screen.png", shell=True)
    # result = result.decode('utf-8')

    for pattern in [r"(\d+)/160", r"(\d+)／160"]:
        match = re.search(pattern, result)
        if match:
            # 获取匹配到的值
            text = match.group(1)
            print(f"The value is: {text}")
            break
        else:
            print("Pattern not found in the string.")

    print("识别结果为:", text)
    current_resin = int(text)
    time_till_full = (160 - current_resin) * 8
    t = datetime.datetime.now()
    delta = datetime.timedelta(minutes=time_till_full)

    t_full = t + delta
    print(current_resin, ", ", t_full, "完全恢复")
    print()

    return current_resin


def sign_in():
    print("正在签到")

    match_and_click("./templates/sign_in.png")
    time.sleep(8)

    result = get_new_screenshot_OCR_result()
    # 判断是否已签到
    for i in result:
        if "漏签0天" in i[1][0]:
            return True

    match_and_click("./templates/draw.png")
    time.sleep(5)

    result = get_new_screenshot_OCR_result()

    for i in result:
        if "签到成功" in i[1][0]:
            return True

    return False


def sign_in_by_genshin():
    tab_name = "原神"
    print(f"正在签到 {tab_name}")
    # 切换到原神 tab
    result = match_text_and_click(tab_name)

    if not result:  # 未匹配到文本，跳过执行
        return

    # 点击 签到福利页面
    result = match_text_and_click("签到福利")
    if not result:  # 未匹配到文本，跳过执行
        return

    # 判断是否已签到
    # TODO 优化是否已签到的逻辑判断
    result = match_text_and_click("漏签0天")
    if result:  # 已签到，跳过执行
        return

    match_and_click("./templates/draw.png")
    time.sleep(5)

    result = get_new_screenshot_OCR_result()

    for i in result:
        if "签到成功" in i[1][0]:
            return True

    return False


# miyoushe_bbs = {"原神": "酒馆", "崩坏：星穹铁道": "候车室", "崩坏3": "甲板", "绝区零": "咖啡馆", "综合": "ACG"}
miyoushe_bbs = {
    "原神": "酒馆",
    "综合": "ACG",
    "崩坏：星穹铁道": "候车室",
    "绝区零": "咖啡馆",
    "崩坏3": "甲板",
    "未定事件簿": "律所",
    "崩坏学园2": "学园",
}


# 米游社的游戏福利签到，兼容 原神、崩坏：星穹铁道、崩坏3
# miyoushe
def sign_in_by_game_benefits(tab_name, sign_in_bbs=True):
    global miyoushe_bbs
    print(f"正在签到 {tab_name}")
    handle_pop_up()
    # 切换 tab
    # result = match_text_by_OCR_result(tab_name)
    # print("result", result)
    # result = get_new_screenshot_OCR_result()
    # for i in result:
    #     if tab_name in i[1][0]:
    #         print(i)

    result = match_text_and_click(tab_name)

    if not result:  # 未匹配到文本，跳过执行
        return False

    if sign_in_bbs:
        # 如果要米游社论坛签到，则先执行
        # 切换到对应的论坛tab
        bbs_tab_name = miyoushe_bbs[tab_name]
        result = match_text_and_click(bbs_tab_name, strict=True)
        if result:
            # 判断是否已打卡
            result = match_text_by_OCR_result("已打卡")
            if not result:  # 如果未打卡，则打卡
                result = match_text_and_click("打卡")
                if result:
                    print(f"{tab_name} {bbs_tab_name} 打卡成功！")
            else:
                print(f"{tab_name} {bbs_tab_name} 已打卡，跳过本次打卡")

    # 点击 签到福利页面
    result = match_text_and_click("签到福利")
    if not result:  # 未匹配到文本，跳过执行
        return False

    result = get_new_screenshot_OCR_result()

    pattern = r"第\d+天"
    pattern_sign = r"(\d+)月已累计签到(\d+)天"
    now_day = datetime.now().day
    for i in result:
        text = i[1][0]
        match = re.search(pattern_sign, text)  # 判断已签到天数
        if match:
            signed_days = match.group(2)
            # 判断是否已签到
            if signed_days == now_day:
                print(f"{tab_name} 已签到，跳过本次执行")
                adb_back()  # 返回到上一页
                return True
        if "请选择角色" in text:
            coordinates = i[0]
            adb_tap_center(coordinates)
            time.sleep(3)
            print(f"{tab_name} 未绑定任何角色，跳过本次签到")
            adb_back()  # 返回到上一页
            return False
        if re.search(pattern, text):  # 遍历所有的 第x天
            coordinates = i[0]
            adb_tap_center(coordinates)
            time.sleep(1)
    result = get_new_screenshot_OCR_result()
    for i in result:
        if "签到成功" in i[1][0]:
            adb_back()  # 返回到上一页
            return True
    adb_back()  # 返回到上一页
    return False


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


def send_wechat(text):
    print(text)
    # params = {"title": text}
    # response = requests.post(url, data=params, proxies=None, timeout=10)
    # print(response.text)


def balance_SOC_or_sleep(seconds):
    soc = get_soc()
    if soc > 90:
        # 增加CPU负载
        print(f"stree cpu {seconds}s")
        t0 = time.time()
        turn2main_page()
        while time.time() - t0 < seconds:
            os.system("adb shell input swipe 500 1800 500 1000")
            time.sleep(0.2)
        time.sleep(3)

        turn2main_page()

    else:
        print(f"sleep {seconds}s")
        time.sleep(seconds)


# while True:
if __name__ == "__main__":
    fault_num = 0
    reset_threshold = 4 * 60
    time_tolerance = 5 * 60 * 60
    # os.system("adb disconnect 127.0.0.1:16384")
    # TODO 优化adb链接
    os.system("adb connect 127.0.0.1:16384")
    os.system("adb devices")
    # 调用adb shell命令将亮度设置为0
    # subprocess.run(["adb", "shell", "settings", "put", "system", "screen_brightness", "0"])
    # 检查今天是否已经签到
    # 加载上次签到的日期
    # try:
    #     with open("last_sign_in_day.pkl", "rb") as f:
    #         last_sign_in_day = pickle.load(f)
    # except FileNotFoundError:
    # last_sign_in_day = None
    last_sign_in_day = None
    # 获取当前时间
    now = datetime.datetime.now()
    #  + datetime.timedelta(
    #     hours=-3
    # )
    # 米游社在零点会跳出一个弹窗 三点钟再签到避免这种情况
    # 如果当前时间是今天，并且上次签到不是今天，则执行签到
    if now.day != last_sign_in_day:
        try:
            # 启动应用程序
            turn2main_page()
            for key, value in miyoushe_bbs.items():
                # print(key, value)
                result = sign_in_by_game_benefits(key, True)
                if result:
                    last_sign_in_day = now.day
                try:
                    send_wechat(f"{key} 签到成功")
                except:
                    pop_up_windows(f"{key} 签到成功")
            # 保存签到日期到磁盘上
            with open("last_sign_in_day.pkl", "wb") as f:
                pickle.dump(last_sign_in_day, f)
            with open("last_sign_in_day.json", "wb") as f:
                json.dump({"last_sign_in_day": last_sign_in_day}, f)
        except Exception as e:
            traceback.print_exc()

    # start_time = time.time()
    # while time.time() - start_time <= reset_threshold:
    #     try:
    #         turn2resin_page()
    #         current_resin = monitor_resin()
    #         if current_resin >= 159:
    #             try:
    #                 send_wechat(f"current_resin:{current_resin}; soc:{get_soc()}")
    #             except:
    #                 pop_up_windows("请求错误")
    #             # 进入死循环，每10分钟查看一次，直到体力被消耗
    #             while monitor_resin() >= current_resin:
    #                 balance_SOC_or_sleep(reset_threshold)
    #                 turn2resin_page()

    #         fault_num = 0
    #     except Exception as e:
    #         traceback.print_exc()
    #         fault_num += 1
    #         relaunch_APP()

    #     balance_SOC_or_sleep(reset_threshold)

    # if fault_num * reset_threshold > time_tolerance:
    #     try:
    #         send_wechat("出现异常界面")
    #     except:
    #         pop_up_windows("出现异常界面")
    #     fault_num = 0
