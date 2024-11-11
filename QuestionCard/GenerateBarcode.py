from barcode import Code128
from barcode.writer import ImageWriter


def generate_barcode(data):
    """生成一个Code 128条形码并将其保存为图片文件,，图片名称=条形码"""
    # 创建一个Code 128条形码实例
    barcode = Code128(data, writer=ImageWriter())
    # 保存条形码为图片文件
    barcode.save('barcode/' + data,
                 options={'format': 'png', 'module_width': 0.2, 'module_height': 8, 'font_size': 4,
                          'text_distance': 1.8,
                          'quiet_zone': 0.5})
    print(f"Barcode saved as {data}.png")


if __name__ == '__main__':
    # 使用该函数生成一个条形码
    barcode_list = [str(i) for i in range(1300001, 1300019)]
    for code in barcode_list:
        generate_barcode(code)
