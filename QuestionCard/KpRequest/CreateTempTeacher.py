"""
作者: hulinhui6
日期：2025年04月15日
"""
from QuestionCard.KpRequest.KpLogin import KpLogin
from QuestionCard.KpRequest.KpStudent import KpStudent


class GenerateExcelTeacher:
    def __init__(self):
        self._stuobj = KpStudent(KpLogin(), ids_run=False)
        self._examobj = None
        self._EXCEL_PATH = r'D:\PyCharm 2024.1.4\KpProject\QuestionCard\KpRequest\excel'

    @property
    def examobj(self):
        """调用考试模块对象"""
        if not self._examobj:
            from QuestionCard.KpRequest.KpExam import KpExam
            self._examobj = KpExam(self._stuobj.object)
        return self._examobj

    def is_education_office(self):
        """判断是否为教育局"""
        return self._stuobj.other[1] == 1

    def get_organization_data(self):
        """获取学校列表orgid"""
        if self.is_education_office():
            return self._stuobj.get_edu_school()
        return [self._stuobj.org_id]

    def fetch_organization_list(self):
        """获取机构信息"""
        return self.get_organization_data()

    def fetch_teacher_data(self, org_list):
        """获取老师数据"""
        teacher_list = self._stuobj.query_tealeaders(org_list)
        if self.is_education_office():
            edu_teachers = self._stuobj.query_tealeaders(self._stuobj.org_id)
            edu_teachers.extend(teacher_list)
            teacher_list = edu_teachers
        return teacher_list

    def fetch_subject_data(self):
        """
        调用查询考试id及查询科目信息接口，查询数据
        查询配置文件中考试对应的所有科目数据，并返回所有科目名称组成的列表
        :return: 科目名称组成的列表
        """
        exam_id = self.examobj.search_exam(self._stuobj.org_id, self._stuobj.other)
        if exam_id is None: return []
        exam_data = self.examobj.exam_detail(exam_id)
        if not exam_data: return []
        return [_['paperName'] for _ in exam_data['papers'] if not _['inputRecord']]

    def generate_excel_file(self, teachers, subjects):
        """
        生成excel文件
        :param teachers: 阅卷教师数据
        :param subjects: 考试科目数据
        :return:
        """
        import pandas as pd
        import random
        data = {
            '学校(必填)': [t[0] for t in teachers],
            '科目(必填)': [random.choice(subjects) if subjects else '语文' for _ in teachers],
            '教师姓名(必填)': [t[1] for t in teachers],
            '手机号码(必填)': [t[2] for t in teachers]
        }
        df = pd.DataFrame(data)
        file_path = f'{self._EXCEL_PATH}/阅卷教师上报模版.xlsx'
        df.to_excel(file_path, index=False)

    def run(self):
        """
        1、查询登录用户的机构id
        2、查询当前机构下所有教师用户信息（学校只查本校，教育局查教育局及学校数据）
        3、查询考试所有的科目数据
        4、生成数据并保存到excel中
        :return:
        """
        org_list = self.fetch_organization_list()
        teacher_data = self.fetch_teacher_data(org_list)
        subject_data = self.fetch_subject_data()
        if not teacher_data: return
        self.generate_excel_file(teacher_data, subject_data)


if __name__ == '__main__':
    GenerateExcelTeacher().run()
