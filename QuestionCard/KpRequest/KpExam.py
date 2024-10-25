class KpExam:
    def __init__(self, l_object):
        self.login_object = l_object
        self.data = self.login_object.kp_data

    def search_exam(self, orgid):
        exam_url = self.data['exam_url']
        exam_data = {"data": {"examStatus": ["0"], "roleCodes": ["ROLE_ORG_MANAGER", "ROLE_TEACHER"], "orgType": 1,
                              "orgId": orgid, "examName": self.data['exam_name']},
                     "pageSize": 10, "pageNum": 1}
        exam_response = self.login_object.get_response(url=exam_url, method='POST', data=exam_data)
        result, r_data = self.login_object.check_response(exam_response)
        if result:
            data = r_data.get("data")
            exam_id = data and data[0]['examId'] or None
            return exam_id
        else:
            self.login_object.logger.info('获取响应失败!')

    def search_paper(self, exam_id, org_id):
        paper_url = self.data['paper_url']
        paper_data = {"data": {"examId": exam_id, "orgId": org_id,
                               "roleCodes": ["ROLE_ORG_MANAGER", "ROLE_TEACHER"]}}
        paper_response = self.login_object.get_response(url=paper_url, method='POST', data=paper_data)
        result, r_data = self.login_object.check_response(paper_response)
        if result:
            paper_name = self.data['paper_name']
            paper_list = [item['paperId'] for item in r_data.get("data", []) if
                          item['paperName'] == paper_name]
            exam_info = paper_list and {'examId': exam_id, 'paperId': paper_list[0]} or None
            return exam_info
        else:
            self.login_object.logger.info('获取响应失败!')

    def get_exam_info(self, org_id):
        exam_id = self.search_exam(org_id)
        if not exam_id:
            return
        exam_info = self.search_paper(exam_id, org_id)
        return exam_info


if __name__ == '__main__':
    pass
