import random


class KpStudent:
    def __init__(self, login_object, ids_run=True):
        self.object = login_object
        self.org_info = self.object.get_login_token(keys=['userId', 'orgType', 'roleList'])
        self.org_id, *_ = self.org_info
        self.ids_info = self.query_class_info() if ids_run else None

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
        :param grade_name: 年级名称（如：一年级、高一）
        :return: (学阶代码, 年级代码)
                学阶代码：1-小学, 2-初中, 3-高中
                年级代码：1-9（一到九年级）, 10-12（高一到高三）
        """
        num_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                   '六': 6, '七': 7, '八': 8, '九': 9}

        if len(grade_name) < 3:  # 高中年级
            return '3', str(9 + num_map.get(grade_name[1], 0))

        grade_num = num_map.get(grade_name[0], 0)
        return '1' if grade_num <= 6 else '2', str(grade_num)

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
        name_list = self.object.kp_data['class_name'].split(',')
        class_data = {"type": "1", "schoolAreaId": aid, "gradeId": eid, "stepId": pid}
        response = self.object.get_response(class_url, method='POST', data=class_data)
        result, data = self.object.check_response(response)
        if result:
            class_list = [class_item['classId'] for class_item in data['data'] if
                          class_item['className'] in name_list]
            return class_list
        else:
            self.object.logger.warning('响应数据有误')

    def get_edu_school(self):
        name_list = self.object.kp_data['school_name'].split(',')
        school_url = self.object.kp_data['school_url']
        school_params = {'eduId': self.org_id}
        school_resp = self.object.get_response(school_url, method='GET', params=school_params)
        result, data = self.object.check_response(school_resp)
        if result:
            school_list = [school_item['orgId'] for school_item in data['data'] if school_item['orgName'] in name_list]
            return school_list
        else:
            self.object.logger.warning('响应数据有误')

    def query_tealeaders(self, org_data):
        """
        查询题组长用户数据，包含所有用户（教育局包含所有单校用户，学校包含本校所有用户）
        :return:
        """
        org_data, orgId = (org_data, '') if isinstance(org_data, list) else ([], org_data)
        leaders_url = self.object.kp_data['leaders_url']
        leaders_data = {'data': {'examId': '1', 'paperId': '2', 'itemId': '3',
                                 'queryConditions': {'orgList': org_data, 'orgId': orgId, 'mobile': ''}},
                        'pageSize': 999, 'pageNum': 1}
        divleaders_response = self.object.get_response(url=leaders_url, method='POST', data=leaders_data)
        result, r_data = self.object.check_response(divleaders_response)
        if result:
            tea_data = [(_['orgName'], _['teacherName'], _['mobile']) for _ in r_data['data'] if _['orgName']]
            return tea_data
        else:
            self.object.logger.info('获取响应失败!')

    def query_class_info(self):
        """
        返回校区id、年级id、学阶id、班级id列表数据
        :return:
        """
        school_areaid = self.get_school_area() if self.other[1] == 2 else self.get_edu_school()
        grade_tuple = self.get_grade(self.object.kp_data['grade_name'])
        class_ids = self.get_class(school_areaid, *grade_tuple) if self.other[1] == 2 else None
        return [school_areaid, *grade_tuple, class_ids]

    def query_student(self, area_id, class_id=None):
        """
        查询全校学生或查询单个班级学生
        :param area_id:   校区id
        :param class_id: 班级id,class_id默认为None，查询全校学生
        :return: 查询班级学生时，返回准考证号列表；查询全校学生时，返回最大的学号和准考证号的元祖，方便后面添加考生
        """
        student_url = self.object.kp_data['stu_url']
        student_data = {"classId": class_id, "schoolAreaId": area_id, "schoolId": self.org_id,
                        "pageSize": 9999}
        response = self.object.get_response(student_url, method='POST', data=student_data)
        result, data = self.object.check_response(response)
        if result:
            result_data = data.get("data").get("records")
            return result_data
        else:
            self.object.logger.warning('响应数据有误')
            return []

    def query_edu_student(self, school_id, grade_id):
        edu_stu_url = self.object.kp_data['edu_stu_url']
        edu_stu_data = {"schoolId": school_id, "gradeId": grade_id, "eduId": self.org_id, "pageSize": 999}
        name_list = self.object.kp_data['class_name'].split(',')
        stu_response = self.object.get_response(edu_stu_url, method='POST', data=edu_stu_data)
        result, data = self.object.check_response(stu_response)
        if result:
            record_list = data.get("data").get("records")
            return [item for item in record_list if item['baseClassName'] in name_list]
        else:
            self.object.logger.warning('响应数据有误')

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

    def delete_student(self, student_ids):
        """
        删除学生
        :param student_ids:
        :return:
        """
        delete_url = self.object.kp_data['del_stu_url']
        area_id, *_, class_ids = self.ids_info
        delete_data = {"schoolAreaId": area_id, "classId": class_ids[0], "studentIds": student_ids}
        delete_response = self.object.get_response(delete_url, method='POST', data=delete_data)
        result, data = self.object.check_response(delete_response)
        if result:
            self.object.logger.info('删除成功！')
        else:
            self.object.logger.warning(f"{data['message']}")

    def get_max_code(self):
        """
        获取全校内最大的学生准考证号及学号
        :return: 最大的准考证号及最大的学号
        """
        result_data = self.get_student_data(all_flag=True)
        stu_no_data = [item['studentNo'] for item in result_data if item.get('studentNo')] if result_data else []
        stu_zkzh_data = [item['zkzh'] for item in result_data if item.get('zkzh')] if result_data else []
        max_zkzh, max_no = max(stu_zkzh_data) if stu_zkzh_data else 0, max(stu_no_data) if stu_no_data else 0
        return int(max_zkzh), int(max_no)

    def get_batch_info(self, exam_label):
        """
        根据exam_label的数据类型判断执行哪种方式添加学生
        :param exam_label: 选考标签数据[(选考id，选考名称)]
        :return: batch_list:返回创建学生需要得请求data数据
        """
        from faker import Faker
        faker, batch_list = Faker("zh-CN"), []
        # 查询当前校区年级、班级、校级id
        area_id, grade_id, _, class_ids = self.ids_info
        # 查询本校区内最大的准考证号、最大的学号
        max_zkzh, max_no = self.get_max_code()
        # 添加学生的人数
        student_count = len(exam_label) if isinstance(exam_label, list) else int(exam_label)
        # 学生人数=0时，不执行后续操作，直接退出
        if not (student_count and max_zkzh and max_no): return batch_list
        # 判断按选考还是按自定义，自定义的话无法获取选考标签，显示空字符串
        label_getter = lambda no, label: (label[no][0], label[no][1]) if isinstance(label, list) else ("", "")
        # 初始化测试数据，添加数据
        for index in range(1, student_count + 1):
            stu_item = {
                "studentName": faker.name(),
                "studentNo": f"{max_no + index}",
                "zkzh": f"{max_zkzh + index}",
                "selectExamLabelName": label_getter(index - 1, exam_label)[1],
                "studentCode": f"{max_no + index}",
                "tel": faker.phone_number(),
                "sex": random.choice(range(1, 4)),
                "idCardType": f"{random.choice(range(100001, 100013))}",
                "idCard": faker.ssn(),
                "index": index,
                "gradeId": grade_id,
                "gradeName": self.object.kp_data['grade_name'],
                "schoolAreaId": area_id,
                "classId": class_ids[0],
                "selectExamLabelId": label_getter(index - 1, exam_label)[0]}
            batch_list.append(stu_item)
        return batch_list

    def add_student(self, batch_data):
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

    def get_student_data(self, all_flag=False):
        """
        查询本校区学生数据
        :param all_flag: 查询全校学生
        :return:
        """
        school_ids, grade_id, _, class_ids = self.ids_info
        if not (self.org_id and school_ids and grade_id):
            self.object.logger.warning('必要参数获取失败！')
            return []
        result_data = ([item for school_id in school_ids for item in self.query_edu_student(school_id, grade_id)]
                       if isinstance(school_ids, list) else self.query_student(school_ids, None)
        if all_flag else [item for class_id in class_ids for item in self.query_student(school_ids, class_id)])
        return result_data

    def add_class_student(self, label_name=None, stu_num=None):
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
        self.add_student(batch_data)

    def query_class_student_no(self, numType):
        """
        查询班级学生编号（准考证号/学号/账号后8位）
        :param numType: 0:准考证号, 1:学号, 2:账号后8位
        :return: 排序后的编号列表
        """
        if not (res_data := self.get_student_data()):
            return []
        key_map = {
            0: ('zkzh', lambda x: x),
            1: ('studentNo', lambda x: x),
            2: ('studentAccount', lambda x: x[-8:])
        }
        key, transform = key_map.get(numType, ('', lambda x: x))
        return sorted(transform(item[key]) for item in res_data if item.get(key))

    def delete_class_student(self, student_name=None):
        """
        查询班级学生，找到对应学生，执行删除
        :param student_name: 默认为None，删除全班学生，传入学生名称，删除单个学生
        :return: None
        """
        result_data = self.get_student_data()
        student_ids = [item['studentId'] for item in result_data if
                       item.get('studentName') == student_name or student_name is None] if result_data else []
        if student_ids:
            self.delete_student(student_ids)
        else:
            self.object.logger.warning(f'本班级未找到学生：{student_name}')


if __name__ == '__main__':
    from QuestionCard.KpRequest.KpLogin import KpLogin

    login = KpLogin()

    stu_obj = KpStudent(login)
    # stu_obj.delete_class_student()
    # aa = stu_obj.query_class_student_no(numType=0)
    # print(aa, len(aa))
    # aa = stu_obj.get_max_code()
    # print(aa)
    stu_obj.add_class_student(label_name='文理分科')
    # print(stu_obj.get_max_code())
    # stu_obj.delete_class_student()
