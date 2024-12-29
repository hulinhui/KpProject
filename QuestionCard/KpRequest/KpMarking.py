import random


class KpMarking:
    def __init__(self, l_object):
        self.login_object = l_object
        self.data = self.login_object.kp_data
        self.logger = self.login_object.logger
        self.count = 0

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
            self.logger.info('获取响应失败!')

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
            self.logger.info('获取响应失败!')

    def get_volume_info(self, volume_type):
        """
        根据卷的类型返回相关卷的获取字段
        :param volume_type: 卷的类型
        :return:
        """
        volume_item = {
            1: ('正常卷', 'taskList', None, None, self.data['reqtask_url'], self.data['submit_normal_url']),
            2: ('三评卷', 'threeMarks', 'threeCount', 'unThreeCount', self.data['thirdtask_url'],
                self.data['submit_normal_url']),
            3: ('问题卷', 'unProblemGroups', 'problemCount', 'unProblemTotal', self.data['problemtask_url'],
                self.data['submit_problem_url']),
            4: ('仲裁卷', 'unArbitrationGroups', 'arbitrationCount', 'unArbitrationTotal', self.data['arbitratask_url'],
                self.data['submit_arbitra_url']),
            5: ('打回卷', 'returnTaskList', None, None, self.data['return_url'], self.data['submit_return_url'])
        }
        volume_datas = list(volume_item.get(volume_type))
        volume_datas.insert(0, volume_type)
        return volume_datas

    def get_general_task(self, exam_data, volume_list):
        """
        根据卷的类型获取对应任务信息
        :param exam_data: 考试信息
        :param volume_list: 卷相关参数列表
        :return:
        """
        exam_info = {**exam_data} if exam_data else None
        if not exam_info: self.logger.info('当前科目暂无阅卷任务'); return
        p_name, paper_info = exam_info.pop('paper_name'), exam_info.pop('paper_info')
        vol_type, vol_name, vol_path, vol_field, vol_unfield, *_ = volume_list
        finish_num, remain_num, div_alias, vol_data = 0, 0, [], paper_info.get(vol_path)
        if vol_type in [1, 5]:
            if vol_data:
                remain_nums, finish_nums = list(zip(*[(_['remainNum'], _['taskNum']) for _ in vol_data]))
                div_alias = [_['divAlias'] for _ in vol_data if _['remainNum'] > 0]
                finish_num, remain_num = sum(finish_nums), sum(remain_nums)
        if vol_type in [2, 3, 4]:
            div_alias = list(vol_data.keys()) if isinstance(vol_data, dict) else vol_data
            finish_num, remain_num = paper_info.get(vol_field), paper_info.get(vol_unfield)
            div_alias = div_alias if remain_num > 0 else []
        exam_info['div_alias'] = div_alias
        self.logger.info(f'【{p_name}】{vol_name}任务：已完成==>{finish_num},还剩==>{remain_num}')
        return exam_info

    def query_div_detail(self, div_dict):
        """
        获取题组的给分点信息
        :param div_dict: 考试信息
        :return: item  生成一个新的item作为提交给分的参数
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
            self.logger.info('获取响应失败!')
        return div_item

    def div_reques_task(self, req_url, div_dict, vol_type):
        """
        获取阅卷任务通用方法，包含（正常卷、问题卷、三评卷、仲裁卷）
        :param req_url: 获取阅卷任务请求url
        :param div_dict: 考试信息
        :param vol_type: 传参类型（1：正常卷 2:三评卷 3:问题卷 4：仲裁卷 5：打回卷）
        :return:考生密号、卷类型、任务id 组成的元祖
        """
        req_data = {"data": div_dict} if vol_type in [1, 2] else div_dict
        req_response = self.login_object.get_response(url=req_url, method='POST', data=req_data)
        result, r_data = self.login_object.check_response(req_response)
        if result:
            d_data = (r_data.get("data") or {}).get("list", r_data.get("data"))
            t_data = d_data[0] if d_data and isinstance(d_data, list) else d_data
            encode_no = t_data and t_data.get("encode") or None
            pjSeq_type = t_data and t_data.get("pjSeq") or None
            task_id = t_data and t_data.get("taskId") or None
            encode_no is None and self.logger.info(f"当前题组【{div_dict['itemId']}】暂时无任务")
            return encode_no, pjSeq_type, task_id
        else:
            error_msg = r_data.get("errorCode") and r_data.get("errorMsg") or '获取响应失败!'
            self.logger.info(error_msg)
            return (result,)

    def div_batch_task(self, q_item):
        """
        批量获取正常卷任务，默认5个
        :param q_item: 考试信息
        :return: 列表套元祖的考生encode
        """
        batch_task_url = self.data['batchtask_url']
        batch_data = {'paperId': q_item['paperId'], 'itemId': q_item['itemId'], "batchNum": 5, "pjSeq": 1}
        batch_response = self.login_object.get_response(url=batch_task_url, method='POST', data=batch_data)
        result, r_data = self.login_object.check_response(batch_response)
        if result:
            encode_list = [(_['encode'], _['pjSeq'], _['taskId']) for _ in r_data.get("data")]
            return encode_list
        else:
            error_msg = r_data.get("errorCode") and r_data.get("errorMsg") or '获取响应失败!'
            self.logger.info(error_msg)
            return []

    def generate_random_score(self, point_item, task_tuple, score_type=1):
        """
        生成每个给分点的分数，并组成完整提交给分的参数
        :param point_item: 包含给分点的考生数据字典
        :param task_tuple: 阅卷任务接口返回的元祖信息（考生密号、卷类型、任务id）
        :param score_type: 给分方式（0：零分；1：范围内随机分数；2：满分）
        :return: 完整的提交给分参数
        """
        if not point_item: return
        total_score = 0
        for score_item in point_item.get('scorePoints', []):
            end, step = score_item.get('total_score'), score_item.get('step')
            score_iter = (round(i * step, 1) for i in range(int(end / step) + 2))
            random_score = random.choice(list(set((min(score, end) for score in score_iter))))
            score = 0 if score_type == 0 else random_score if score_type == 1 else end
            score_item.update({'score': score})
            total_score += score
        # 解包更新提交数据所需字段
        point_item.update(zip(['encode', 'pjSeq', 'taskId'], task_tuple))
        self.logger.info(f"【考生:{task_tuple[0]}】-第{point_item['itemId']}题评分为：{total_score}分")

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
            self.count += 1
            self.logger.info('提交分数成功！')
        else:
            error_msg = r_data.get("errorCode") and r_data.get("errorMsg") or '获取响应失败!'
            self.logger.info(error_msg)

    def req_submit_problem(self, url, submit_data):
        """
        提交问题卷
        :param url: 提交问题卷的url
        :param submit_data: 提交问题卷的请求参数
        :return:
        """
        if not submit_data: return
        normal_data = {"data": submit_data | {"problemType": "0", "problemDesc": ""}}
        normal_response = self.login_object.get_response(url=url, method='POST', data=normal_data)
        result, r_data = self.login_object.check_response(normal_response)
        if result:
            self.count += 1
            self.logger.info('提交问题卷成功！')
        else:
            error_msg = r_data.get("errorCode") and r_data.get("errorMsg") or '获取响应失败!'
            self.logger.info(error_msg)

    def exam_paper_info(self):
        """
        获取由exam_Id,paperId,paper_info组成的字典数据，给后续提交给分接口提供参数
        :return: dict
        """
        login_info = self.login_object.get_login_token(keys=['orgType', 'userId'])
        if login_info is None: exit()
        exam_id = self.query_task_examid(*login_info)
        if not exam_id: self.logger.info('获取exam_id参数有误');return
        paper_info = self.query_task_paper(exam_id)
        if not paper_info: self.logger.info('获取paper_id参数有误');return
        paper_id, paper_name, paper_info = paper_info[0]
        return {'examId': exam_id, 'paperId': paper_id, 'paper_name': paper_name, 'paper_info': paper_info}

    def submit_general_score(self, question_item, volume_list):
        """
        通用卷给分
        :param question_item: 阅卷数据
        :param volume_list: 卷相关参数列表
        :return:
        """
        volume_type, vol_name, *_, task_url, submit_url = volume_list
        div_alias = question_item.pop('div_alias')
        while div_alias:
            question_item['itemId'] = div_alias.pop(0)
            task_result = self.div_reques_task(task_url, question_item, vol_type=volume_type)
            if not any(task_result): continue
            self.logger.info(f"题组【{question_item['itemId']}】开始阅卷")
            submit_data = self.query_div_detail(question_item)
            while True:
                self.generate_random_score(submit_data, task_result)
                self.req_submit_score(submit_url, submit_data)
                task_result = self.div_reques_task(task_url, question_item, vol_type=volume_type)
                if not any(task_result): break
        self.logger.info(f'【{vol_name}】阅卷结束！')

    def submit_problem_paper(self, question_item, volume_list):
        """
        提交问题卷
        :param question_item: 阅卷数据
        :param volume_list: 卷相关参数列表
        :return:
        """
        volume_list.append(self.data['problem_paper_url'])
        volume_type, vol_name, *_, task_url, _, problem_paper_url = volume_list
        div_alias = question_item.pop('div_alias')
        while div_alias:
            question_item['itemId'] = div_alias.pop(0)
            task_result = self.div_reques_task(task_url, question_item, vol_type=volume_type)
            if not any(task_result): continue
            self.logger.info(f"题组【{question_item['itemId']}】开始阅卷")
            while True:
                submit_data = {**question_item} | dict(zip(['encode', 'pjSeq', 'taskId'], task_result))
                self.req_submit_problem(url=problem_paper_url, submit_data=submit_data)
                task_result = self.div_reques_task(task_url, question_item, vol_type=volume_type)
                if not any(task_result): break
        self.logger.info(f"本次总共评分次数:{self.count}")

    def submit_preload_score(self, question_item, volume_list):
        """
        正常卷预加载给分
        :param question_item: 阅卷数据
        :param volume_list: 卷相关参数列表
        :return:
        """
        volume_type, vol_name, *_, task_url, submit_url = volume_list
        div_alias = question_item.pop('div_alias')
        div_str, div_num = '、'.join(div_alias), len(div_alias)
        self.logger.info(f"当前科目有({div_str})等{div_num}个题组需要阅卷")
        question_item['itemId'] = div_alias[0]
        while div_alias:
            encode_list = self.div_batch_task(question_item)
            submit_data = self.query_div_detail(question_item)
            while encode_list:
                encode_info = encode_list.pop(0)
                self.generate_random_score(submit_data, encode_info)
                self.req_submit_score(submit_url, submit_data)
                if not encode_list: continue
                task_result = self.div_reques_task(task_url, question_item, vol_type=volume_type)
                if not any(task_result): continue
                encode_list.append(task_result)
            div_alias.pop(0)
            self.logger.info(f"题组【{question_item['itemId']}】阅卷完成")
            if not div_alias: break
            question_item['itemId'] = div_alias[0]
            self.div_reques_task(task_url, question_item, vol_type=volume_type)
        self.logger.info(f"本次总共评分次数:{self.count}")

    def problem_normal_paper(self):
        exam_data = self.exam_paper_info()
        volume_info = self.get_volume_info(volume_type=1)
        item = self.get_general_task(exam_data, volume_info)
        if not (item and item.get('div_alias')):
            return
        self.submit_problem_paper(item, volume_info)

    def preload_normal_score(self):
        """
        正常卷预加载模式
        :return:
        """
        exam_data = self.exam_paper_info()
        volume_info = self.get_volume_info(volume_type=1)
        item = self.get_general_task(exam_data, volume_info)
        if not (item and item.get('div_alias')):
            return
        self.submit_preload_score(item, volume_info)

    def run(self):
        """
        全阅卷主流程
        :return:
        """
        exam_data = self.exam_paper_info()
        for _ in range(1, 6):
            volume_info = self.get_volume_info(_)
            item = self.get_general_task(exam_data, volume_info)
            if not (item and item.get('div_alias')):
                continue
            self.submit_general_score(item, volume_info)
        print(self.count)


if __name__ == '__main__':
    from KpLogin import KpLogin

    kp_login = KpLogin()
    km = KpMarking(kp_login)
    km.problem_normal_paper()
