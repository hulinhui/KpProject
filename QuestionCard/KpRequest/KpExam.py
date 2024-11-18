class KpExam:
    def __init__(self, l_object):
        self.login_object = l_object
        self.data = self.login_object.kp_data

    def search_exam(self, orgid):
        """
        进行中考试列表查询考试id
        :param orgid: 机构id
        :return: str 考试id
        """
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
        """
        查询科目对应paper信息
        :param exam_id: 考试id
        :param org_id: 机构id
        :return: 包含考试exam及科目paper的字典
        """
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

    def exam_detail(self, exam_id):
        """
        获取考试详情信息
        :param exam_id: 考试id
        :return: 考试详细信息字典
        """
        detail_url = self.data['exam_detail_url']
        detail_params = {'examId': exam_id, 'findType': 2, 'findState': 0}
        detail_response = self.login_object.get_response(url=detail_url, method='GET', params=detail_params)
        result, r_data = self.login_object.check_response(detail_response)
        if result:
            grade_id = r_data['data']['gradeId']
            exam_type = r_data['data']['examModel'] or None
            school_ids = ','.join([item['schoolId'] for item in r_data['data']['papers'][0]['schoolList']])
            return {'examId': exam_id, 'gradeId': grade_id, 'schoolIds': school_ids, 'modelType': exam_type}
        else:
            self.login_object.logger.info('获取响应失败!')

    def exam_remark(self, remark_data):
        """
        全卷重评
        :param remark_data: 考试id及paperid的字典
        :return:
        """
        remark_url = self.data['remark_url']
        remark_response = self.login_object.get_response(url=remark_url, method='POST', data=remark_data)
        result, r_data = self.login_object.check_response(remark_response)
        if result:
            self.login_object.logger.info('全卷重评成功！')
        else:
            self.login_object.logger.info('获取响应失败!')

    def exam_marking(self, marking_data, valid):
        """
        全卷暂停或全卷恢复
        :param marking_data: 考试id及paperid的字典
        :param valid: 状态，1-恢复，9-暂停
        :return:
        """
        marking_url = self.data['marking_url']
        marking_data.update({'valid': valid})
        remark_response = self.login_object.get_response(url=marking_url, method='POST', data=marking_data)
        result, r_data = self.login_object.check_response(remark_response)
        if result:
            status = '暂停' if valid == 9 else '恢复'
            self.login_object.logger.info(f'全卷{status}成功！')
        else:
            self.login_object.logger.info('获取响应失败!')

    def get_exam_info(self, org_id):
        exam_id = self.search_exam(org_id)
        if exam_id:
            exam_info = self.search_paper(exam_id, org_id)
            return exam_info
        else:
            return None

    def run(self):
        org_id = self.login_object.get_login_token()
        exam_info = self.get_exam_info(org_id)
        if exam_info is not None:
            # 全卷恢复或暂停
            self.exam_marking(exam_info, 1)
            # 全卷重评
            self.exam_remark(exam_info)
        else:
            self.login_object.logger.info('考试信息数据获取有误!')


if __name__ == '__main__':
    from KpLogin import KpLogin

    kp_login = KpLogin()
    ke = KpExam(kp_login)
    ke.run()
