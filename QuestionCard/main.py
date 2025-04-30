from QuestionCard.GenerateBarcode import generate_barcode
from QuestionCard.PdfConvertImage import (generate_card_pic, get_file_list, LazyModule,
                                          get_file_path, move_file_to_directory, clear_directory)
from QuestionCard.EditImage import create_image_data, short_answer_scoring


class CardImageGenerator:
    def __init__(self, login):
        """
        初始化登录对象及所需配置数据
        :param login: 登录类对象
        """
        self.login = login
        self.data = self.login.kp_data
        self.logger = self.login.logger

    def get_point_info(self):
        """
        (1,1):    校内考+条形码：    条形码定位+条形码选择题定位+准考证形式
        (1,0):    校内考+准考证填涂：  准考证定位+准考证选择题定位+准考证形式
        (0,1):    联考+条形码：       联考条形码定位+联考条形码选择题定位+准考证形式
        (0,0):    联考+准考证填涂：   联考准考证定位+联考准考证选择题定位+准考证形式
        :return: 根据exam_flag和number_from交互场景，返回对应场景的定位点元祖信息
        """
        exam_model, zkzh_type = int(self.data['exam_flag']), int(self.data['number_from'])
        point_item = {
            (1, 1): (self.data['ie_pos'], self.data['ie_xz_tpos'], int(self.data['number_from'])),
            (1, 0): (self.data['ie_zh_pos'], self.data['ie_xz_zpos'], int(self.data['number_from'])),
            (0, 1): (self.data['je_pos'], self.data['je_xz_tpos'], int(self.data['number_from'])),
            (0, 0): (self.data['je_zh_pos'], self.data['je_xz_zpos'], int(self.data['number_from']))
        }
        return point_item.get((exam_model, zkzh_type), "无效的输入")

    def get_student_count(self, folder_path, clear_flag):
        """
        根据barcode文件夹中的学生条形码图片个数获取学生人数，即图片人数=学生人数
        文件夹中无图片或者需要更新时，获取系统学生信息
        :param folder_path: 文件夹路径
        :param clear_flag: 清除目录标记
        :return: barname_list  学生条形码名称列表数据
        """
        if clear_flag:
            # 清空文件夹文件
            clear_directory(folder_path)
            # 获取学生模块对象
            Student = LazyModule('QuestionCard.KpRequest.KpStudent')
            stu_class = Student.KpStudent(self.login)
            # 获取班级学生准考证号
            student_list = stu_class.query_class_student_zkzh()
            # 批量生成学生条形码
            list(map(generate_barcode, student_list)) if student_list else []
        # 获取目录下所有文件名的列表
        barname_list = get_file_list(folder_path)
        # 返回文件名列表
        return barname_list

    def get_pdf_pic(self, barname_list, name):
        """
        1、将pdf文件转成对应尺寸图片jpg
        2、复制图片指定份数
        :param barname_list: 图片份数
        :param name: pdf文件名（两页题卡）
        :return: 元祖包含题卡文件夹路径及pdf文件路径
        """
        # 获取题卡文件夹
        card_folder = get_file_path(self.data['c_name'])
        # 移动指定目录题卡文件到当前题卡目录(card_folder)
        pdf_path = get_file_path(name, self.data['origin_path'])
        move_file_to_directory(self.logger, pdf_path, card_folder)
        # 检查题卡目录是否存在pdf文件
        if not get_file_list(card_folder):
            return None
        # 存在文件时，进行生成题卡图片操作,返回元祖包含题卡文件夹路径及pdf文件路径
        barcode_count = len(barname_list) * 2
        # pdf转图片并复制图片数量（条形码数量），返回图片pdf文件路径及图片文件夹名称
        card_tuple = generate_card_pic(self.logger, barcode_count, card_folder, file_name=name)
        return card_tuple

    def create_image_info(self, stuname_list, b_folder, c_folder, file_name):
        """
        填充图片的准考证号或粘贴条形码及客观题随机答案，手阅模版进行随机打分
        :param stuname_list: 考生图片文件名列表
        :param b_folder: 条形码文件夹
        :param c_folder: 题卡文件夹
        :param file_name: pdf文件名
        :return:
        """
        # 获取准考证号定位、选择题定位、准考证号的形式【条形码还是填充】
        zk_position, xz_position, form = self.get_point_info()
        # 判断题卡文件是否存在并且是手阅类型
        # 导入KpCard文件
        KpCard = LazyModule('QuestionCard.KpRequest.KpCard')
        # 加载KpCard题卡对象
        card_class = KpCard.KpCard(login_class)
        card_id = card_class.find_card_type(file_name)
        # 获取题卡中解答题题组满分、打分类型、打分定位点
        card_item = card_class.get_zgt_preview_info(card_id) if card_id else None
        # 获取图片文件名填充的长度
        file_len = len(str(len(stuname_list) * 2))
        # 遍历学生准考证号文件名
        for i, stuname in enumerate(stuname_list, 1):
            # 获取条形码图片完整路径,准考证号条形码方式使用
            b_file = get_file_path(stuname, b_folder)
            # 获取题卡奇数图片,填涂信息都在奇数页
            c_file = get_file_path(f'{2 * i - 1:0{file_len}d}.jpg', c_folder)
            # 获取题卡偶数图片,手阅操作使用
            d_file = get_file_path(f'{2 * i:0{file_len}d}.jpg', c_folder)
            # 获取学生准考证号,准考证号填涂使用
            stu_barcode = stuname.split('.')[0]
            # 生成题卡数据【包含条形码粘贴、准考证号填充、选择题填充、第一页的手阅】
            create_image_data(b_file, c_file, stu_barcode, zk_position, xz_position, form, card_item)
            # 网阅题卡直接跳过
            if card_item is None: continue
            # 第二页题卡进行手阅操作
            short_answer_scoring(d_file, card_item)
        self.logger.info('题卡数据制造完成！')

    def run(self, f_name, c_flag=None):
        """
        输入pdf文件民（不带后缀名）和是否清空barcode文件夹标记，返回生成的题卡图片
        :param f_name: 文件名
        :param c_flag: 条形码文件夹（barcode）清空标记
        :return:
        """
        # 获取学校条形码文件夹
        barcode_folder = get_file_path(self.data['b_name'])
        # 获取学生人数
        barname_list = self.get_student_count(barcode_folder, c_flag)
        if not barname_list:
            self.logger.info('错误：获取学生人数有误！')
            return

        # pdf题卡转图片，并按学生人数复制题卡图片,返回题卡图片文件夹路径及pdf文件路径
        card_tuple = self.get_pdf_pic(barname_list, f'{f_name}.pdf')
        if not card_tuple:
            self.logger.info(f'错误：题卡文件夹没有pdf文件!')
            return

        # 条形码粘贴到题卡图片或准考证号填涂,并进行选择题填涂
        self.create_image_info(barname_list, barcode_folder, card_tuple[1], f_name)

        # 移动题卡及题卡图片文件夹到指定文件夹[判断测试环境还是正式环境]
        env_path = 'test_path' if self.data['env_flag'] == 'test' else 'prod_path'
        final_path = get_file_path(self.data['org_name'], self.data[env_path])
        [move_file_to_directory(self.logger, soure_path, final_path) for soure_path in card_tuple]


if __name__ == '__main__':
    KpLogin = LazyModule('QuestionCard.KpRequest.KpLogin')
    login_class = KpLogin.KpLogin()
    card = CardImageGenerator(login_class)
    card.run(f_name='自制题卡网阅数据', c_flag=None)
