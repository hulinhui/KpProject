from PIL import Image


def resize_and_paste_image(background_path, foreground_path, position, size):
    """
    将一张图片缩放到指定大小，然后放置到另一张图片的指定位置上并保存合成后的新图。

    :param background_path: 背景图片的路径
    :param foreground_path: 要放置的图片（前景）的路径
    :param position: 前景图片放置的位置，格式为 (x, y)
    :param size: 前景图片缩放的目标大小，格式为 (width, height)
    :param output_path: 合成后的图片保存的路径
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


if __name__ == '__main__':
    # 示例代码使用
    b_path = r'./cardinfo/高中历史20240820170434/19.jpg'  # 背景图片的路径
    f_path = './barcode/学生10.png'  # 前景图片的路径
    f_pos = (1510, 510)  # 前景图片放置的位置（x, y）
    f_size = (780, 370)  # 前景图片缩放的目标大小
    print(type(f_pos),type(f_size))
    resize_and_paste_image(b_path, f_path, f_pos, f_size)
