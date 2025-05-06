import math


class GenerateExcelStu:
    def __init__(self):
        self.excel_path = r'D:\PyCharm 2024.1.4\KpProject\QuestionCard\KpRequest\excel'

    @staticmethod
    def _get_lables(exam_mode):
        """
        根据是否新高考标签查询选考标签
        :param exam_mode: 高考模式
        :return: 选考标签列表 or None
        """
        # 判断是否新高考模式
        is_new_gaokao = True if exam_mode in ['3+1+2', '3+3', '文理分科'] else False
        if not is_new_gaokao: return
        from QuestionCard.KpRequest import KpLogin, KpStudent
        login = KpLogin.KpLogin()
        student_client = KpStudent.KpStudent(login, ids_run=False)
        return student_client.get_exam_label(exam_mode)

    @staticmethod
    def _generate_school(stu_number, index):
        """
        生成学生学校列数据
        :param stu_number: 总的学生数
        :param index: 第n个学生数
        :return:
        """
        return '胡林辉二校' if index > (stu_number / 2) else '胡林辉一校'

    @staticmethod
    def _generate_class(stu_number, class_number, index):
        """
        均分学生数量并生成班级名称
        :param stu_number: 总学生数量
        :param class_number: 总班级数量
        :param index: 第n个学生数
        :return:
        """
        if index > (stu_number / 2):
            return f'{math.ceil((index - (stu_number / 2)) / class_number):02d}班'
        else:
            return f'{math.ceil(index / class_number):02d}班'

    def _generate_exam_data(self, label_list, students_count, class_count):
        """
        生成考生数据
        :param label_list: 选考标签列表
        :param students_count: 默认学生人数
        :param class_count: 默认班级个数
        :return:
        """
        from faker import Faker

        total_students = len(label_list) if label_list else students_count
        class_stu, faker = int(total_students / 2 / class_count), Faker("zh-CN")
        excel_data = {
            '准考证号(必填)': [f'{1300000 + i}' for i in range(1, total_students + 1)],
            '学校(必填)': [self._generate_school(total_students, i) for i in range(1, total_students + 1)],
            '班级(必填)': [self._generate_class(total_students, class_stu, i) for i in range(1, total_students + 1)],
            '姓名(必填)': [faker.name() for _ in range(1, total_students + 1)]
        }
        if label_list: excel_data['选考标签(必填)'] = [info[1] for info in label_list]
        return excel_data

    def _save_to_excel(self, exam_data):
        """
        将数据保存到 Excel 文件。
        :param exam_data:考试数据字典
        :return:
        """
        import pandas as pd

        df = pd.DataFrame(exam_data)
        file_path = f'{self.excel_path}/临时考生上报模版.xlsx'
        df.to_excel(file_path, index=False)

    def run(self, exam_mode):
        """
        1、初始化数据和判断是否新高考模式
        2、获取新高考模式选考标签
        3、生成临时考生数据
        4、保存到Excel
        :param exam_mode:考试模式标签（普通和新高考【文理分科、3+1+2、3+3】）
        :return:
        """
        # 初始化学生人数及班级个数
        total_students, class_count = 100, 3
        # 获取新高考模式的选考标签数据
        label_list = self._get_lables(exam_mode)
        # 生成临时考生数据
        exam_data = self._generate_exam_data(label_list, total_students, class_count)
        # 保存到Excel
        self._save_to_excel(exam_data)


if __name__ == '__main__':
    GenerateExcelStu().run('3+1+2')
