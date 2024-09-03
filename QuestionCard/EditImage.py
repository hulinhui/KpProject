import random
import numpy as np
from PIL import Image
import cv2


def coordinate_sorted(data_list, direction=None):
    """
       将定位的坐标列表进行排序，横向和纵向。
       :param data_list: 坐标列表，列表套元祖
       :param direction: 按照横向还是纵向排序，默认横向
       :return data_list 返回排序后的列表数据
       """
    if direction is None:
        return sorted(data_list, key=lambda x: (x[1], x[0]))
    else:
        return sorted(data_list, key=lambda x: (x[0], x[1]))


def resize_and_paste_image(background_path, foreground_path, position, size):
    """
    将一张图片缩放到指定大小，然后放置到另一张图片的指定位置上并保存合成后的新图。

    :param background_path: 背景图片的路径
    :param foreground_path: 要放置的图片（前景）的路径
    :param position: 前景图片放置的位置，格式为 (x, y)
    :param size: 前景图片缩放的目标大小，格式为 (width, height)
    """
    # 打开背景和前景图片
    background = Image.open(background_path)
    foreground = Image.open(foreground_path)

    # 缩放前景图片到指定大小
    resized_foreground = foreground.resize(size, Image.LANCZOS)

    # 如果前景图片没有透明度通道，则创建一个白色背景的透明度掩码
    if resized_foreground.mode != 'RGBA':
        alpha_channel = Image.new('L', resized_foreground.size, 255)  # 创建白色背景的掩码
        resized_foreground.putalpha(alpha_channel)

    # 将缩放后的前景图片放置到背景图片上
    background.paste(resized_foreground, position, resized_foreground)

    # 保存合成后的新图片
    background.save(background_path)


def find_rectangles_in_region(image_path, point_tuple, option_size=(68, 38), option_range=2, option_count=4):
    """
    指定图片的某个区域中寻找所有矩形，并打印它们的坐标。

    参数:
    :param image_path: 图片的路径。
    :param point_tuple: 一个元组，指定区域中心的 (x,y,w,h) 坐标；x区域横坐标，y区域纵坐标，w区域长度，h区域高度。
    :param option_size: 选项区域的尺寸,w为选项的长度，h为选项的高度。 默认(68, 38)
    :param option_range:选项宽高误差尺寸，默认2个
    :param option_count:选项个数。默认4个
    """
    # 定位
    # 加载图片
    image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), -1)
    # 获取局域坐标信息
    left, top, width, hight = point_tuple
    # 获取选项尺寸误差范围
    o_width_range, o_height_range = [range(option_size[0] - option_range, option_size[0] + option_range),
                                     range(option_size[1] - option_range, option_size[1] + option_range)]
    # 裁剪区域
    region = image[top:top + hight, left:left + width]
    # 转换为灰度图
    gray_region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    # 使用阈值进行二值化
    _, thresh = cv2.threshold(gray_region, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # 寻找并打印所有矩形坐标
    rectangles = [cv2.boundingRect(contour) for contour in contours if len(contour) >= 4]
    # 按照横向还是纵向进行排序
    sorted_rectangles = coordinate_sorted(rectangles)
    # 过滤无效的定位点,获取满足条件的[(start_x, start_y, end_x, end_y)]  x_rect, y_rect, w_rect, h_rect = rect
    coordinate_data = [(left + rect[0], top + rect[1], left + rect[0] + rect[2], top + + rect[1] + rect[3]) for rect in
                       sorted_rectangles if
                       rect[0] != 0 and rect[2] in o_width_range and rect[3] in o_height_range]
    # 按照题的选项个数进行拆分，得到每道题的所有选项坐标为一个列表，列表套列表
    coord_split_data = [coordinate_data[_:_ + option_count] for _ in range(0, len(coordinate_data), option_count)]

    # 答题
    # 循环每道题，进行填充答案
    for coord_list in coord_split_data:
        # 随机答题
        random_coordinate = random.choice(coord_list)
        # 每一道题的左上坐标及右下坐标
        start_x, start_y, end_x, end_y = random_coordinate
        # -1 全部填充  (0,0,0) 颜色
        cv2.rectangle(image, (start_x, start_y), (end_x, end_y), (0, 0, 0), -1)
    # 保存图片
    cv2.imencode('.jpg', image)[1].tofile(image_path)


if __name__ == '__main__':
    # 示例代码使用
    # b_path = r'./cardinfo/高中历史20240820170434/19.jpg'  # 背景图片的路径
    # f_path = './barcode/学生10.png'  # 前景图片的路径
    # f_pos = (1510, 510)  # 前景图片放置的位置（x, y）
    # f_size = (780, 370)  # 前景图片缩放的目标大小
    # resize_and_paste_image(b_path, f_path, f_pos, f_size)
    find_rectangles_in_region(r'D:\PyCharm 2024.1.4\KpProject\QuestionCard\cardinfo\语文手阅0830\03.jpg',
                              (178, 1100, 2123, 318), (68, 38))
