"""
作者: hulinhui6
日期：2025年04月28日
"""
import time

import urllib3
import json
import queue
from threading import Thread, Event, Lock
from urllib3.exceptions import InsecureRequestWarning
from QuestionCard.KpRequest.Handle_Logger import HandleLog
from QuestionCard.KpRequest.FormatHeaders import get_format_headers, headers_kp, dict_cover_data, get_content_text
from QuestionCard.KpRequest.NotifyMessage import read_config
from urllib.parse import urlparse
import requests
import random

# 忽略警告
urllib3.disable_warnings(category=InsecureRequestWarning)


class Producer(Thread):
    def __init__(self, m_queue, t_queue, name):
        super().__init__()
        self.m_queue = m_queue
        self.t_queue = t_queue
        self.name = name
        self.domain = None
        self.headers = None
        self.lock = Lock()
        self.kp_data = read_config(name='KP')
        self.logger = HandleLog()

    def init_headers(self, format_str=None):
        """
        初始化请求头，请求头设置域名及默认表单模式，生成初始请求头
        :return:
        """
        self.domain = [self.kp_data[key] for key in self.kp_data.keys() if key.startswith(self.kp_data['env_flag'])][0]
        header_item = {'Host': urlparse(self.domain).hostname, 'Content-Type': get_content_text(format_str)}
        headers = get_format_headers(headers_kp, **header_item)
        return headers

    def get_response(self, url, method='GET', params=None, data=None, files=None):
        """
        负责请求处理
        :param files: 请求文件
        :param url: 请求url
        :param method: 请求方法
        :param params: 请求参数，get使用
        :param data: 请求body，post方法使用
        :return: response:请求响应对象
        """
        try:
            data = json.dumps(data) if isinstance(data, (dict, list)) and files is None else data
            response = requests.request(method=method.upper(), url=self.domain + url, headers=self.headers,
                                        params=params, data=data, files=files, verify=False)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response
        except Exception as e:
            self.logger.info(e)

    @staticmethod
    def check_response(response, return_value=None):
        """
        处理响应内容，进行响应结果判断
        :param response: 请求响应对象
        :param return_value: 是否返回响应json数据，默认返回
        :return: result, json_data
        """
        json_data = {} if response is None else response.json()
        result = json_data['result'] if json_data and 'result' in json_data else False
        if return_value is not None:
            return result
        else:
            return result, json_data

    def create_login_data(self, mobile, passwd):
        self.headers = self.init_headers()
        self.headers['Content-Type'] = get_content_text('from')
        login_url = self.kp_data['login_url']
        login_item = {'username': mobile, 'password': passwd, 'randomStr': '38716_1518792598512', 'code': 'ep3e',
                      'verCode': '', 'grant_type': 'password', 'scope': 'server', 'encrypted': 'false'}
        login_resp = self.get_response(login_url, method='POST', data=dict_cover_data(login_item))
        result, r_data = self.check_response(login_resp)
        if result:
            token = r_data.get('access_token')
            self.headers['Authorization'] = f"Bearer {token}"
            self.headers['Content-Type'] = get_content_text()
            data = r_data and r_data.get('data') or None
            return data
        else:
            self.logger.info('用户登录失败')

    def change_account(self, a_data):
        """
        账号多机构时，进行切换机构，设置登录token，返回机构信息
        :param a_data: 机构数据
        :return: org_info
        """
        org_name, user_url = a_data['org_name'], self.kp_data['user_url'],
        account_info = [u for u in a_data['users'] if u.get('companyEnable') and u.get('companyName') == org_name]
        if not account_info: self.logger.info(f'机构-{org_name}：没找到!');return
        u_item = {key: account_info[0][key] for key in ('userType', 'userId')}
        user_data = {'accountId': a_data['accountId'], 'randomStr': int(time.time() * 1000)} | u_item
        user_resp = self.get_response(user_url, method='POST', data=user_data)
        result, r_data = self.check_response(user_resp)
        if result:
            data = r_data and r_data.get('data') or None
            if data: self.headers['Authorization'] = f"Bearer {data['accessToken']}"
            return data
        else:
            self.logger.info('响应数据有误')

    def get_org_info(self, data, keys):
        """
        判断当前账号是否存在多个机构，单个机构直接返回机构信息，多个机构根据配置信息-学校名称返回机构信息
        :param keys: 获取登录所需字段
        :param data: 当前账号登录的默认机构
        :return: org_info （机构名，机构id）
        """
        valid_account_num = sum(1 for _ in data['users'] if _.get('companyEnable'))
        org_info = (
            self.change_account(data) if valid_account_num > 1 else
            data if valid_account_num == 1 else
            (self.logger.info('当前账号无有效的机构！') or None)
        )
        return [org_info.get(key) for key in ['name', 'orgId', *(keys or [])]] if org_info else None

    def get_login_token(self, user_data, keys=None):
        """
        登录:
        :return: org_id  机构id
        """
        mobile, passwd, org_name = user_data
        account_data = self.create_login_data(mobile, passwd)
        account_data['org_name'] = org_name
        if not account_data: return
        info_list = self.get_org_info(account_data, keys)
        info_list and self.logger.info(f"{self.name}用户-{info_list[0]}:登录成功!")
        return info_list

    def run(self):
        while not self.m_queue.empty():
            try:
                account_info = self.m_queue.get(timeout=1)
                login_data = self.get_login_token(account_info, keys=['orgType', 'userId'])
                tea_task = (*login_data, self.headers, self.domain)
                self.t_queue.put(tea_task)
            except queue.Empty:
                continue
            except Exception as e:
                print(f'Error in producer: {e}')


