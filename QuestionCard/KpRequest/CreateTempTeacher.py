"""
作者: hulinhui6
日期：2025年04月15日
"""
import pandas as pd
import random
from QuestionCard.KpRequest.KpLogin import KpLogin
from QuestionCard.KpRequest.KpStudent import KpStudent


class GenerateExcelTeacher:
    def __init__(self):
        self.stuobj = KpStudent(KpLogin(), ids_run=False)
        self.excel_path = r'D:\PyCharm 2024.1.4\KpProject\QuestionCard\KpRequest\excel'

    def stu_org_data(self):
        """
        根据登录账号的学校类型（教育局或学校）返回机构id组成的列表（教育局及教育局下的学校id，学校则返回学校id）
        :return:
        """
        org_is_edu = self.stuobj.org_type == 1
        school_list = self.stuobj.get_edu_school() if org_is_edu else [self.stuobj.org_id]
        org_data = [self.stuobj.org_id] + school_list if org_is_edu else school_list
        return org_data

    def exam_subject_data(self):
        """
        导入kpexam文件中的kpexam类，调用查询考试id及查询科目信息接口，查询数据
        查询配置文件中考试对应的所有科目数据，并返回所有科目名称组成的列表
        :return: 科目名称组成的列表
        """
        from QuestionCard.KpRequest.KpExam import KpExam
        examobj = KpExam(self.stuobj.object)
        exam_id = examobj.search_exam(self.stuobj.org_id)
        if exam_id is None: return []
        exam_data = examobj.exam_detail(exam_id)
        if not exam_data: return []
        paper_names = [_['paperName'] for _ in exam_data['papers'] if not _['inputRecord']]
        return paper_names

    def run(self):
        """
        1、查询登录用户的机构id
        2、查询当前机构下所有教师用户信息（学校只查本校，教育局查教育局及学校数据）
        3、查询考试所有的科目数据
        4、生成数据并保存到excel中
        :return:
        """
        org_list = self.stu_org_data()
        tea_list = self.stuobj.query_tealeaders(org_list)
        paper_names = self.exam_subject_data()
        excel_data = {
            '学校(必填)': [tea_tup[0] for tea_tup in tea_list],
            '科目(必填)': [random.choice(paper_names) for _ in tea_list],
            '教师姓名(必填)': [tea_tup[1] for tea_tup in tea_list],
            '手机号码(必填)': [tea_tup[2] for tea_tup in tea_list]
        }
        df = pd.DataFrame(excel_data)
        df.to_excel(f'{self.excel_path}/阅卷教师上报模版.xlsx', index=False)


if __name__ == '__main__':
    GenerateExcelTeacher().run()
