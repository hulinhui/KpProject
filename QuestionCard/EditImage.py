import random
import numpy as np
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


def get_point_data(data_list, number=None):
    """
    获取指定选项的定位点
    :param data_list: 选项或准考证号列表 ，例如：【（）,（），（），（）】
    :param number: 获取第n个选项
    :return: 返回指定选项的定位点信息
    """
    if number is not None:
        if number >= len(data_list):
            raise '输入有误'
        pos_data = data_list[number]
    else:
        pos_data = random.choice(data_list)
    return pos_data


def paste_barcode_to_image(background_image, foreground_image, position):
    """
    将一张图片缩放到指定大小，然后放置到另一张图片的指定位置上并保存合成后的新图。

    :param background_image: 背景图片的对象
    :param foreground_image: 要放置的图片（前景）的对象
    :param position: 前景图片放置的位置及前景图的尺寸，格式为 (x, y,w,h)
    """
    # 获取定位及尺寸
    pos, size = position[:2], position[2:]
    # 调整前景图片的尺寸
    resized_foreground = cv2.resize(foreground_image, size)
    # 粘贴前景图片到背景图片上
    background_image[pos[1]:pos[1] + size[1], pos[0]:pos[0] + size[0]] = resized_foreground


def find_rectangles_in_region(image, point_tuple, option_height=25, option_range=2, option_count=4,
                              stu_barcode=None, direction=None):
    """
    指定图片的某个区域中寻找所有矩形，并打印它们的坐标。
    过滤掉无用的矩形区域，并将有用的矩形定位进行横向或纵向排序
    按照题的选项个数进行拆分得到列表
    遍历选项定位列表进行，随机或按照准考证号进行填涂，黑色填充
    参数:
    :param image: 图片的对象。
    :param point_tuple: 一个元组，指定区域中心的 (x,y,w,h) 坐标；x区域横坐标，y区域纵坐标，w区域长度，h区域高度。
    :param option_height: 选项区域选项的高度。 默认25
    :param option_range:选项宽高误差尺寸，默认3个
    :param option_count:选项个数。默认4个
    :param stu_barcode: 学生准考证号
    :param direction: 横向还是竖向排序【准考证号竖向，选择题横向】
    """
    # 定位
    # 获取局域坐标信息
    left, top, width, hight = point_tuple
    # 获取选项高度误差范围
    o_height_range = list(range(option_height - option_range, option_height + option_range))
    # print(o_height_range)
    # 裁剪区域
    region = image[top:top + hight, left:left + width]
    # 转换为灰度图
    gray_region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    # 使用阈值进行二值化
    _, thresh = cv2.threshold(gray_region, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # 寻找并打印所有矩形坐标
    rectangles = [cv2.boundingRect(contour) for contour in contours if len(contour) >= 4]

    # 获取选项高度误差范围最大的矩形高度
    max_height = max([rect[3] for rect in rectangles if rect[3] in o_height_range])
    # 按照横向还是纵向进行排序
    sorted_rectangles = coordinate_sorted(rectangles, direction=direction)
    # 过滤无效的定位点,获取满足条件的矩形[由于矩形边框线存在1px的误差，导致一个选项存在2个区域，故选取最大矩形填充]
    coordinate_data = [(left + rect[0], top + rect[1], left + rect[0] + rect[2], top + + rect[1] + rect[3]) for rect in
                       sorted_rectangles if rect[3] == max_height]
    # print(len(coordinate_data))
    # for rect in sorted_rectangles:
    #     x_rect, y_rect, w_rect, h_rect = rect
    #     print(x_rect, y_rect, w_rect, h_rect)
    #     if h_rect == max_height:
    #         print(x_rect, y_rect, w_rect, h_rect)
    # 按照题的选项个数进行拆分，得到每道题的所有选项坐标为一个列表，列表套列表
    coord_split_data = [coordinate_data[_:_ + option_count] for _ in range(0, len(coordinate_data), option_count)]
    # print(f'一共找到{len(coord_split_data)}个填充项')
    # 获取学生准考账号列表数据
    barcode_list = [int(_) for _ in stu_barcode] if stu_barcode else [None] * len(coord_split_data)  # 列表的个数就是题或证号的个数

    # 答题或填涂准考证
    # 循环每道题，进行填充答案
    for coord_list, number in zip(coord_split_data, barcode_list):
        # 随机答题
        random_coordinate = get_point_data(coord_list, number=number)
        # # 每一道题的左上坐标及右下坐标
        start_x, start_y, end_x, end_y = random_coordinate
        # -1 全部填充  (0,0,0) 颜色
        cv2.rectangle(image, (start_x, start_y), (end_x, end_y), (0, 0, 0), -1)


def get_random_score_list(question):
    # 随机浮点数分数，分数范围（0，score）之间，可以存在小数（0.5的倍数）
    random_score = random.randint(0, question.get('score', 1) * 2) / 2.0
    print(f"第{question['th']}题随机获取的分数为：{random_score}")
    # 获取整数位和小数位
    integer_part, decimal_part = divmod(random_score, 1)
    # 判断积分列规则，进行不同方式获取积分列表
    if question['scoreType'] == 1:
        # 第一种：11.5==>[11.0,0.5]
        score_list = [integer_part] + ([decimal_part] if decimal_part else [])
    else:
        # 第二种：11.5==>[10.0,1.0,0.5]
        integer_part_list = [(integer_part // 10) * 10, integer_part % 10] if integer_part > 10 else [integer_part]
        score_list = integer_part_list if decimal_part == 0 else integer_part_list + [decimal_part]
    # 根据积分列表获取到题卡对应积分定位点列表
    pos_list = [pos_item for score in score_list for pos_item in question.get('vals') if pos_item['val'] == score]
    return pos_list


def execute_score(image, pos_list):
    # 循环定位点列表
    for pos_item in pos_list:
        # 获取定位坐标(x,y,w,h)
        hight, _, width, left, top = pos_item.values()
        # 计算矩形中间的x坐标
        center_x = (left + width + left) // 2
        # 定义线的划线起点和终点纵坐标
        line_start = (center_x, top - 50)
        line_end = (center_x, top + hight + 100)
        # 画线，颜色为红色，线条粗细为3
        cv2.line(image, line_start, line_end, (0, 0, 255), 3)


def short_answer_scoring(d_file, item):
    # 获取第一页的信息还是第二页的信息
    paper_key = 'paper_2' if isinstance(d_file, str) else 'paper_1'
    # 获取页面满足条件的题组
    question_list = item.get(paper_key) if item else []
    # 页面没有解答题，直接退出手阅
    if not question_list:
        print('当前页获取不到手阅的题组！')
        return
    # 加载图像，看参数传的图像还是字符串，字符串就加载图像
    image = cv2.imdecode(np.fromfile(d_file, dtype=np.uint8), -1) if isinstance(d_file, str) else d_file
    # 循环题组信息
    for question in question_list:
        # 根据积分列规则返回对应的题组定位信息
        pos_list = get_random_score_list(question)
        # 执行评分操作
        execute_score(image, pos_list)
    # 判断传入的是图像对象还是字符串对象，图像对象直接退出，外面有保存，字符串对象直接保存
    if not isinstance(d_file, str):
        return
    # 保存图片信息
    cv2.imencode('.jpg', image)[1].tofile(d_file)


def create_image_data(b_file, c_file, stu_barcode, zk_position, xz_position, form, card_item=None):
    # 加载题卡图片-背景图
    c_image = cv2.imdecode(np.fromfile(c_file, dtype=np.uint8), -1)
    # 判断进行条形码粘贴还是准考证填涂
    if form:
        # 加载条形码图片-前景图
        b_image = cv2.imdecode(np.fromfile(b_file, dtype=np.uint8), -1)
        # 准考证号条形码粘贴操作
        paste_barcode_to_image(c_image, b_image, position=eval(zk_position))
        # 释放图像占用的内存
        del b_image
    else:
        # 准考证号填涂操作
        find_rectangles_in_region(c_image, eval(zk_position), option_count=10, stu_barcode=stu_barcode, direction=True)
    # 选择题填涂操作
    find_rectangles_in_region(c_image, eval(xz_position))
    # 获取到手阅题卡信息，进行手阅打分操作
    short_answer_scoring(c_image, card_item)
    # 保存最终填充的背景图片
    cv2.imencode('.jpg', c_image)[1].tofile(c_file)


if __name__ == '__main__':
    # 示例代码使用
    b_path = r'D:\PyCharm 2024.1.4\KpProject\QuestionCard\barcode\42000002.png'  # 背景图片的路径
    f_path = r'D:\PyCharm 2024.1.4\KpProject\QuestionCard\cardinfo\手阅测试题卡\01.jpg'  # 前景图片的路径
    s_barcode = '42000002'
    zk_pos = '(1018, 412, 519, 391)'  # 前景图片放置的位置（x, y,w,h）
    xz_pos = '(121, 912, 1415, 228)'
    create_image_data(b_path, f_path, s_barcode, zk_pos, xz_pos, form=0)