class Consumer(Thread):
    def __init__(self, t_queue, name):
        super().__init__()
        self.name = name
        self.domain = None
        self.headers = None
        self.logger = HandleLog()
        self.t_queue = t_queue
        self.kp_data = read_config(name='KP')
        self.lock = Lock()
        self.stop_event = Event()

    def get_response(self, url, method='GET', params=None, data=None, files=None):
        """
        负责请求处理
        :param files: 请求文件
        :param url: 请求url
        :param method: 请求方法
        :param params: 请求参数，get使用
        :param data: 请求body，post方法使用
        :return: response:请求响应对象
        """
        try:
            data = json.dumps(data) if isinstance(data, (dict, list)) and files is None else data
            response = requests.request(method=method.upper(), url=self.domain + url, headers=self.headers,
                                        params=params, data=data, files=files, verify=False)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response
        except Exception as e:
            self.logger.info(e)

    @staticmethod
    def check_response(response, return_value=None):
        """
        处理响应内容，进行响应结果判断
        :param response: 请求响应对象
        :param return_value: 是否返回响应json数据，默认返回
        :return: result, json_data
        """
        json_data = {} if response is None else response.json()
        result = json_data['result'] if json_data and 'result' in json_data else False
        if return_value is not None:
            return result
        else:
            return result, json_data

    def query_task_examid(self, orgid, orgtype, userid):
        """
        查询在线阅卷页面的考试id
        :param orgid: 机构id
        :param orgtype:机构类型
        :param userid:登录用户id
        :return: exam_id
        """
        eTask_url = self.kp_data['examtask_url']
        eTask_data = {"data": {"userId": userid, "orgType": orgtype, "orgId": orgid,
                               "roleCodes": ["ROLE_ORG_MANAGER", "ROLE_CLASS_TEACHER", "ROLE_TEACHER"],
                               "examName": self.kp_data['exam_name']}, "pageSize": 5, "pageNum": 1}
        eTask_response = self.get_response(url=eTask_url, method='POST', data=eTask_data)
        result, r_data = self.check_response(eTask_response)
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
        pTask_url = self.kp_data['papertask_url']
        pTask_data = {"examId": exam_id}
        pTask_response = self.get_response(url=pTask_url, method='POST', data=pTask_data)
        result, r_data = self.check_response(pTask_response)
        if result:
            paper_name = self.kp_data['paper_name']
            paper_list = [(item['paperId'], item['paperName'], item) for item in r_data.get("data", []) if
                          item['paperName'] == paper_name]
            return paper_list
        else:
            self.logger.info('获取响应失败!')

    def exam_paper_info(self, login_info):
        """
        获取由exam_Id,paperId,paper_info组成的字典数据，给后续提交给分接口提供参数
        :return: dict
        """
        exam_id = self.query_task_examid(*login_info)
        if not exam_id: self.logger.info('获取exam_id参数有误');return
        paper_info = self.query_task_paper(exam_id)
        if not paper_info: self.logger.info('获取paper_id参数有误');return
        paper_id, paper_name, paper_info = paper_info[0]
        return {'examId': exam_id, 'paperId': paper_id, 'paper_name': paper_name, 'paper_info': paper_info}

    def get_volume_info(self, volume_type):
        """
        根据卷的类型返回相关卷的获取字段
        :param volume_type: 卷的类型
        :return:
        """
        volume_item = {
            1: ('正常卷', 'taskList', None, None, self.kp_data['reqtask_url'], self.kp_data['submit_normal_url']),
            2: ('三评卷', 'threeMarks', 'threeCount', 'unThreeCount', self.kp_data['thirdtask_url'],
                self.kp_data['submit_normal_url']),
            3: ('问题卷', 'unProblemGroups', 'problemCount', 'unProblemTotal', self.kp_data['problemtask_url'],
                self.kp_data['submit_problem_url']),
            4: (
                '仲裁卷', 'unArbitrationGroups', 'arbitrationCount', 'unArbitrationTotal',
                self.kp_data['arbitratask_url'],
                self.kp_data['submit_arbitra_url']),
            5: ('打回卷', 'returnTaskList', None, None, self.kp_data['return_url'], self.kp_data['submit_return_url'])
        }
        volume_datas = list(volume_item.get(volume_type))
        volume_datas.insert(0, volume_type)
        return volume_datas

    def get_general_task(self, tea_name, exam_data, volume_list):
        """
        根据卷的类型获取对应任务信息
        :param tea_name: 老师名称
        :param exam_data: 考试信息
        :param volume_list: 卷相关参数列表
        :return:
        """
        exam_info = {**exam_data} if exam_data else None
        if not exam_info: self.logger.info(f'{tea_name}-当前科目暂无阅卷任务'); return
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
        self.logger.info(
            f'{self.name}-{tea_name}阅卷-【{p_name}】{vol_name}任务：已完成==>{finish_num},还剩==>{remain_num}')
        return exam_info

    def div_batch_task(self, q_item):
        """
        批量获取正常卷任务，默认5个
        :param q_item: 考试信息
        :return: 列表套元祖的考生encode
        """
        batch_task_url = self.kp_data['batchtask_url']
        batch_data = {'paperId': q_item['paperId'], 'itemId': q_item['itemId'], "batchNum": 5, "pjSeq": 1}
        batch_response = self.get_response(url=batch_task_url, method='POST', data=batch_data)
        result, r_data = self.check_response(batch_response)
        if result:
            batch_result = r_data.get("data")
            encode_list = [(_['encode'], _['pjSeq'], _['taskId']) for _ in batch_result]
            remain_task = int(next(_['remainTasks'] for _ in batch_result)) if batch_result else 0
            return encode_list, remain_task
        else:
            error_msg = r_data.get("errorCode") and r_data.get("errorMsg") or '获取响应失败!'
            self.logger.info(error_msg)
            return [], 0

    def query_div_detail(self, div_dict):
        """
        获取题组的给分点信息
        :param div_dict: 考试信息
        :return: item  生成一个新的item作为提交给分的参数
        """
        div_item = {}
        div_url = self.kp_data['divdetail_url']
        div_data = {"data": div_dict}
        div_response = self.get_response(url=div_url, method='POST', data=div_data)
        result, r_data = self.check_response(div_response)
        if result:
            div_item.update(div_dict)
            score_points = r_data.get("data").get("scorePoints")
            score_data = [{key: value for key, value in point.items() if value} for point in score_points]
            [score_data[i].update({'total_score': score_data[i].pop('score')}) for i in range(len(score_data))]
            div_item['scorePoints'] = score_data
        else:
            self.logger.info('获取响应失败!')
        return div_item

    def generate_random_score(self, tea_name, point_item, task_tuple, score_type=1):
        """
        生成每个给分点的分数，并组成完整提交给分的参数
        :param tea_name: 老师名
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
            with self.lock:
                total_score += score
        # 解包更新提交数据所需字段
        point_item.update(zip(['encode', 'pjSeq', 'taskId'], task_tuple))
        point_item.update({'source': 'web'})
        self.logger.info(f"[{tea_name}]阅卷-【考生:{task_tuple[0]}】-第{point_item['itemId']}题评分为：{total_score}分")

    def req_submit_score(self, url, submit_data):
        """
        提交给分
        :param url: 提交给分的url
        :param submit_data: 提交给分的请求参数(打回卷不传data)
        :return:
        """
        if not submit_data: return
        normal_data = {"data": submit_data} if url.find('return') == -1 else submit_data
        normal_response = self.get_response(url=url, method='POST', data=normal_data)
        result, r_data = self.check_response(normal_response)
        if result:
            self.logger.info('提交分数成功！')
        else:
            error_msg = r_data.get("errorCode") and r_data.get("errorMsg") or '获取响应失败!'
            self.logger.info(error_msg)

    def div_reques_task(self, req_url, div_dict, vol_type):
        """
        获取阅卷任务通用方法，包含（正常卷、问题卷、三评卷、仲裁卷）
        :param req_url: 获取阅卷任务请求url
        :param div_dict: 考试信息
        :param vol_type: 传参类型（1：正常卷 2:三评卷 3:问题卷 4：仲裁卷 5：打回卷）
        :return:考生密号、卷类型、任务id 组成的元祖
        """
        req_data = {"data": div_dict} if vol_type in [1, 2] else div_dict
        req_response = self.get_response(url=req_url, method='POST', data=req_data)
        result, r_data = self.check_response(req_response)
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

    def submit_preload_score(self, tea_name, question_item, volume_list):
        """
        正常卷预加载给分
        :param tea_name: 老师名称
        :param question_item: 阅卷数据
        :param volume_list: 卷相关参数列表
        :return:
        """
        volume_type, vol_name, *_, task_url, submit_url = volume_list
        div_alias = question_item.pop('div_alias')
        div_str, div_num = '、'.join(div_alias), len(div_alias)
        self.logger.info(f"[{tea_name}]当前科目有({div_str})等{div_num}个题组需要阅卷")
        while div_alias:
            question_item['itemId'] = div_alias.pop(0)
            encode_list, remain_task = self.div_batch_task(question_item)
            myreq_num, submit_data = len(encode_list), self.query_div_detail(question_item)
            while encode_list:
                encode_info = encode_list.pop(0)
                self.generate_random_score(tea_name, submit_data, encode_info)
                self.req_submit_score(submit_url, submit_data)
                if myreq_num >= remain_task: continue
                task_result = self.div_reques_task(task_url, question_item, vol_type=volume_type)
                if task_result in encode_list or not any(task_result): continue
                with self.lock:
                    encode_list.append(task_result)
                    myreq_num += 1
                time.sleep(1)
            self.logger.info(f"[{tea_name}]-题组【{question_item['itemId']}】阅卷完成")

    def run(self):
        while not self.stop_event.is_set():
            try:
                tea_name, *login_info, self.headers, self.domain = self.t_queue.get()
                exam_data = self.exam_paper_info(login_info)
                volume_info = self.get_volume_info(volume_type=1)
                item = self.get_general_task(tea_name, exam_data, volume_info)
                if not (item and item.get('div_alias')): return
                self.submit_preload_score(tea_name, item, volume_info)
            except queue.Empty:
                continue
            except Exception as e:
                print(f'Error in consumer: {e}')


def main():
    user_account_list = [('17855223366', 'kp147258', '胡林辉一校'), ('17620387002', 'kp147258', '胡林辉二校'),
                         ('17620387001', 'kp147258', '胡林辉二校')]
    mob_queue = queue.Queue()
    for i in user_account_list:
        mob_queue.put(i)
    tea_queue = queue.Queue()
    producers = [Producer(mob_queue, tea_queue, f'Producer-{idx + 1}') for idx in range(len(user_account_list))]
    consumers = [Consumer(tea_queue, f'Consumer-{idx + 1}') for idx in range(len(user_account_list))]
    for producer in producers:
        producer.start()

    for consumer in consumers:
        consumer.start()

    for producer in producers:
        producer.join()

    for consumer in consumers:
        consumer.stop_event.set()
        consumer.join()

    print('All threads have completed.')


if __name__ == '__main__':
    main()
