from barcode import Code128
from barcode.writer import ImageWriter


def generate_barcode(data, filename='barcode'):
    """生成一个Code 128条形码并将其保存为图片文件"""
    # 创建一个Code 128条形码实例
    barcode = Code128(data, writer=ImageWriter())
    # 保存条形码为图片文件
    barcode.save(filename)
    print(f"Barcode saved as {filename}.png")


# 使用该函数生成一个条形码
barcode_data = "42000002"  # 这是你希望编码的数据
generate_barcode(barcode_data, 'my_barcode')
