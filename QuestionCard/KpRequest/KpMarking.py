class KpMarking:
    def __init__(self, l_object):
        self.login_object = l_object
        self.data = self.login_object.kp_data

    def query_task_exam(self, orgid, orgtype, userid):
        examtask_url = self.data['examtask_url']
        examTask_data = {"data": {"userId": userid, "orgType": orgtype, "orgId": orgid,
                                  "roleCodes": ["ROLE_ORG_MANAGER", "ROLE_CLASS_TEACHER", "ROLE_TEACHER"],
                                  "examName": self.data['exam_name']}, "pageSize": 5, "pageNum": 1}
        examTask_response = self.login_object.get_response(url=examtask_url, method='POST', data=examTask_data)
        result, r_data = self.login_object.check_response(examTask_response)
        if result:
            data = r_data.get("data")
            exam_id = data and data[0]['examId'] or None
            return exam_id
        else:
            self.login_object.logger.info('获取响应失败!')

    def query_task_paper(self):
        pass

    def get_normal_task(self):
        pass

    def run(self):
        login_info = self.login_object.get_login_token(keys=['orgType', 'userId'])
        exam_id = self.query_task_exam(*login_info)
        print(exam_id)


if __name__ == '__main__':
    from KpLogin import KpLogin

    kp_login = KpLogin()
    km = KpMarking(kp_login)
    km.run()
