"""
图片旋转处理工具
作者: hulinhui6
日期：2025年05月28日
"""
import cv2
import os
import numpy as np
from typing import Optional


class ImageRotator:
    """图片旋转处理类"""

    SUPPORTED_DEGREES = {
        90: cv2.ROTATE_90_CLOCKWISE,
        180: cv2.ROTATE_180,
        270: cv2.ROTATE_90_COUNTERCLOCKWISE
    }

    def __init__(self, image_path: str):
        """
        初始化图片旋转器
        Args:image_path (str): 输入图片路径
        """
        self.image_path = image_path
        self.image = None
        self._load_image()

    def _load_image(self) -> None:
        """
        加载图片并进行基本检查
        Raises:
            FileNotFoundError: 图片文件不存在
            ValueError: 图片加载失败
        """
        if not os.path.exists(self.image_path):
            raise FileNotFoundError(f"找不到图片文件：{self.image_path}")

        # 使用numpy读取图片以支持中文路径
        try:
            self.image = cv2.imdecode(np.fromfile(self.image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if self.image is None:
                raise ValueError(f"无法加载图片：{self.image_path}")
        except Exception as e:
            raise ValueError(f"读取图片失败：{str(e)}")

    def rotate(self, angle: int, scale: float = 1.0) -> np.ndarray:
        """
        将图片旋转指定角度

        Args:
            angle (int): 旋转角度（支持任意角度）
            scale (float): 缩放比例，默认为1.0

        Returns:
            np.ndarray: 旋转后的图片

        Raises:
            ValueError: 图片未正确加载
        """
        if self.image is None:
            raise ValueError("图片未正确加载")

        # 对于90度的倍数，使用更快的方法
        if angle in self.SUPPORTED_DEGREES:
            return cv2.rotate(self.image, self.SUPPORTED_DEGREES[angle])

        # 对于其他角度，使用仿射变换
        height, width = self.image.shape[:2]
        center = (width / 2, height / 2)

        # 获取旋转矩阵
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, scale)

        # 计算新图像的尺寸
        abs_cos = abs(rotation_matrix[0, 0])
        abs_sin = abs(rotation_matrix[0, 1])
        new_width = int(height * abs_sin + width * abs_cos)
        new_height = int(height * abs_cos + width * abs_sin)

        # 调整旋转矩阵
        rotation_matrix[0, 2] += new_width / 2 - center[0]
        rotation_matrix[1, 2] += new_height / 2 - center[1]

        # 执行旋转
        rotated_image = cv2.warpAffine(
            self.image,
            rotation_matrix,
            (new_width, new_height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255)
        )

        return rotated_image

    def save_image(self, rotated_image: np.ndarray, output_path: Optional[str] = None, quality: int = 95) -> str:
        """
        保存旋转后的图片

        Args:
            rotated_image (np.ndarray): 旋转后的图片数组
            output_path (str, optional): 输出路径，默认在原图片名前加上'rotated_'
            quality (int): 图片质量，范围1-100，默认95

        Returns:
            str: 保存后的文件路径

        Raises:
            ValueError: 保存图片失败
        """
        if output_path is None:
            directory = os.path.dirname(self.image_path)
            filename = os.path.basename(self.image_path)
            output_path = os.path.join(directory, filename)

        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # 设置图片压缩参数
        params = [cv2.IMWRITE_JPEG_QUALITY, quality] if output_path.lower().endswith(('.jpg', '.jpeg')) else []

        # 使用imencode和fromfile来支持中文路径
        try:
            # 编码图片数据
            ext = os.path.splitext(output_path)[1]
            _, img_encoded = cv2.imencode(ext, rotated_image, params)
            # 写入文件
            img_encoded.tofile(output_path)
            return output_path
        except Exception as e:
            raise ValueError(f"保存图片失败：{str(e)}")


def main():
    """主函数"""
    try:
        # 设置测试参数
        image_path = r"C:\Users\Administrator\Downloads\document\测试题卡\胡林辉一校\2个主观题\22.jpg"
        rotation_angle = 180  # 支持任意角度

        # 创建图片旋转器实例
        rotator = ImageRotator(image_path)

        # 执行旋转
        rotated_img = rotator.rotate(rotation_angle)

        # 保存结果
        output_path = rotator.save_image(rotated_img)
        print(f"旋转后的图片已保存：{output_path}")

    except Exception as e:
        print(f"处理图片时出错：{str(e)}")


if __name__ == '__main__':
    main()
