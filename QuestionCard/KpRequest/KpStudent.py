import random
from datetime import datetime, timedelta
from QuestionCard.KpRequest.KpLogin import KpLogin
from faker import Faker

# 创建一个Faker实例，指定使用中文
fake = Faker("zh-CN")


class KpStudent:
    def __init__(self):
        self.object = KpLogin()
        self.org_id = self.object.get_login_token()

    def get_school_area(self):
        """
        查询当前学校的校区id
        :return: school_areaid
        """
        area_url = self.object.kp_data['area_url']
        area_params = {'orgId': self.org_id}
        area_resp = self.object.get_response(area_url, method='GET', params=area_params)
        result, data = self.object.check_response(area_resp)
        if result:
            school_areaid = data['data'][0]['id']
            return school_areaid
        else:
            self.object.logger.warning('响应数据有误')

    @staticmethod
    def name_cover_code(grade_name):
        """
        获取学阶代码及年级代码
        学阶code：1、小学 2、初中 3、高中
        年级code：1-9（一到9年级）、10-12（高一、高二、高三）
        :param grade_name:
        :return: step_index，grade_index
        """
        cover_func = lambda cn: {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,
                                 '七': 7, '八': 8, '九': 9}.get(cn, 0)
        if len(grade_name) >= 3:
            grade_int = cover_func(grade_name[0])
            if grade_int <= 6:
                step_index = 1
            else:
                step_index = 2
            grade_index = grade_int
        else:
            step_index = 3
            grade_index = 9 + cover_func(grade_name[1])
        return str(step_index), str(grade_index)

    def get_grade(self, grade_name):
        """
        获取年级id、学阶id
        :param grade_name: 年级名称
        :return: (grade_id, step_id)
        """
        step_code, grade_code = self.name_cover_code(grade_name)
        grade_url = self.object.kp_data['grade_url']
        grade_data = {"data": {"orgId": self.org_id, "includeGrades": 'true'}}
        grade_resp = self.object.get_response(grade_url, method='POST', data=grade_data)
        result, data = self.object.check_response(grade_resp)
        if result:
            grade_list = [
                (grade['id'], step_item['id'])
                for step_item in data['data']
                if step_item['code'] == step_code
                for grade in step_item['grades']
                if grade['code'] == grade_code
            ]
            return grade_list[0]
        else:
            self.object.logger.warning('响应数据有误')

    def get_class(self, aid, eid, pid):
        """
        获取班级id
        :param aid: 校区id
        :param eid: 年级id
        :param pid: 学阶id
        :return: class_id 班级id
        """
        class_url = self.object.kp_data['class_url']
        class_data = {"type": "1", "schoolAreaId": aid, "gradeId": eid, "stepId": pid}
        response = self.object.get_response(class_url, method='POST', data=class_data)
        result, data = self.object.check_response(response)
        if result:
            class_list = [class_item['classId'] for class_item in data['data'] if
                          class_item['className'] == self.object.kp_data['class_name']]
            return class_list[0]
        else:
            self.object.logger.warning('响应数据有误')

    def get_student_data(self, school_area_id, class_id=None):
        """
        查询全校学生或查询单个班级学生
        :param school_area_id: 校区id
        :param class_id: 班级id,class_id默认为None，查询全校学生
        :return: 查询班级学生时，返回准考证号列表；查询全校学生时，返回最大的学号和准考证号的元祖，方便后面添加考生
        """
        student_url = self.object.kp_data['stu_url']
        student_data = {"classId": class_id, "schoolAreaId": school_area_id, "schoolId": self.org_id, "pageSize": 9999}
        response = self.object.get_response(student_url, method='POST', data=student_data)
        result, data = self.object.check_response(response)
        if result:
            result_data = data.get("data").get("records")
            stu_zkzh_data = [item['zkzh'] for item in result_data if item.get('zkzh')] if result_data else []
            stu_no_data = [item['studentNo'] for item in result_data if item.get('studentNo')] if result_data else []
            if class_id is not None:
                stu_zkzh_data.sort()
                return stu_zkzh_data
            else:
                return int(max(stu_zkzh_data)), int(max(stu_no_data))
        else:
            self.object.logger.warning('响应数据有误')
            return []

    def get_exam_label(self, label_name):
        """
        根据考试标签（label_name）筛选出对应的选考标签
        :param label_name:考试标签
        :return:label_info_list: 选考标签信息[(id,name)]
        """
        label_url = self.object.kp_data['exam_label_url']
        label_data = {"pageNum": 1, "pageSize": 130}
        label_response = self.object.get_response(label_url, method='POST', data=label_data)
        result, data = self.object.check_response(label_response)
        if result:
            label_list = sorted(data['data']['records'], key=lambda x: int(x['id']))
            label_info_list = [(label_info['id'], label_info['selectExamLabel']) for label_info in label_list if
                               label_name in label_info.get('examLabel')]
            self.object.logger.info(f'考试模式==>{label_name},获取选考标签个数为{len(label_info_list)}')
            return label_info_list
        else:
            self.object.logger.warning('响应数据有误')

    def query_info(self):
        """
        返回校区id、年级id、学阶id、班级id列表数据
        :return:
        """
        school_areaid = self.get_school_area()
        grade_tuple = self.get_grade(self.object.kp_data['grade_name'])
        class_id = self.get_class(school_areaid, *grade_tuple)
        return [school_areaid, *grade_tuple, class_id]

    @staticmethod
    def generate_random_birth_date():
        """
        生成随机学生的出生日期
        :return:格式化年月日
        """
        current_year = datetime.now().year
        birth_year = random.randint(1997, current_year - 8)  # 确保18岁以上
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)  # 为简化起见，假设每月最多28天
        try:
            birth_date = datetime(birth_year, birth_month, birth_day)
        except ValueError:  # 处理非法日期
            birth_date = datetime(birth_year, birth_month, random.randint(1, 28))

        # 再次确认日期的合法性
        while birth_date >= datetime.now():
            birth_date -= timedelta(days=1)

        return birth_date.strftime("%Y-%m-%d")

    def get_batch_info(self, exam_label):
        """
        根据exam_label的数据类型判断执行哪种方式添加学生
        :param exam_label: 选考标签数据[(选考id，选考名称)]
        :return: batch_list:返回创建学生需要得请求data数据
        """
        batch_list = []
        # 查询当前校区年级、班级、校级id
        area_id, grade_id, _, class_id = self.query_info()
        # 查询本校区内最大的准考证号、最大的学号
        max_zkzh, max_no = self.get_student_data(area_id)
        # 添加学生的人数
        student_count = len(exam_label) if isinstance(exam_label, list) else int(exam_label)
        # 学生人数=0时，不执行后续操作，直接退出
        if not student_count: return batch_list
        # 判断按选考还是按自定义，自定义的话无法获取选考标签，显示空字符串
        label_getter = lambda no, label: (label[no][0], label[no][1]) if isinstance(label, list) else ("", "")
        # 添加数据
        for index in range(1, student_count + 1):
            stu_item = {"className": self.object.kp_data['class_name'],
                        "studentName": fake.name(),
                        "studentNo": f"{max_no + index}",
                        "zkzh": f"{max_zkzh + index}",
                        "selectExamLabelName": label_getter(index - 1, exam_label)[1],
                        "studentCode": f"{max_no + index}",
                        "tel": fake.phone_number(),
                        "sex": random.choice(range(1, 4)),
                        "birthday": self.generate_random_birth_date(),
                        "idCardType": f"{random.choice(range(100001, 100013))}",
                        "idCard": fake.ssn(),
                        "index": index,
                        "gradeId": grade_id,
                        "gradeName": self.object.kp_data['grade_name'],
                        "schoolAreaId": area_id,
                        "classId": class_id,
                        "selectExamLabelId": label_getter(index - 1, exam_label)[0]}
            batch_list.append(stu_item)
        return batch_list

    def batch_add_student(self, batch_data):
        """
        创建学生
        :param batch_data: 创建学生请求所需的data
        :return:
        """
        batch_url = self.object.kp_data['batchstu_url']
        label_response = self.object.get_response(batch_url, method='POST', data=batch_data)
        result, data = self.object.check_response(label_response)
        if result:
            fail_info = data['data']
            if not fail_info:
                self.object.logger.info(f'批量添加学生成功！')
            else:
                self.object.logger.warning(f"{fail_info[0]['value']}--{fail_info[0]['message']}")
        else:
            self.object.logger.warning('响应数据有误')

    def add_student(self, label_name=None, stu_num=None):
        """
        两种方式添加学生，
        一种自定义添加，传入stu_num(创建学生人数-字符串)即可；
        一种根据选考标签个数（传入lebel_name）添加学生人数，学生人数=选考标签个数；
        :param label_name: 选考标签的名称（文理分科、3+1+2、3+3）
        :param stu_num: 学生人数
        :return:
        """
        if label_name is not None:
            # 获取选考标签信息（ID、标签名称）列表套元祖
            label_info_list = self.get_exam_label(label_name)
            stu_num = label_info_list if label_info_list else []
        # 生成批量创建学生的data数据
        batch_data = self.get_batch_info(stu_num)
        # 创建学生
        self.batch_add_student(batch_data)

    def query_student(self):
        area_id, *_, class_id = self.query_info()
        if not (self.org_id and area_id and class_id):
            self.object.logger.warning('必要参数获取失败！')
            return
        data = self.get_student_data(area_id, class_id)
        return data


if __name__ == '__main__':
    stu_obj = KpStudent()
    stu_obj.add_student(label_name=None, stu_num='2')
    # print(stu_obj.query_student())
