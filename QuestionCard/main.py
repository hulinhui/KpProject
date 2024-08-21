from QuestionCard.KpRequest.StudentZkzhData import StudentZkzhData
from QuestionCard.GenerateBarcode import generate_barcode
from QuestionCard.PdfConvertImage import generate_card_pic, get_file_count, get_file_path, move_file_to_directory
from QuestionCard.EditImage import resize_and_paste_image


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


def get_pdf_pic(count, card_folder, name=None):
    if name is not None:
        move_file_to_directory(name, card_folder)
    if not get_file_count(card_folder):
        return
    card_child_folder = generate_card_pic(count, card_folder, file_name=name)  # 该函数可直接传pdf文件名,不传默认最新pdf文件
    return card_child_folder


def get_image_info(student_count, b_folder, c_folder):
    for i in range(1, student_count + 1):
        c_file = get_file_path(f'{2 * i - 1:02d}.jpg', c_folder)
        b_file = get_file_path(f'学生{i}.png', b_folder)
        resize_and_paste_image(c_file, b_file)
    print('题卡数据制造完成！')


def main(file_name=None, b_name='barcode', c_name='cardinfo'):
    barcode_folder = get_file_path(b_name)
    student_count = get_student_count(barcode_folder)
    if not student_count:
        print('出现错误：获取学生人数有误！')
        return
    card_folder = get_file_path(c_name)
    card_child_folder = get_pdf_pic(student_count, card_folder, file_name)
    if not card_child_folder:
        print(f'出现错误：题卡文件夹没有pdf文件!')
        return
    get_image_info(student_count, barcode_folder, card_child_folder)


if __name__ == '__main__':
    main()  # 移动文件到cardinfo目录时需要传文件名
