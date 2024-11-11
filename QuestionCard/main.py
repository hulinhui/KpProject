from QuestionCard.KpRequest.KpStudent import KpStudent
from QuestionCard.KpRequest.KpCard import KpCard
from QuestionCard.GenerateBarcode import generate_barcode
from QuestionCard.PdfConvertImage import (generate_card_pic, get_file_list,
                                          get_file_path, move_file_to_directory, clear_directory)
from QuestionCard.EditImage import create_image_data, short_answer_scoring

# 实例化一个题卡类
card_class = KpCard()
# 获取题卡类的kp数据
kp_info, logger = card_class.object.kp_data, card_class.object.logger


def get_point_info():
    """
    (1,1):    校内考+条形码：    条形码定位+条形码选择题定位+准考证形式
    (1,0):    校内考+准考证填涂：  准考证定位+准考证选择题定位+准考证形式
    (0,1):    联考+条形码：       联考条形码定位+联考条形码选择题定位+准考证形式
    (0,0):    联考+准考证填涂：   联考准考证定位+联考准考证选择题定位+准考证形式
    :return: 根据exam_flag和number_from交互场景，返回对应场景的定位点元祖信息
    """
    point_item = {
        (1, 1): (kp_info['ie_pos'], kp_info['ie_xz_tpos'], int(kp_info['number_from'])),
        (1, 0): (kp_info['ie_zh_pos'], kp_info['ie_xz_zpos'], int(kp_info['number_from'])),
        (0, 1): (kp_info['je_pos'], kp_info['je_xz_tpos'], int(kp_info['number_from'])),
        (0, 0): (kp_info['je_zh_pos'], kp_info['je_xz_zpos'], int(kp_info['number_from']))
    }
    return point_item.get((int(kp_info['exam_flag']), int(kp_info['number_from'])), "无效的输入")


def get_student_count(folder_path, clear_flag=False):
    """
    根据barcode文件夹中的学生条形码图片个数获取学生人数，即图片人数=学生人数
    文件夹中无图片或者需要更新时，获取系统学生信息
    :param folder_path: 文件夹路径
    :param clear_flag: 清除目录标记
    :return: barname_list  学生条形码名称列表数据
    """
    if clear_flag:
        # 清空文件夹文件
        clear_directory(folder_path)
        # 获取学生模块对象
        stu_class = KpStudent()
        # 获取班级学生准考证号
        student_list = stu_class.query_class_student_zkzh()
        # 批量生成学生条形码
        list(map(generate_barcode, student_list)) if student_list else []
    # 获取目录下所有文件名的列表
    barname_list = get_file_list(folder_path)
    # 返回文件名列表
    return barname_list


def get_pdf_pic(barname_list, c_name, name):
    # 获取题卡文件夹
    card_folder = get_file_path(c_name)
    # 移动指定目录题卡文件到当前题卡目录(card_folder)
    pdf_path = get_file_path(name, kp_info['origin_path'])
    move_file_to_directory(logger, pdf_path, card_folder)
    # 检查题卡目录是否存在pdf文件
    if not get_file_list(card_folder):
        return None
    # 存在文件时，进行生成题卡图片操作,返回元祖包含题卡文件夹路径及pdf文件路径
    barcode_count = len(barname_list)
    # pdf转图片并复制图片数量（条形码数量），返回图片pdf文件路径及图片文件夹名称
    card_tuple = generate_card_pic(logger, barcode_count, card_folder, file_name=name)
    return card_tuple


def create_image_info(stuname_list, b_folder, c_folder):
    # 获取准考证号定位、选择题定位、准考证号的形式【条形码还是填充】
    zk_position, xz_position, form = get_point_info()
    # 判断题卡文件是否存在并且是手阅类型
    card_id = card_class.find_card_type(file_name)
    # 获取题卡中解答题题组满分、打分类型、打分定位点
    card_item = card_class.get_zgt_preview_info(card_id) if card_id else None
    # 遍历学生准考证号文件名
    for i, stuname in enumerate(stuname_list, 1):
        # 获取条形码图片完整路径,准考证号条形码方式使用
        b_file = get_file_path(stuname, b_folder)
        # 获取题卡奇数图片,填涂信息都在奇数页
        c_file = get_file_path(f'{2 * i - 1:02d}.jpg', c_folder)
        # 获取题卡偶数图片,手阅操作使用
        d_file = get_file_path(f'{2 * i:02d}.jpg', c_folder)
        # 获取学生准考证号,准考证号填涂使用
        stu_barcode = stuname.split('.')[0]
        # 生成题卡数据【包含条形码粘贴、准考证号填充、选择题填充、第一页的手阅】
        create_image_data(b_file, c_file, stu_barcode, zk_position, xz_position, form, card_item)
        # 网阅题卡直接跳过
        if card_item is None:
            continue
        # 第二页题卡进行手阅操作
        short_answer_scoring(d_file, card_item)
    logger.info('题卡数据制造完成！')


def main():
    # 获取学校条形码文件夹
    barcode_folder = get_file_path(kp_info['b_name'])
    # 获取学生人数
    barname_list = get_student_count(barcode_folder, clear_flag=False)
    if not barname_list:
        logger.info('错误：获取学生人数有误！')
        return

    # pdf题卡转图片，并按学生人数复制题卡图片,返回题卡图片文件夹路径及pdf文件路径
    card_tuple = get_pdf_pic(barname_list, kp_info['c_name'], f'{file_name}.pdf')
    if not card_tuple:
        logger.info(f'错误：题卡文件夹没有pdf文件!')
        return

    # 条形码粘贴到题卡图片或准考证号填涂,并进行选择题填涂
    create_image_info(barname_list, barcode_folder, card_tuple[1])

    # 移动题卡及题卡图片文件夹到指定文件夹[判断测试环境还是正式环境]
    final_path = get_file_path(kp_info['org_name'],
                               kp_info['test_path' if kp_info['env_flag'] == 'test' else 'prod_path'])
    [move_file_to_directory(logger, soure_path, final_path) for soure_path in card_tuple]


if __name__ == '__main__':
    file_name = '手阅测试题卡'  # 移动文件到cardinfo目录时需要传文件名(带后缀名)
    main()
