import os
import shutil

from pdf2image import convert_from_path

poppler_path = r'D:\poppler-24.07.0\Library\bin'
card_folder = r'C:\Users\Administrator\Downloads\document\测试题卡'


def convert_pdf_to_jpg(pdf_name, dpi=300):
    """
    将PDF文件转换为JPG图片。

    参数:
    pdf_name (str): PDF文件名。
    dpi (int): 转换时使用的DPI值，DPI越高，输出图片的分辨率越高。
    output_path:输出图片的文件夹路径
    """
    path_list = []
    pdf_file_path = os.path.join(card_folder, pdf_name)
    output_folder = os.path.join(card_folder, pdf_name.split('.')[0])
    os.makedirs(output_folder, exist_ok=True)
    images = convert_from_path(pdf_file_path, dpi=dpi, poppler_path=poppler_path)

    # 保存图片到指定的文件夹
    for i, image in enumerate(images, 1):
        # 设置输出路径和文件名
        output_path = os.path.join(output_folder, f'{i:02d}.jpg')
        # 将PIL图像对象转换为JPG格式并保存
        image.save(output_path, 'JPEG')
        print(f"第{i}张图片保存成功: {i:02d}.jpg")
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
    print('题卡图片复制完成!')


if __name__ == '__main__':
    pic_path_list = convert_pdf_to_jpg('高中语文20240812提卡.pdf')
    copy_images_in_sequence(10, *pic_path_list)
