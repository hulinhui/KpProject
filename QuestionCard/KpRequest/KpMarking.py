import random
import time


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
            paper_name = self.data['paper_name']
            paper_list = [(item['paperId'], item['paperName'], item) for item in r_data.get("data", []) if
                          item['paperName'] == paper_name]
            return paper_list
        else:
            self.login_object.logger.info('获取响应失败!')

    def get_normal_task(self, exam_info):
        if exam_info:
            paper_name = exam_info.pop('paper_name')
            divtask_list = exam_info.pop('paper_info').get('taskList', [])
            div_alias, remain_nums = list(
                zip(*[(_['divAlias'], _['remainNum']) for _ in divtask_list if _['remainNum']])) or ([], [])
            finish_num = sum([item.get('taskNum', 0) for item in divtask_list])
            self.login_object.logger.info(f'【{paper_name}】正常卷任务：已完成==>{finish_num},还剩==>{sum(remain_nums)}')
            exam_info['div_alias'] = list(div_alias)
            return exam_info
        else:
            self.login_object.logger.info('当前科目暂无阅卷任务')

    def get_third_task(self, exam_info):
        if exam_info:
            paper_name = exam_info.pop('paper_name')
            paper_info = exam_info.pop('paper_info')
            thridtask_list = paper_info.get('threeMarks', [])
            three_count, unthree_count = paper_info.get('threeCount', 0), paper_info.get('unThreeCount', 0)
            self.login_object.logger.info(f'【{paper_name}】三评卷任务：已完成==>{three_count},还剩==>{unthree_count}')
            exam_info['div_alias'] = list(thridtask_list)
            return exam_info
        else:
            self.login_object.logger.info('当前科目暂无阅卷任务')

    def get_problem_task(self, exam_info):
        if exam_info:
            paper_name = exam_info.pop('paper_name')
            paper_info = exam_info.pop('paper_info')
            unProblemGroups = paper_info.get('unProblemGroups', {})
            problem_count, unproblem_count = paper_info.get('problemCount', 0), paper_info.get('unProblemTotal', 0)
            self.login_object.logger.info(f'【{paper_name}】问题卷任务：已完成==>{problem_count},还剩==>{unproblem_count}')
            exam_info['div_alias'] = list(unProblemGroups.keys())
            return exam_info
        else:
            self.login_object.logger.info('当前科目暂无阅卷任务')

    def get_arbitration_task(self, exam_info):
        if exam_info:
            paper_name = exam_info.pop('paper_name')
            paper_info = exam_info.pop('paper_info')
            unArbitrationGroups = paper_info.get('unArbitrationGroups', {})
            arbit_count, unarbit_count = paper_info.get('arbitrationCount', 0), paper_info.get('unArbitrationTotal', 0)
            self.login_object.logger.info(f'【{paper_name}】仲裁卷任务：已完成==>{arbit_count},还剩==>{unarbit_count}')
            exam_info['div_alias'] = list(unArbitrationGroups.keys())
            return exam_info
        else:
            self.login_object.logger.info('当前科目暂无阅卷任务')

    def query_div_detail(self, div_dict):
        div_item = {}
        div_url = self.data['divdetail_url']
        div_data = {"data": div_dict}
        div_response = self.login_object.get_response(url=div_url, method='POST', data=div_data)
        result, r_data = self.login_object.check_response(div_response)
        if result:
            div_item.update(div_dict)
            score_points = r_data.get("data").get("scorePoints")
            score_data = [{key: value for key, value in point.items() if value} for point in score_points]
            [score_data[i].update({'total_score': score_data[i].pop('score')}) for i in range(len(score_data))]
            div_item['scorePoints'] = score_data
        else:
            self.login_object.logger.info('获取响应失败!')
        return div_item

    def div_reques_task(self, req_url, div_dict, data_type=1):
        req_data = {"data": div_dict} if data_type == 1 else div_dict
        req_response = self.login_object.get_response(url=req_url, method='POST', data=req_data)
        result, r_data = self.login_object.check_response(req_response)
        if result:
            t_data = r_data.get("data")
            encode_no = t_data and t_data.get("encode") or None
            pjSeq_type = t_data and t_data.get("pjSeq") or None
            task_id = t_data and t_data.get("taskId") or None
            encode_no is None and self.login_object.logger.info(f"当前题组【{div_dict['itemId']}】暂时无任务")
            return encode_no, pjSeq_type, task_id
        else:
            error_msg = r_data.get("errorCode") and r_data.get("errorMsg") or '获取响应失败!'
            self.login_object.logger.info(error_msg)
            return (result,)

    def generate_random_score(self, point_item, task_item, score_type=1):
        if not point_item: return
        encode_no, pjSeq_type, task_id = task_item
        for score_item in point_item.get('scorePoints', []):
            end, step = score_item.get('total_score'), score_item.get('step')
            score_iter = (round(i * step, 1) for i in range(int(end / step) + 2))
            random_score = random.choice(list(set((min(score, end) for score in score_iter))))
            score = 0 if score_type == 0 else random_score if score_type == 1 else end
            self.login_object.logger.info(f'本次评分为：{score}')
            score_item.update({'score': score})
        point_item.update({'encode': encode_no, 'pjSeq': pjSeq_type, 'taskId': task_id})

    def req_submit_score(self, url, submit_data):
        if not submit_data: return
        normal_data = {"data": submit_data}
        normal_response = self.login_object.get_response(url=url, method='POST', data=normal_data)
        result, r_data = self.login_object.check_response(normal_response)
        if result:
            self.login_object.logger.info('提交分数成功！')
        else:
            error_msg = r_data.get("errorCode") and r_data.get("errorMsg") or '获取响应失败!'
            self.login_object.logger.info(error_msg)

    def submit_normal_score(self, exam_data):
        div_data = self.get_normal_task(exam_data)
        if not div_data: return
        div_alias = div_data.pop('div_alias')
        while div_alias:
            div_data['itemId'] = div_alias.pop(0)
            task_result = self.div_reques_task(req_url=self.data['reqtask_url'], div_dict=div_data)
            if not any(task_result): continue
            self.login_object.logger.info(f"题组【{div_data['itemId']}】开始阅卷")
            submit_data = self.query_div_detail(div_data)
            while True:
                self.generate_random_score(submit_data, task_result)
                self.req_submit_score(self.data['submit_normal_url'], submit_data)
                time.sleep(1)
                task_result = self.div_reques_task(self.data['reqtask_url'], div_data)
                if not any(task_result): break
        self.login_object.logger.info('阅卷结束！')

    def submit_thrid_score(self, exam_data):
        third_data = self.get_third_task(exam_data)
        if not third_data: return
        div_alias = third_data.pop('div_alias')
        while div_alias:
            third_data['itemId'] = div_alias.pop(0)
            task_result = self.div_reques_task(req_url=self.data['thirdtask_url'], div_dict=third_data)
            if not any(task_result): continue
            self.login_object.logger.info(f"题组【{third_data['itemId']}】开始阅卷")
            submit_data = self.query_div_detail(third_data)
            while True:
                self.generate_random_score(submit_data, task_result)
                self.req_submit_score(self.data['submit_normal_url'], submit_data)
                time.sleep(1)
                task_result = self.div_reques_task(req_url=self.data['thirdtask_url'], div_dict=third_data)
                if not any(task_result): break
        self.login_object.logger.info('阅卷结束！')

    def submit_problem_score(self, exam_data):
        problem_data = self.get_problem_task(exam_data)
        if not problem_data: return
        div_alias = problem_data.pop('div_alias')
        while div_alias:
            problem_data['itemId'] = div_alias.pop(0)
            task_result = self.div_reques_task(self.data['problemtask_url'], problem_data, data_type=2)
            if not any(task_result): continue
            self.login_object.logger.info(f"题组【{problem_data['itemId']}】开始阅卷")
            submit_data = self.query_div_detail(problem_data)
            while True:
                self.generate_random_score(submit_data, task_result)
                self.req_submit_score(self.data['submit_problem_url'], submit_data)
                time.sleep(5)
                task_result = self.div_reques_task(self.data['problemtask_url'], problem_data, data_type=2)
                if not any(task_result): break
        self.login_object.logger.info('阅卷结束！')

    def submit_arbitration_score(self, exam_data):
        arbit_data = self.get_arbitration_task(exam_data)
        if not arbit_data: return
        div_alias = arbit_data.pop('div_alias')
        while div_alias:
            arbit_data['itemId'] = div_alias.pop(0)
            task_result = self.div_reques_task(self.data['arbitratask_url'], arbit_data, data_type=2)
            if not any(task_result): continue
            self.login_object.logger.info(f"题组【{arbit_data['itemId']}】开始阅卷")
            submit_data = self.query_div_detail(arbit_data)
            while True:
                self.generate_random_score(submit_data, task_result)
                self.req_submit_score(self.data['submit_arbitra_url'], submit_data)
                time.sleep(10)
                task_result = self.div_reques_task(self.data['arbitratask_url'], arbit_data, data_type=2)
                if not any(task_result): break
        self.login_object.logger.info('阅卷结束！')

    def exam_paper_info(self):
        login_info = self.login_object.get_login_token(keys=['orgType', 'userId'])
        exam_id = self.query_task_exam(*login_info)
        if not exam_id:
            self.login_object.logger.info('获取exam_id参数有误')
            return None
        paper_info = self.query_task_paper(exam_id)
        if not paper_info:
            self.login_object.logger.info('获取paper_id参数有误')
            return None
        paper_id, paper_name, paper_info = paper_info[0]
        return {'examId': exam_id, 'paperId': paper_id, 'paper_name': paper_name, 'paper_info': paper_info}

    def run(self):
        exam_data = self.exam_paper_info()
        # self.submit_normal_score(exam_data)
        # self.submit_thrid_score(exam_data)
        self.submit_problem_score(exam_data)
        # self.submit_arbitration_score(exam_data)


if __name__ == '__main__':
    from KpLogin import KpLogin

    kp_login = KpLogin()
    km = KpMarking(kp_login)
    km.run()
