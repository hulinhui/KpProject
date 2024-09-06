import os
import shutil
from pdf2image import convert_from_path


def move_file_to_directory(source_path, destination_directory):
    """
    移动文件及文件夹到指定的目录。
    :param source_path: str, 源文件的路径。
    :param destination_directory: str, 目标目录的路径。
    """
    # 确保目标目录存在，如果不存在则创建
    os.makedirs(destination_directory, exist_ok=True)
    source_name = os.path.basename(source_path)
    dest_dir_name = os.path.basename(destination_directory)
    # 移动文件及文件夹
    try:
        shutil.move(source_path, destination_directory)
    except FileNotFoundError:
        print(f"错误：题卡文件-{source_name}不存在！")
    else:
        print(f"题卡文件-{source_name}已移动到指定文件夹-{dest_dir_name}")


def get_file_path(folder_name, root=None):
    """
    进行文件路径的拼接
    :param folder_name: 文件夹名称
    :param root: 原始文件夹
    :return: 绝对路径
    """
    if root is None:
        return os.path.join(os.getcwd(), folder_name)
    else:
        return os.path.join(root, folder_name)


def get_file_list(folder_path):
    """
    获取文件夹下的文件，返回文件名列表
    :param folder_path:
    :return: file_list
    """
    file_list = []
    for name in os.listdir(folder_path):
        file_path = get_file_path(name, folder_path)
        if os.path.isfile(file_path):
            file_list.append(name)
    return file_list


def get_newest_pdf(directory):
    # 获取目录中所有文件的列表
    files = os.listdir(directory)

    # 过滤出PDF文件并获取它们的修改时间
    pdf_files_with_mtime = [(f, os.path.getmtime(get_file_path(f, directory))) for f in files if
                            f.lower().endswith('.pdf')]
    # 按修改时间排序，获取最新的PDF文件
    newest_pdf = max(pdf_files_with_mtime, key=lambda x: x[1])[0]

    # 返回最新的PDF文件路径
    return newest_pdf


def convert_pdf_to_jpg(pdf_path, dpi=300):
    """
    将PDF文件转换为JPG图片。

    参数:
    pdf_name (str): PDF文件名。
    dpi (int): 转换时使用的DPI值，DPI越高，输出图片的分辨率越高。
    output_path:输出图片的文件夹路径
    """
    path_list = []
    # 获取pdf去掉后缀的文件名
    output_folder = os.path.splitext(pdf_path)[0]
    # 不存在文件夹即创建文件夹
    os.makedirs(output_folder, exist_ok=True)
    # pdf转图片
    images = convert_from_path(pdf_path, dpi=dpi, poppler_path=r'D:\poppler-24.07.0\Library\bin')

    # 保存图片到指定的文件夹
    for i, image in enumerate(images, 1):
        # 设置输出路径和文件名
        output_path = get_file_path(f'{i:02d}.jpg', output_folder)
        # 将PIL图像对象转换为JPG格式并保存
        image.save(output_path, 'JPEG')
        path_list.append(output_path)
    return path_list


def copy_images_in_sequence(number, img_path_01, img_path_02):
    """
    复制指定数量的01和02图片，并按照奇偶数命名。

    参数:
    number (int): 需要复制的图片数量。
    img_path_01 (str): 第一个图片的路径。
    img_path_02 (str): 第二个图片的路径。
    """
    # 获取图片文件目录
    output_folder = os.path.dirname(img_path_01)
    # 确保输出目录存在
    os.makedirs(output_folder, exist_ok=True)

    # 复制图片
    for i in range(3, 2 * number, 2):
        # 复制01图片，使用奇数索引
        shutil.copy(img_path_01, os.path.join(output_folder, f'{i:02d}.jpg'))
        # 复制02图片，使用偶数索引
        shutil.copy(img_path_02, os.path.join(output_folder, f'{i + 1:02d}.jpg'))
    # 复制图片后的图片个数
    pic_num = len(get_file_list(output_folder))
    return pic_num


def generate_card_pic(count, card_folder, file_name):
    """
       未传文件名时，默认取folder文件夹中最新的pdf文件，传文件名取文件名文件

       参数:
       :param count: 复制图片的数量。
       :param card_folder : 题卡文件夹。
       :param file_name: pdf文件名。
       :return tuple  pdf文件路径及题卡图片文件夹
       """
    # if file_name is None:
    #     file_name = get_newest_pdf(card_folder)
    # 获取pdf文件完整路径
    pdf_path = get_file_path(file_name, card_folder)
    # pdf转图片，并返回文件路径列表
    pic_path_list = convert_pdf_to_jpg(pdf_path)
    print(f'题卡-{file_name}：转图片生成{len(pic_path_list)}张图片')
    # 图片复制
    pic_count = copy_images_in_sequence(count, *pic_path_list)
    print(f'题卡-{file_name}:复制图片共{pic_count}张图片')
    # 返回pdf文件路径及图片文件夹名称，图片文件夹名称=pdf不带后缀的文件名
    return pdf_path, os.path.splitext(pdf_path)[0]


if __name__ == '__main__':
    generate_card_pic(1, 'cardinfo', file_name='高中语文联考0822.pdf')
