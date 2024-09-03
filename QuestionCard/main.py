from QuestionCard.KpRequest.StudentZkzhData import StudentZkzhData
from QuestionCard.GenerateBarcode import generate_barcode
from QuestionCard.PdfConvertImage import generate_card_pic, get_file_list, get_file_path, move_file_to_directory
from QuestionCard.EditImage import resize_and_paste_image


def get_student_count(folder_path):
    """
    根据barcode文件夹中的学生条形码图片个数获取学生人数，即图片人数=学生人数
    文件夹中无图片或者需要更新时，获取系统学生信息
    :return: barname_list  学生条形码名称列表数据
    """
    if not get_file_list(folder_path):
        student_list = stu_class.run()
        if not student_list:
            return []
        for student in student_list:
            generate_barcode(*student)
    barname_list = get_file_list(folder_path)
    return barname_list


def get_pdf_pic(barname_list, c_name, name):
    # 获取题卡文件夹
    card_folder = get_file_path(c_name)
    # 移动指定目录题卡文件到当前题卡目录(card_folder)
    pdf_path = get_file_path(name, kp_info['origin_path'])
    move_file_to_directory(pdf_path, card_folder)
    # 检查题卡目录是否存在pdf文件
    if not get_file_list(card_folder):
        return None
    # 存在文件时，进行生成题卡图片操作,返回元祖包含题卡文件夹路径及pdf文件路径
    barcode_count = len(barname_list)
    card_tuple = generate_card_pic(barcode_count, card_folder, file_name=name)
    return card_tuple


def create_image_info(stuname_list, b_folder, c_folder):
    for i, stuname in enumerate(stuname_list, 1):
        c_file = get_file_path(f'{2 * i - 1:02d}.jpg', c_folder)
        b_file = get_file_path(stuname, b_folder)
        position, size = (kp_info['ie_pos'], kp_info['ie_size']) if kp_info['exam_flag'] else (
            kp_info['je_pos'], kp_info['je_size'])
        resize_and_paste_image(c_file, b_file, position=eval(position), size=eval(size))  # 联考与校内考题卡条形码位置不一致（需要重新设置）
    print('题卡数据制造完成！')


def main():
    # 获取学校条形码文件夹
    barcode_folder = get_file_path(kp_info['b_name'])
    # 获取学生人数
    barname_list = get_student_count(barcode_folder)
    if not barname_list:
        print('错误：获取学生人数有误！')
        return

    # pdf题卡转图片，并按学生人数复制题卡图片,返回题卡图片文件夹路径及pdf文件路径
    card_tuple = get_pdf_pic(barname_list, kp_info['c_name'], file_name)
    if not card_tuple:
        print(f'错误：题卡文件夹没有pdf文件!')
        return

    # 条形码粘贴到题卡图片
    create_image_info(barname_list, barcode_folder, card_tuple[1])

    # 移动题卡及题卡图片文件夹到指定文件夹[判断测试环境还是正式环境]
    final_path = kp_info['test_path'] if kp_info['env_flag'] else kp_info['prod_path']
    [move_file_to_directory(soure_path, final_path) for soure_path in card_tuple]


if __name__ == '__main__':
    file_name = '语文手阅0830.pdf'   # 移动文件到cardinfo目录时需要传文件名(带后缀名)
    # 实例化一个学生类
    stu_class = StudentZkzhData()
    # 获取学生类的kp数据
    kp_info = stu_class.kp_data
    main()
