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

    def query_div_detail(self, div_dict):
        div_url = self.data['divdetail_url']
        div_data = {"data": div_dict}
        div_response = self.login_object.get_response(url=div_url, method='POST', data=div_data)
        result, r_data = self.login_object.check_response(div_response)
        if result:
            score_points = r_data.get("data").get("scorePoints")
            score_data = [{key: value for key, value in point.items() if value} for point in score_points]
            [score_data[i].update({'total_score': score_data[i].pop('score')}) for i in range(len(score_data))]
            div_dict['scorePoints'] = score_data
            return div_dict
        else:
            self.login_object.logger.info('获取响应失败!')

    def div_reques_task(self, req_url, div_dict, flag=False):
        req_data = {"data": div_dict}
        req_response = self.login_object.get_response(url=req_url, method='POST', data=req_data)
        result, r_data = self.login_object.check_response(req_response)
        if result:
            t_data = r_data.get("data")
            encode_no = t_data and t_data.get("encode") or None
            pjSeq_type = t_data and t_data.get("pjSeq") or None
            encode_no is None and self.login_object.logger.info(f"当前题组【{div_dict['itemId']}】暂时无任务")
            return_value = (encode_no, pjSeq_type) if flag else encode_no
            return return_value
        else:
            error_msg = r_data.get("errorCode") and r_data.get("errorMsg") or '获取响应失败!'
            self.login_object.logger.info(error_msg)
            return result

    def generate_random_score(self, point_item, score_type=1):
        if not point_item: return
        for score_item in point_item.get('scorePoints', []):
            end, step = score_item.get('total_score'), score_item.get('step')
            score_iter = (round(i * step, 1) for i in range(int(end / step) + 2))
            random_score = random.choice(list(set((min(score, end) for score in score_iter))))
            score = 0 if score_type == 0 else random_score if score_type == 1 else end
            self.login_object.logger.info(f'本次评分为：{score}')
            score_item.update({'score': score})
        return point_item

    def req_submit_score(self, submit_data):
        if not submit_data: return
        normal_url = self.data['submit_normal_url']
        normal_data = {"data": submit_data}
        normal_response = self.login_object.get_response(url=normal_url, method='POST', data=normal_data)
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
            reques_result = self.div_reques_task(req_url=self.data['reqtask_url'], div_dict=div_data, flag=True)
            if not all(reques_result): continue
            self.login_object.logger.info(f"题组【{div_data['itemId']}】开始阅卷")
            encode_no, pjSeq_type = reques_result
            div_item = self.query_div_detail(div_data)
            while True:
                if not encode_no: break
                div_item and div_item.update({'encode': encode_no, 'pjSeq': pjSeq_type})
                submit_data = self.generate_random_score(div_item)
                self.req_submit_score(submit_data)
                time.sleep(1)
                encode_no = self.div_reques_task(req_url=self.data['reqtask_url'], div_dict=div_data)
        self.login_object.logger.info('阅卷结束！')

    def submit_thrid_score(self, exam_data):
        third_data = self.get_third_task(exam_data)
        if not third_data: return
        div_alias = third_data.pop('div_alias')
        while div_alias:
            third_data['itemId'] = div_alias.pop(0)
            reques_result = self.div_reques_task(req_url=self.data['thirdtask_url'], div_dict=third_data, flag=True)
            if not all(reques_result): continue
            self.login_object.logger.info(f"题组【{third_data['itemId']}】开始阅卷")
            encode_no, pjSeq_type = reques_result
            div_item = self.query_div_detail(third_data)
            while True:
                if not encode_no: break
                div_item and div_item.update({'encode': encode_no, 'pjSeq': pjSeq_type})
                submit_data = self.generate_random_score(div_item)
                self.req_submit_score(submit_data)
                time.sleep(1)
                encode_no = self.div_reques_task(req_url=self.data['thirdtask_url'], div_dict=third_data)
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
        self.submit_thrid_score(exam_data)


if __name__ == '__main__':
    from KpLogin import KpLogin

    kp_login = KpLogin()
    km = KpMarking(kp_login)
    km.run()
