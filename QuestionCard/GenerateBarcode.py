from barcode import Code128
from barcode.writer import ImageWriter
from pathlib import Path
from typing import Iterable, Union

BARCODE_OPTIONS = {
    'format': 'png',
    'module_width': 0.2,
    'module_height': 8,
    'font_size': 4,
    'text_distance': 1.8,
    'quiet_zone': 0.5
}


def generate_barcode(data: str, save_dir: Path) -> str:
    """生成单个条形码并保存为图片
    Args:
        data: 条形码数据
        save_dir: 保存目录
    Returns:
        str: 生成的条形码图片完整路径
    """
    save_dir.mkdir(exist_ok=True)
    save_path = save_dir / data
    Code128(data, writer=ImageWriter()).save(str(save_path), options=BARCODE_OPTIONS)
    return f'{data}.png'


def batch_generate_barcodes(data_list: Iterable[Union[str, int]], barcode_dir: Path = None) -> list[str]:
    """批量生成条形码
    Args:
        data_list: 条形码数据列表，可以是字符串或数字的可迭代对象
        barcode_dir: 保存目录，默认为脚本同级目录下的 barcode 文件夹
    Returns:
        list[str]: 所有生成的条形码图片名列表
    """
    save_dir = Path(__file__).parent / 'barcode' if barcode_dir is None else barcode_dir
    return [generate_barcode(str(data), save_dir) for data in data_list]


if __name__ == '__main__':
    # 示例：生成一组条形码
    result = batch_generate_barcodes(range(1300001, 1300010))
    print(f"已生成 {len(result)} 个条形码图片")
