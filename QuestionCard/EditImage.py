from PIL import Image


def paste_png_on_jpeg(target_path, source_path, result_path, position=(0, 0), source_size=None):
    """
    将PNG格式的图片粘贴到JPEG格式的图片上。

    :param target_path: 目标JPEG图片的路径
    :param source_path: 源PNG图片的路径
    :param result_path: 结果图片的保存路径
    :param position: 源图片在目标图片上的粘贴位置
    :param source_size: 源图片的新尺寸，如果为None则不改变尺寸
    """
    # 打开JPEG图片和PNG图片
    target_image = Image.open(target_path)
    source_image = Image.open(source_path)

    # 如果提供了source_size，则调整源图片大小
    if source_size:
        source_image = source_image.resize(source_size)

    # 将JPEG图片转换为RGBA格式以支持透明度
    target_image = target_image.convert('RGBA')

    # 将PNG图片粘贴到JPEG图片上
    target_image.paste(source_image, position, source_image)

    # 将结果图片保存为PNG格式（因为JPEG不支持透明度）
    target_image.save(result_path, 'PNG')


# 使用示例
paste_png_on_jpeg(
    target_path=r'C:\Users\Administrator\Downloads\document\测试题卡\高中语文20240812提卡\01.jpg',  # 目标JPEG图片路径
    source_path=r'./my_barcode.png',  # 源PNG图片路径
    result_path=r'C:\Users\Administrator\Downloads\document\测试题卡\高中语文20240812提卡\01_image.png',  # 结果图片保存路径
    position=(390, 140),  # 粘贴位置
    source_size=(180, 90)  # 源图片新尺寸，如果不需要改变大小则传None
)
