import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential
from KpCreateExam import KpCreateExam
from NotifyMessage import config_reminder_decorator


class KpExam:
    def __init__(self, l_object):
        self.login_object = l_object
        self.data = self.login_object.kp_data
        self.logger = self.login_object.logger

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
            self.logger.info('获取响应失败!')

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
            self.logger.info('获取响应失败!')

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
            self.logger.info('获取响应失败!')

    def exam_remark(self, remark_data):
        """
        全卷重评
        :param remark_data: 考试id及paperid的字典
        :return: None
        """
        remark_url = self.data['remark_url']
        authcode = KpCreateExam(self.login_object).generate_authcode(remark_data.get('paperId'), '3')
        remark_data.update({'authcode': authcode})
        print(remark_data)
        remark_response = self.login_object.get_response(url=remark_url, method='POST', data=remark_data)
        result, r_data = self.login_object.check_response(remark_response)
        if result:
            self.logger.info('全卷重评成功！')
        else:
            self.logger.info('获取响应失败!')

    def exam_questionlist(self, exam_info, que_name):
        question_url = self.data['quegroup_url']
        question_params = {'paperId': exam_info.get('paperId')}
        question_response = self.login_object.get_response(url=question_url, method='GET', params=question_params)
        result, r_data = self.login_object.check_response(question_response)
        if result and r_data and 'data' in r_data:
            divIds = [item.get('id') for item in r_data['data'] if item.get('questionGroupAlias') == que_name]
            divId = divIds[0] if divIds else None
            return divId
        else:
            self.logger.info('获取响应失败!')

    def exam_divremark(self, exam_info, div_id):
        divremark_url = self.data['divremark_url']
        authcode = KpCreateExam(self.login_object).generate_authcode(div_id, '2')
        divremark_data = {'paperId': exam_info.get('paperId'), 'divId': div_id, 'authCode': authcode}
        divremark_response = self.login_object.get_response(url=divremark_url, method='POST', data=divremark_data)
        result, r_data = self.login_object.check_response(divremark_response)
        if result:
            self.logger.info(f'题组id【{div_id}】重评成功！')
        else:
            self.logger.info('获取响应失败!')

    def exam_marking(self, marking_data, valid):
        """
        全卷暂停或全卷恢复
        :param marking_data: 考试id及paperid的字典
        :param valid: 状态，1-恢复，9-暂停
        :return: None
        """
        marking_url = self.data['marking_url']
        marking_data.update({'valid': valid})
        remark_response = self.login_object.get_response(url=marking_url, method='POST', data=marking_data)
        result, r_data = self.login_object.check_response(remark_response)
        if result:
            status = '暂停' if valid == 9 else '恢复'
            self.logger.info(f'全卷{status}成功！')
        else:
            self.logger.info('获取响应失败!')

    def get_allocation_type(self, exam_info):
        """
        获取分配方式
        :param exam_info: 包含examId和paperId的字典信息
        :return: str 分配方式类型
        """
        Pinfo_url = self.data['paperinfo_url']
        Pinfo_params = {'paperId': exam_info.get('paperId')}
        Pinfo_response = self.login_object.get_response(url=Pinfo_url, method='GET', params=Pinfo_params)
        result, r_data = self.login_object.check_response(Pinfo_response)
        if result:
            d_data = r_data['data']
            alloc_type = f"{d_data['markEngineType']}{d_data['allotType']}" if d_data['markEngineType'] == 1 \
                else str(d_data['markEngineType'])
            return alloc_type
        else:
            self.logger.info('获取响应失败!')

    def get_task_allocation_info(self, exam_info):
        """
        获取主观题题组id及题组名称
        :param exam_info: 包含examId和paperId的字典信息
        :return: list  所有题组的id信息的字典
        """
        Dinfo_url = self.data['divinfo_url']
        Dinfo_response = self.login_object.get_response(url=Dinfo_url, method='GET', params=exam_info)
        result, r_data = self.login_object.check_response(Dinfo_response)
        if result:
            div_items = [{**exam_info, 'divId': item['id'], 'divName': item['divName']} for item in
                         r_data['data']['divList']]
            return div_items
        else:
            self.logger.info('获取响应失败!')

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_question_allocation(self, d_item):
        """
        获取单题组任务量（阅卷学校及阅卷老师信息）
        :param d_item: 包含examId和paperId和divId的字典信息
        :return: item  当前题组任务量字典
        """
        allot_url = self.data['allotlist_url'].format(d_item['paperId'], d_item['divId'])
        allot_response = self.login_object.get_response(url=allot_url, method='POST')
        result, r_data = self.login_object.check_response(allot_response)
        if result:
            return next(item for item in r_data['data'] if item['divId'] == d_item['divId'])
        error_code = r_data.get('errorCode')
        if error_code == '-1':
            raise Exception(r_data['errorMsg'])
        self.logger.info('获取响应失败!')

    def get_question_allocation_wrapper(self, d_item):
        """重试包装器"""
        try:
            return self.get_question_allocation(d_item)
        except tenacity.RetryError as e:
            self.logger.error(f"获取响应失败，所有重试均已耗尽: {e}")
            return None

    @staticmethod
    def get_allot_nums(alloc_type, da_item):
        """
        获取学校分配任务量及阅卷老师id（全体任务or按学校比例分）
        :param alloc_type: 分配类型
        :param da_item: 题组任务量数据
        :return: list 根据分配类型返回对应的所需数据
        """
        da_sum, schools = da_item.get('totalTaskNum', 0), da_item.get('schoolTeaAllot', [])
        if alloc_type in {'3', '6', '11'}:
            # 按学校比例模式(仅评本校、按学校-定量、按老师-定量-学校比例)
            return [(s['totalTaskNum'], [t['teacherId'] for t in s['teaAllots']]) for s in schools]
        else:
            # 按全体任务(单校-定量分配、按老师-定量-全体)
            return [(da_sum, [t['teacherId'] for s in schools for t in s['teaAllots']])]

    @staticmethod
    def average_distribution(remain_num, t_num):
        """
        平均分配数量
        :param remain_num: 待分配量
        :param t_num: 老师数量
        :return: list 每个老师对应的量列表
        """
        if t_num <= 0: return []
        remainder = remain_num % t_num
        base = (remain_num - remainder) // t_num
        result = [base + 1 if i < remainder else base for i in range(t_num)]
        return result

    def div_allocate_tasks(self, alloc_type, allot_item, average_flag=True):
        """
        平均分配任务
        :param alloc_type: 分配类型
        :param allot_item: 题组任务量数据
        :param average_flag:是否进行平均操作。默认为 True，表示平均，否则置为0。
        :return: list 生成分配任务接口的传参
        """
        remain_tea_list = self.get_allot_nums(alloc_type, allot_item)
        avger_numbers = [num for r, t in remain_tea_list for num in self.average_distribution(r, len(t))]
        task_numbers = avger_numbers if average_flag else [0] * len(avger_numbers)
        teachers_info = [teacher for _, teachers in remain_tea_list for teacher in teachers]
        allotList = [{'number': num, 'teacherId': info} for info, num in zip(teachers_info, task_numbers)]
        return allotList

    def execute_task_allocation(self, div_name, div_item, allot_list):
        """
        运行分配任务
        :param div_name: 题组名称
        :param div_item: 包含examId和paperId和divId的字典信息
        :param allot_list: 多个老师分配任务的组成的字典列表
        :return: None
        """
        Atask_url = self.data['allottask_url']
        Atask_data = div_item | {'allotList': allot_list}
        Atask_response = self.login_object.get_response(url=Atask_url, method='POST', data=Atask_data)
        result, r_data = self.login_object.check_response(Atask_response)
        if result:
            success_flag = r_data.get('data')
            message_info = f'第{div_name}题分配任务成功!' if success_flag else r_data['errorMsg']
            self.logger.info(message_info)
        else:
            self.logger.info('获取响应失败!')

    def average_allocate_all_questions(self, exam_info):
        """
        平均分配所有题
        :param exam_info: 包含examId和paperId的字典信息
        :return: None
        """
        alloc_type = self.get_allocation_type(exam_info)
        if alloc_type in ['0', '2']:
            self.logger.info('效率优先或分班阅卷无需分配任务')
            return
        div_items = self.get_task_allocation_info(exam_info)
        for div_item in div_items:
            div_name = div_item.pop('divName')
            div_allot_item = self.get_question_allocation_wrapper(div_item)
            div_allotList = self.div_allocate_tasks(alloc_type, div_allot_item, average_flag=True)
            self.execute_task_allocation(div_name, div_item, div_allotList)
        else:
            self.logger.info('所有题平均分配成功！')

    @config_reminder_decorator(content='管理员登录账号和考试名称及科目')
    def run(self):
        org_id = self.login_object.get_login_token()
        exam_info = self.search_paper(examId, org_id) if (examId := self.search_exam(org_id)) else None
        if exam_info is not None:
            # 全卷恢复或暂停
            # self.exam_marking(exam_info, 1)
            # 题组重评
            # divId = self.exam_questionlist(exam_info, '11')
            # self.exam_divremark(exam_info, divId)
            # 全卷重评
            # self.exam_remark(exam_info)
            # 平均分配所有题
            self.average_allocate_all_questions(exam_info)
        else:
            self.logger.info('考试信息数据获取有误!')


if __name__ == '__main__':
    from KpLogin import KpLogin

    kp_login = KpLogin()
    ke = KpExam(kp_login)
    ke.run()
