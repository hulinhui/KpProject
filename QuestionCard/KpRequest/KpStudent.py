from QuestionCard.KpRequest.KpLogin import KpLogin


class KpStudent:
    def __init__(self):
        self.object = KpLogin()
        self.org_id = self.object.get_login_token()

    def get_school_area(self):
        area_url = self.object.kp_data['area_url']
        area_params = {'orgId': self.org_id}
        area_resp = self.object.get_response(area_url, method='GET', params=area_params)
        result, data = self.object.check_response(area_resp)
        if result:
            school_areaid = data['data'][0]['id']
            return school_areaid
        else:
            self.object.logger.info('响应数据有误')

    @staticmethod
    def name_cover_code(grade_name):
        cover_func = lambda cn: {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,
                                 '七': 7, '八': 8, '九': 9}.get(cn, 0)
        if len(grade_name) >= 3:
            grade_int = cover_func(grade_name[0])
            if grade_int < 6:
                step_index = 1
            else:
                step_index = 2
            grade_index = grade_int
        else:
            step_index = 3
            grade_index = 9 + cover_func(grade_name[1])
        return str(step_index), str(grade_index)

    def get_grade(self, grade_name):
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
            self.object.logger.info('响应数据有误')

    def get_class(self, aid, eid, pid):
        class_url = self.object.kp_data['class_url']
        class_data = {"type": "1", "schoolAreaId": aid, "gradeId": eid, "stepId": pid}
        response = self.object.get_response(class_url, method='POST', data=class_data)
        result, data = self.object.check_response(response)
        if result:
            class_list = [class_item['classId'] for class_item in data['data'] if
                          class_item['className'] == self.object.kp_data['class_name']]
            return class_list[0]
        else:
            self.object.logger.info('响应数据有误')

    def query_info(self):
        school_areaid = self.get_school_area()
        grade_tuple = self.get_grade(self.object.kp_data['grade_name'])
        class_id = self.get_class(school_areaid, *grade_tuple)
        return [school_areaid, *grade_tuple, class_id]

    def get_student_data(self, school_area_id, class_id):
        student_url = self.object.kp_data['stu_url']
        student_data = {"classId": class_id, "schoolAreaId": school_area_id, "schoolId": self.org_id, "pageSize": 100}
        response = self.object.get_response(student_url, method='POST', data=student_data)
        result, data = self.object.check_response(response)
        if result:
            result_data = data.get("data").get("records")
            stu_zkzh_data = [item.get('zkzh') for item in result_data] if result_data else []
            stu_zkzh_data.sort()
            return stu_zkzh_data
        else:
            self.object.logger.info('响应数据有误')
            return []

    def get_exam_label(self):
        label_url = self.object.kp_data['exam_label_url']
        label_data = {"pageNum": 1, "pageSize": 130}
        label_response = self.object.get_response(label_url, method='POST', data=label_data)
        result, data = self.object.check_response(label_response)
        if result:
            label_count = data['data']['total']
            label_list = sorted(data['data']['records'], key=lambda x: int(x['id']))
            self.object.logger.info(f'一共查询选考标签数量为{label_count}个')
            return label_list
        else:
            self.object.logger.info('响应数据有误')

    def query_exam_label(self, label_name):
        label_list = self.get_exam_label()
        if not label_list:
            return
        exam_label = [(label_info['id'], label_info['selectExamLabel']) for label_info in label_list if
                      label_name in label_info.get('examLabel')]
        self.object.logger.info(f'考试模式==>{label_name},获取选考标签个数为{len(exam_label)}')
        return exam_label

    def get_batch_info(self, name):
        exam_label = self.query_exam_label(name)
        area_id, grade_id, _, class_id = self.query_info()
        batch_list = []
        for index, label_info in enumerate(exam_label, 1):
            label_item = {"className": self.object.kp_data['class_name'],
                          "studentName": f"{name}生{index}",
                          "studentNo": f"{100000 + index}",
                          "zkzh": f"{42000000 + index}",
                          "selectExamLabelName": label_info[1], "index": index,
                          "gradeId": grade_id,
                          "gradeName": self.object.kp_data['grade_name'], "schoolAreaId": area_id,
                          "classId": class_id, "selectExamLabelId": label_info[0]}
            batch_list.append(label_item)
        return batch_list

    def create_student(self, name):
        batch_url = self.object.kp_data['batchstu_url']
        batch_data = self.get_batch_info(name)
        label_response = self.object.get_response(batch_url, method='POST', data=batch_data)
        result, data = self.object.check_response(label_response)
        print(data)
        if result:
            self.object.logger.info(f'{name}==>批量添加学生成功！')
        else:
            self.object.logger.info('响应数据有误')

    def query_student(self):
        area_id, *_, class_id = self.query_info()
        if not (self.org_id and area_id and class_id):
            self.object.logger.info('必要参数获取失败！')
            return
        data = self.get_student_data(area_id, class_id)
        return data


if __name__ == '__main__':
    stu_obj = KpStudent()
    #stu_obj.create_student('文理分科')
    print(stu_obj.query_student())
