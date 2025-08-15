import itertools
import random

import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential
from KpCreateExam import KpCreateExam
from NotifyMessage import config_reminder_decorator


class KpExam:
    def __init__(self, l_object):
        self.login_object = l_object
        self.data = self.login_object.kp_data
        self.logger = self.login_object.logger

    def search_exam_role(self):
        """
       获取考试角色权限
       :return: 考试详细信息字典
       """
        role_url = self.data['exam_role_url']
        role_response = self.login_object.get_response(role_url)
        result, r_data = self.login_object.check_response(role_response)
        if result:
            return r_data.get("data", {})
        else:
            self.logger.info('获取响应失败!')

    @staticmethod
    def get_sort_roles(role_data):
        """
        角色权限按指定顺序排序
        :param role_data: 用户角色权限数据
        :return: 返回排序后的第一个角色权限
        """
        role_priority = {
            'ROLE_ORG_MANAGER': 1,
            'ROLE_EXAM_MANAGER': 2,
            'ROLE_GRADE_LEADER': 3,
            'ROLE_SUBJECT_LEADER': 4,
            'ROLE_GRADE_SUBJECT_LEADER': 5,
            'ROLE_TEACHER': 6
        }
        sorted_roles = sorted([role['roleCode'] for role in role_data], key=lambda x: role_priority.get(x, 999))
        return sorted_roles[0]

    def generate_exam_params(self, user_info, exam_flag=True):
        """
        获取考试查询参数
        :param user_info: 用户信息
        :param exam_flag: 考试查询标记，是否使用考试名称查询，默认按考试名称查询
        :return:
        """
        # 拆分用户信息及用户权限
        *org_info, role_data = user_info
        # 提取并排序角色代码，取第一个角色
        exam_user_role, exam_role = self.get_sort_roles(role_data), self.search_exam_role()
        # 判断是否信息管理员或考试管理员
        isOrgManager = True if exam_user_role == 'ROLE_ORG_MANAGER' else False
        isExamManager = True if exam_user_role == 'ROLE_EXAM_MANAGER' else False
        # 判断是否使用考试名称查询
        exam_name = self.data['exam_name'] if exam_flag else ''
        return {"examStatus": 0, "userId": org_info[1], "roleCodes": [exam_user_role], "orgType": org_info[2],
                "orgId": org_info[0], "examName": exam_name, "pageSize": 999, "pageNum": 1, "isCollegeManager": False,
                "isExamManager": isOrgManager, "isOrgManager": isExamManager, **exam_role}

    def search_exam(self, user_info):
        """
        进行中考试列表查询考试id
        :param user_info: 用户数据
        :return: str 考试id
        """
        exam_url, exam_data = self.data['exam_url'], self.generate_exam_params(user_info)
        exam_response = self.login_object.get_response(url=exam_url, method='POST', data=exam_data)
        result, r_data = self.login_object.check_response(exam_response)
        if result:
            data = r_data.get("data")
            # role_data = [i['examId'] for i in data['list'] if i['examGrade'] == 11]
            # print(role_data)
            # data_count = len([i for i in data['list'] if i['examGrade'] == 11])
            # print(data_count)
            exam_id = data and data['list'][0]['examId'] or None
            return exam_id, exam_data['orgId'], exam_data['roleCodes']
        else:
            self.logger.info('获取响应失败!')

    def search_paper(self, exam_id, org_id, role_code):
        """
        查询科目对应paper信息
        :param exam_id: 考试id
        :param org_id: 机构id
        :param role_code: 权限代码
        :return: 包含考试exam及科目paper的字典
        """
        paper_url = self.data['paper_url']
        paper_data = {"data": {"examId": exam_id, "orgId": org_id, "roleCodes": role_code}}
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

    def exam_detail(self, exam_id, _, role_code):
        """
        获取考试详情信息
        :param _: 无效参数
        :param exam_id: 考试id
        :param role_code: 权限代码
        :return: 考试详细信息字典
        """
        detail_url = self.data['exam_detail_url']
        detail_params = {'examId': exam_id, 'findType': 2, 'roleCodes': role_code}
        detail_response = self.login_object.get_response(url=detail_url, method='GET', params=detail_params)
        result, r_data = self.login_object.check_response(detail_response)
        if result:
            return r_data.get("data", {})
        else:
            self.logger.info('获取响应失败!')

    def exam_detail_query(self, exam_info):
        exam_data = self.exam_detail(*exam_info)
        grade_id, exam_type = exam_data.get('gradeId'), exam_data.get('examModel')
        school_ids = ','.join([item['schoolId'] for item in exam_data['papers'][0]['schoolList']])
        return {'examId': exam_info[0], 'gradeId': grade_id, 'schoolIds': school_ids, 'modelType': exam_type}

    def exam_remark(self, remark_data):
        """
        全卷重评
        :param remark_data: 考试id及paperid的字典
        :return: None
        """
        remark_url = self.data['remark_url']
        # authcode = KpCreateExam(self.login_object).generate_authcode(remark_data.get('paperId'), '3')
        # remark_data.update({'authcode': authcode})
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

    def get_kgomr_scheme(self, exam_info):
        """
        获取绑定题卡的客观题设置
        :param exam_info: 考试id及paperid的字典
        :return: 客观题组成list数据
        """
        gomr_url, gomr_data = self.data['getomr_url'], {'data': exam_info}
        gomr_response = self.login_object.get_response(url=gomr_url, method='POST', data=gomr_data)
        result, r_data = self.login_object.check_response(gomr_response)
        if result:
            d_data = r_data and r_data.get('data', []) or []
            return d_data
        else:
            self.logger.info('获取响应失败!')

    @staticmethod
    def generate_random_combination(question_type, num_options):
        """
        单选、多选、判断题型随机生成标准答案
        :param question_type: 题型
        :param num_options: 题选项个数
        :return:
        """
        # 单选及多选根据数字转化成字母（1,2,3,4 --> A,B,C,D）列表，判断体型返回['T','F']列表
        kgAnswer_list = ['T', 'F'] if question_type == '2' else [chr(64 + i) for i in range(1, num_options + 1)]
        # 生成组合的位数（单选和判断只有1位，多选则是1-num_options之间的位数）
        max_length = num_options if question_type == '1' else 1
        # 生成选项组合所有可能的答案
        combinations = [''.join(p) for p in itertools.chain.from_iterable(
            itertools.combinations(kgAnswer_list, _) for _ in range(1, max_length + 1))]
        # 从所有答案集中返回随机一个标答
        return random.choice(combinations)

    @staticmethod
    def generate_kgcard_data(omr_data):
        """
        生成保存客观题设置的cardKgItems传参（无标答和分数时，自动设置标答及分数）
        :param omr_data: 题组的列表数据
        :return: 生成的题组列表数据
        """
        data = [{**item, 'itemId': item['no'], 'additional': False, 'originType': item['type'],
                 'score': int(item['score']) if item.get('score') else random.randint(1, 10),
                 'stdAnswer': item['stdAnswer'] if item.get('stdAnswer') else KpExam.generate_random_combination(
                     item['type'], item['kgAnswerNum'])} for item in omr_data] if omr_data else []
        return data

    def save_kgomr_scheme(self, data):
        """
        保存客观题设置
        :param data: 客观题传参
        :return:
        """
        somr_url = self.data['setomr_url']
        somr_response = self.login_object.get_response(url=somr_url, method='POST', data=data)
        result, r_data = self.login_object.check_response(somr_response)
        if result:
            self.logger.info('客观题设置保存成功！')
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
        user_info = self.login_object.get_login_token(keys=['userId', 'orgType', 'roleList'])
        exam_info = self.search_paper(*examInfo) if (examInfo := self.search_exam(user_info)) else None
        if exam_info is not None:
            # 全卷恢复或暂停
            self.exam_marking(exam_info, 1)
            # 题组重评
            # divId = self.exam_questionlist(exam_info, '11')
            # self.exam_divremark(exam_info, divId)
            # 全卷重评
            self.exam_remark(exam_info)
            # 平均分配所有题
            self.average_allocate_all_questions(exam_info)
        else:
            self.logger.info('考试信息数据获取有误!')

    def run2(self):
        user_info = self.login_object.get_login_token(keys=['userId', 'orgType', 'roleList'])
        exam_info = self.search_paper(*examInfo) if (examInfo := self.search_exam(user_info)) else None
        if exam_info is not None:
            kgomr_data = self.get_kgomr_scheme(exam_info)
            kgcard_list = self.generate_kgcard_data(kgomr_data)
            kgsomr_data = {'data': {**exam_info, 'cardKgItems': kgcard_list}}
            self.save_kgomr_scheme(kgsomr_data)
        else:
            self.logger.info('考试信息数据获取有误!')


if __name__ == '__main__':
    from KpLogin import KpLogin

    kp_login = KpLogin()
    ke = KpExam(kp_login)
    ke.run2()
