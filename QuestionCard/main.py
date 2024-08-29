from QuestionCard.KpRequest.StudentZkzhData import StudentZkzhData
from QuestionCard.GenerateBarcode import generate_barcode
from QuestionCard.PdfConvertImage import generate_card_pic, get_file_count, get_file_path, move_file_to_directory
from QuestionCard.EditImage import resize_and_paste_image

# 从指定目录获取pdf题卡文件
origin_path = r'C:\Users\Administrator\Downloads'

# 最终pdf文件和pdf图片目录存放的路径
final_path = r'C:\Users\Administrator\Downloads\document\测试题卡'


def get_student_count(folder_path):
    """
    根据barcode文件夹中的学生条形码图片个数获取学生人数，即图片人数=学生人数
    文件夹中无图片或者需要更新时，获取系统学生信息
    :return: student_count  学生人数
    """
    student_count = 0
    if not get_file_count(folder_path):
        student_list = StudentZkzhData().get_student_data()
        if not student_list:
            return student_count
        for student in student_list:
            generate_barcode(*student)
            student_count += 1
        return student_count
    else:
        student_count = get_file_count(folder_path)
        return student_count


def get_pdf_pic(count, c_name, name):
    # 获取题卡文件夹
    card_folder = get_file_path(c_name)
    # 移动指定目录题卡文件到当前题卡目录(card_folder)
    pdf_path = get_file_path(name, origin_path)
    move_file_to_directory(pdf_path, card_folder)
    # 检查题卡目录是否存在pdf文件
    if not get_file_count(card_folder):
        return None
    # 存在文件时，进行生成题卡图片操作,返回元祖包含题卡文件夹路径及pdf文件路径
    card_tuple = generate_card_pic(count, card_folder, file_name=name)
    return card_tuple


def get_image_info(student_count, b_folder, c_folder):
    for i in range(1, student_count + 1):
        c_file = get_file_path(f'{2 * i - 1:02d}.jpg', c_folder)
        b_file = get_file_path(f'学生{i}.png', b_folder)
        resize_and_paste_image(c_file, b_file, position=(1570, 600), size=(700, 350))  # 联考与校内考题卡条形码位置不一致（需要重新设置）
    print('题卡数据制造完成！')


def main(file_name, b_name='barcode', c_name='cardinfo'):
    # 获取学校条形码文件夹
    barcode_folder = get_file_path(b_name)
    # 获取学生人数
    student_count = get_student_count(barcode_folder)
    if not student_count:
        print('错误：获取学生人数有误！')
        return
    # pdf题卡转图片，并按学生人数复制题卡图片,返回题卡图片文件夹路径及pdf文件路径
    card_tuple = get_pdf_pic(student_count, c_name, file_name)
    if not card_tuple:
        print(f'错误：题卡文件夹没有pdf文件!')
        return
    # 条形码粘贴到题卡图片
    get_image_info(student_count, barcode_folder, card_tuple[1])
    # 移动题卡及题卡图片文件夹到指定文件夹
    move_file_to_directory(card_tuple[1], final_path)
    move_file_to_directory(card_tuple[0], final_path)


if __name__ == '__main__':
    main('高中英语0829.pdf')  # 移动文件到cardinfo目录时需要传文件名(带后缀名)
