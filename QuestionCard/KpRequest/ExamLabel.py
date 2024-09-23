from StudentZkzhData import StudentZkzhData


class ExamLabel:
    def __init__(self):
        self.object = StudentZkzhData()
        self.org_id = self.object.get_login_token()

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
        batch_list = []
        for index, label_info in enumerate(exam_label, 1):
            label_item = {"className": "06班", "studentName": f"{name}生{index}", "studentNo": f"{100200 + index}",
                          "zkzh": f"{42000200 + index}",
                          "selectExamLabelName": label_info[1], "index": index, "gradeId": "172154942111739800011",
                          "gradeName": "高一", "schoolAreaId": "237172283877937703507",
                          "classId": "052172708159204000672", "selectExamLabelId": label_info[0]}
            batch_list.append(label_item)
        return batch_list

    def create_exam_student(self, name):
        batch_url = self.object.kp_data['batchstu_url']
        batch_data = self.get_batch_info(name)
        label_response = self.object.get_response(batch_url, method='POST', data=batch_data)
        result, data = self.object.check_response(label_response)
        if result:
            self.object.logger.info(f'{name}==>批量添加学生成功！')
        else:
            self.object.logger.info('响应数据有误')


if __name__ == '__main__':
    el = ExamLabel()
    el.create_exam_student('3+1+2')
