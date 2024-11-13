import pandas as pd
import math
from QuestionCard.KpRequest.KpStudent import KpStudent


class GenerateExcel:
    def __init__(self):
        self.stuobj = KpStudent(ids_run=False)
        self.excel_path = r'D:\PyCharm 2024.1.4\KpProject\QuestionCard\KpRequest\excel'

    @staticmethod
    def generate_school(stu_number, index):
        return '胡林辉二校' if index > (stu_number / 2) else '胡林辉一校'

    @staticmethod
    def generate_class(stu_number, class_number, index):
        if index > (stu_number / 2):
            return f'{math.ceil((index - (stu_number / 2)) / class_number):02d}班'
        else:
            return f'{math.ceil(index / class_number):02d}班'

    def run(self, name, exam_type=1):
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
        if exam_type is None: excel_data.popitem()
        df = pd.DataFrame(excel_data)
        df.to_excel(rf'{self.excel_path}\临时考生导入模版.xlsx', index=False)


if __name__ == '__main__':
    GenerateExcel().run('3+1+2', 1)
