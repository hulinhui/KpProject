class KpMarking:
    def __init__(self, l_object):
        self.login_object = l_object
        self.data = self.login_object.kp_data

    def query_task_exam(self, orgid, orgtype, userid):
        eTask_url = self.data['examtask_url']
        eTask_data = {"data": {"userId": userid, "orgType": orgtype, "orgId": orgid,
                               "roleCodes": ["ROLE_ORG_MANAGER", "ROLE_CLASS_TEACHER", "ROLE_TEACHER"],
                               "examName": self.data['exam_name']}, "pageSize": 5, "pageNum": 1}
        eTask_response = self.login_object.get_response(url=eTask_url, method='POST', data=eTask_data)
        result, r_data = self.login_object.check_response(eTask_response)
        if result:
            data = r_data.get("data")
            exam_id = data and data[0]['examId'] or None
            return exam_id
        else:
            self.login_object.logger.info('获取响应失败!')

    def query_task_paper(self, exam_id):
        pTask_url = self.data['papertask_url']
        pTask_data = {"examId": exam_id}
        pTask_response = self.login_object.get_response(url=pTask_url, method='POST', data=pTask_data)
        result, r_data = self.login_object.check_response(pTask_response)
        if result:
            data = r_data.get("data")
            return data
        else:
            self.login_object.logger.info('获取响应失败!')

    def get_normal_task(self):
        pass

    def run(self):
        login_info = self.login_object.get_login_token(keys=['orgType', 'userId'])
        exam_id = self.query_task_exam(*login_info)
        data = self.query_task_paper(exam_id)
        print(data)


if __name__ == '__main__':
    from KpLogin import KpLogin

    kp_login = KpLogin()
    km = KpMarking(kp_login)
    km.run()
