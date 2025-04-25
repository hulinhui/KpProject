import pandas as pd
import math
from QuestionCard.KpRequest.KpStudent import KpStudent


class GenerateExcelStu:
    def __init__(self):
        self.stuobj = KpStudent(ids_run=False)
        self.excel_path = r'D:\PyCharm 2024.1.4\KpProject\QuestionCard\KpRequest\excel'

    @staticmethod
    def generate_school(stu_number, index):
        """
        生成学生学校列数据
        :param stu_number: 总的学生数
        :param index: 第n个学生数
        :return:
        """
        return '胡林辉二校' if index > (stu_number / 2) else '胡林辉一校'

    @staticmethod
    def generate_class(stu_number, class_number, index):
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

    def run(self, name, exam_type=1):
        """
        1、查询考试模式下所有选考标签
        2、根据标签数量及班级数量进行均分
        3、普通模式剔除最后一列（选考标签）
        4、生成数据并保存到excel中
        :param name:考试模式标签（普通和新高考【文理分科、3+1+2新高考、3+3新高考】）
        :param exam_type:普通（False）和新高考（True）
        :return:
        """
        label_list = self.stuobj.get_exam_label(name)
        stu_count, class_count = len(label_list), 3
        class_stu = int(stu_count / 2 / class_count)
        excel_data = {
            '准考证号(必填)': [f'{1300000 + i}' for i in range(1, stu_count + 1)],
            '学校(必填)': [self.generate_school(stu_count, i) for i in range(1, stu_count + 1)],
            '班级(必填)': [self.generate_class(stu_count, class_stu, i) for i in range(1, stu_count + 1)],
            '姓名(必填)': [self.stuobj.faker.name() for _ in range(1, stu_count + 1)],
            '选考标签(必填)': [info[1] for info in label_list]
        }
        if not exam_type: excel_data.popitem()
        df = pd.DataFrame(excel_data)
        df.to_excel(rf'{self.excel_path}\临时考生上报模版.xlsx', index=False)


if __name__ == '__main__':
    GenerateExcelStu().run('3+1+2', 1)
