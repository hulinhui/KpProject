import random
import time


class KpMarking:
    def __init__(self, l_object):
        self.login_object = l_object
        self.data = self.login_object.kp_data

    def query_task_examid(self, orgid, orgtype, userid):
        """
        查询在线阅卷页面的考试id
        :param orgid: 机构id
        :param orgtype:机构类型
        :param userid:登录用户id
        :return: exam_id
        """
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
        """
        查询考试下指定科目的阅卷任务数据
        :param exam_id: 考试id
        :return: list 科目阅卷数据
        """
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

    @staticmethod
    def get_volume_info(volume_type):
        """
        根据卷的类型返回相关卷的获取字段
        :param volume_type: 卷的类型
        :return:
        """
        point_item = {
            1: ('正常卷', 'taskList', None, None),
            2: ('三评卷', 'threeMarks', 'threeCount', 'unThreeCount'),
            3: ('问题卷', 'unProblemGroups', 'problemCount', 'unProblemTotal'),
            4: ('仲裁卷', 'unArbitrationGroups', 'arbitrationCount', 'unArbitrationTotal'),
            5: ('打回卷', 'returnTaskList', None, None)
        }
        return point_item.get(volume_type, '输入的阅卷类型有误')

    def get_general_task(self, exam_info, volume_type):
        """
        根据卷的类型获取对应任务信息
        :param exam_info: 考试信息
        :param volume_type: 卷的类型
        :return:
        """
        if not exam_info: self.login_object.logger.info('当前科目暂无阅卷任务'); return
        p_name, paper_info = exam_info.pop('paper_name'), exam_info.pop('paper_info')
        vol_name, vol_path, vol_field, vol_unfield = self.get_volume_info(volume_type)
        finish_num, remain_num, div_alias, vol_data = 0, 0, [], paper_info.get(vol_path)
        if volume_type in [1, 5]:
            if vol_data is not None:
                div_alias, remains = list(zip(*[(_['divAlias'], _['remainNum']) for _ in vol_data if _['remainNum']]))
                finish_num, remain_num = sum([item.get('taskNum', 0) for item in vol_data]), sum(remains)
        if volume_type in [2, 3, 4]:
            finish_num, remain_num = paper_info.get(vol_field), paper_info.get(vol_unfield)
            div_alias = vol_data.keys() if isinstance(vol_data, dict) else vol_data
        exam_info['div_alias'] = list(div_alias)
        self.login_object.logger.info(f'【{p_name}】{vol_name}任务：已完成==>{finish_num},还剩==>{remain_num}')
        return exam_info

    def query_div_detail(self, div_dict):
        """
        获取题组的给分点信息
        :param div_dict: 考试信息
        :return:
        """
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
        """
        获取阅卷任务通用方法，包含（正常卷、问题卷、三评卷、仲裁卷）
        :param req_url: 获取阅卷任务请求url
        :param div_dict: 考试信息
        :param data_type: 传参类型（1：正常卷和三评卷；2：问题卷与仲裁卷）
        :return:考生密号、卷类型、任务id 组成的元祖
        """
        req_data = {"data": div_dict} if data_type == 1 else div_dict
        req_response = self.login_object.get_response(url=req_url, method='POST', data=req_data)
        result, r_data = self.login_object.check_response(req_response)
        if result:
            d_data = (r_data.get("data") or {}).get("list", r_data.get("data"))
            t_data = d_data[0] if d_data and isinstance(d_data, list) else d_data
            encode_no = t_data and t_data.get("encode") or None
            pjSeq_type = t_data and t_data.get("pjSeq") or None
            task_id = t_data and t_data.get("taskId") or None
            encode_no is None and self.login_object.logger.info(f"当前题组【{div_dict['itemId']}】暂时无任务")
            return encode_no, pjSeq_type, task_id
        else:
            error_msg = r_data.get("errorCode") and r_data.get("errorMsg") or '获取响应失败!'
            self.login_object.logger.info(error_msg)
            return (result,)

    def generate_random_score(self, point_item, task_tuple, score_type=1):
        """
        生成每个给分点的分数，并组成完整提交给分的参数
        :param point_item: 包含给分点的考生数据字典
        :param task_tuple: 阅卷任务接口返回的元祖信息（考生密号、卷类型、任务id）
        :param score_type: 给分方式（0：零分；1：范围内随机分数；2：满分）
        :return: 完整的提交给分参数
        """
        if not point_item: return
        for score_item in point_item.get('scorePoints', []):
            end, step = score_item.get('total_score'), score_item.get('step')
            score_iter = (round(i * step, 1) for i in range(int(end / step) + 2))
            random_score = random.choice(list(set((min(score, end) for score in score_iter))))
            score = 0 if score_type == 0 else random_score if score_type == 1 else end
            self.login_object.logger.info(f'本次评分为：{score}')
            score_item.update({'score': score})
        # 解包更新提交数据所需字段
        point_item.update(zip(['encode', 'pjSeq', 'taskId'], task_tuple))

    def req_submit_score(self, url, submit_data):
        """
        提交给分
        :param url: 提交给分的url
        :param submit_data: 提交给分的请求参数(打回卷不传data)
        :return:
        """
        if not submit_data: return
        normal_data = {"data": submit_data} if url.find('return') == -1 else submit_data
        normal_response = self.login_object.get_response(url=url, method='POST', data=normal_data)
        result, r_data = self.login_object.check_response(normal_response)
        if result:
            self.login_object.logger.info('提交分数成功！')
        else:
            error_msg = r_data.get("errorCode") and r_data.get("errorMsg") or '获取响应失败!'
            self.login_object.logger.info(error_msg)

    def exam_paper_info(self):
        """
        获取由exam_Id,paperId,paper_info组成的字典数据，给后续提交给分接口提供参数
        :return: dict
        """
        login_info = self.login_object.get_login_token(keys=['orgType', 'userId'])
        exam_id = self.query_task_examid(*login_info)
        if not exam_id:
            self.login_object.logger.info('获取exam_id参数有误')
            return None
        paper_info = self.query_task_paper(exam_id)
        if not paper_info:
            self.login_object.logger.info('获取paper_id参数有误')
            return None
        paper_id, paper_name, paper_info = paper_info[0]
        return {'examId': exam_id, 'paperId': paper_id, 'paper_name': paper_name, 'paper_info': paper_info}

    def submit_normal_score(self, exam_data):
        """
        正常卷给分
        :param exam_data: 考试数据
        :return:
        """
        div_data = self.get_general_task(exam_data, volume_type=1)
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
        """
        三评卷给分
        :param exam_data: 考试数据
        :return:
        """
        third_data = self.get_general_task(exam_data, volume_type=2)
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
        """
        问题卷给分
        :param exam_data: 考试数据
        :return:
        """
        problem_data = self.get_general_task(exam_data, volume_type=3)
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
                time.sleep(1)
                task_result = self.div_reques_task(self.data['problemtask_url'], problem_data, data_type=2)
                if not any(task_result): break
        self.login_object.logger.info('阅卷结束！')

    def submit_arbitration_score(self, exam_data):
        """
        仲裁卷给分
        :param exam_data: 考试数据
        :return:
        """
        arbit_data = self.get_general_task(exam_data, volume_type=4)
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
                time.sleep(1)
                task_result = self.div_reques_task(self.data['arbitratask_url'], arbit_data, data_type=2)
                if not any(task_result): break
        self.login_object.logger.info('阅卷结束！')

    def submit_return_score(self, exam_data):
        """
        打回卷给分
        :param exam_data: 考试数据
        :return:
        """
        return_data = self.get_general_task(exam_data, volume_type=5)
        if not return_data: return
        div_alias = return_data.pop('div_alias')
        while div_alias:
            return_data['itemId'] = div_alias.pop(0)
            task_result = self.div_reques_task(self.data['return_url'], return_data, data_type=2)
            if not any(task_result): continue
            self.login_object.logger.info(f"题组【{return_data['itemId']}】开始阅卷")
            submit_data = self.query_div_detail(return_data)
            while True:
                self.generate_random_score(submit_data, task_result)
                self.req_submit_score(self.data['submit_return_url'], submit_data)
                time.sleep(1)
                task_result = self.div_reques_task(self.data['return_url'], return_data, data_type=2)
                if not any(task_result): break
        self.login_object.logger.info('阅卷结束！')

    def run(self):
        """
        主流程
        :return:
        """
        exam_data = self.exam_paper_info()
        self.submit_normal_score(exam_data)
        self.submit_thrid_score(exam_data)
        self.submit_problem_score(exam_data)
        self.submit_arbitration_score(exam_data)
        self.submit_return_score(exam_data)


if __name__ == '__main__':
    from KpLogin import KpLogin

    kp_login = KpLogin()
    km = KpMarking(kp_login)
    km.run()
