import re
from dataclasses import dataclass
from typing import Set, Tuple
from pathlib import Path


@dataclass(frozen=True)
class WifiNetwork:
    """WiFi网络信息数据类
    
    Attributes:
        ssid: WiFi网络名称
        psk: WiFi密码
    """
    ssid: str
    psk: str

    def __str__(self):
        return f"SSID: {self.ssid}, Password: {self.psk}"


class WifiParser:
    def __init__(self, file_path):
        """
        初始化WifiParser类
        :param file_path: WLAN设置文件的路径
        """
        # 使用Path处理路径
        self.file_dir = Path(__file__).parent / 'txt'
        self.input_file_path = self.file_dir / file_path
        self.output_file_path = self.file_dir / 'WifiInfo.txt'
        self.networks: Set[Tuple[str, str]] = set()
        self.ssid_pattern = re.compile(r'SSID="([^"]*)"')
        self.psk_pattern = re.compile(r'PreSharedKey="([^"]*)"')

    @staticmethod
    def _extract_value(pattern, text):
        """
        从文本中提取匹配模式的值
        :param pattern: 编译好的正则表达式
        :param text: 要匹配的文本
        :return: 匹配到的值或None
        """
        match = pattern.search(text)
        return match.group(1) if match else None

    def _parse_network_block(self, block):
        """
        解析单个网络配置块
        :param block: 网络配置块文本
        :return: (ssid, psk) 或 None
        """
        ssid = self._extract_value(self.ssid_pattern, block)
        psk = self._extract_value(self.psk_pattern, block)

        if ssid and psk and psk != 'null':
            return ssid, psk
        return None

    def network_generator(self):
        """
        生成器函数，逐个产生网络信息
        :yield: (ssid, psk) 元组
        """
        try:
            with open(self.input_file_path, 'r', encoding='utf-8', buffering=8192) as file:
                current_block = []
                for line in file:
                    if line.strip() == 'network={':
                        current_block = []
                    elif line.strip() == '}' and current_block:
                        block_text = '\n'.join(current_block)
                        network_info = self._parse_network_block(block_text)
                        if network_info:
                            yield network_info
                        current_block = []
                    else:
                        current_block.append(line.strip())
        except Exception as e:
            print(f"解析文件时出错: {str(e)}")

    def parse(self):
        """
        解析WLAN设置文件，提取所有网络的SSID和PreSharedKey
        :return: 包含所有不重复网络信息的集合
        """
        self.networks = {network_info for network_info in self.network_generator()}
        return self.networks

    def get_networks(self):
        """
        获取所有已解析的网络信息
        :return: 网络信息集合
        """
        return {WifiNetwork(ssid, psk) for ssid, psk in self.networks}

    def save_to_file(self):
        """
        将WiFi信息保存到文件
        """
        if not self.networks:
            print("没有找到任何网络信息，无法保存到文件")
            return

        try:
            with open(self.output_file_path, 'w', encoding='utf-8') as f:
                networks = [WifiNetwork(ssid, psk) for ssid, psk in self.networks]
                for i, network in enumerate(sorted(networks, key=lambda x: x.ssid), 1):
                    f.write(f"{i}. {network}\n")
            print(f"WiFi信息已保存到文件：{self.output_file_path}")
        except Exception as e:
            print(f"保存文件时出错: {str(e)}")

    def print_networks(self):
        """
        打印所有网络信息
        """
        if not self.networks:
            print("没有找到任何网络信息")
            return

        print(f"找到以下{len(self.networks)}个网络：")
        networks = [WifiNetwork(ssid, psk) for ssid, psk in self.networks]
        for i, network in enumerate(sorted(networks, key=lambda x: x.ssid), 1):
            print(f"{i}. {network}")


def main():
    # 使用Path处理路径
    file_name = 'WLAN设置(com.android.settings).txt'
    parser = WifiParser(file_name)
    parser.parse()
    parser.print_networks()
    parser.save_to_file()


if __name__ == "__main__":
    main()
