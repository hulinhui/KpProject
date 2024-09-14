import json
import requests
from QuestionCard.KpRequest.Handle_Logger import HandleLog
from QuestionCard.KpRequest.FormatHeaders import get_format_headers, headers_kp, dict_cover_data, get_content_text
from QuestionCard.KpRequest.NotifyMessage import read_config
from urllib.parse import urlparse
import json


class StudentZkzhData:
    def __init__(self):
        self.orgid = None
        self.domain = None
        self.kp_data = read_config('KP')
        self.logger = HandleLog()
        self.headers = self.init_headers()

    def init_headers(self):
        self.domain = self.kp_data['test_domain'] if self.kp_data['env_flag'] else self.kp_data['prod_domain']
        header_item = {'Host': urlparse(self.domain).hostname, 'Content-Type': get_content_text('form')}
        headers = get_format_headers(headers_kp, **header_item)
        return headers

    def get_response(self, url, method='GET', params=None, data=None):
        try:
            data = json.dumps(data) if isinstance(data, dict) else data
            response = requests.request(method=method.upper(), url=self.domain + url, headers=self.headers,
                                        params=params,
                                        data=data)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response
        except Exception as e:
            self.logger.info(e)

    @staticmethod
    def check_response(response, return_value=None):
        json_data = {} if response is None else response.json()
        result = json_data['result'] if json_data and 'result' in json_data else False
        if return_value is not None:
            return result
        else:
            return result, json_data

    def get_login_token(self):
        login_url = self.kp_data['login_url']
        login_item = {'username': self.kp_data['username'], 'password': self.kp_data['passwd'],
                      'randomStr': '38716_1518792598512', 'code': 'ep3e',
                      'verCode': '', 'grant_type': 'password', 'scope': 'server', 'encrypted': 'false'}
        login_data = dict_cover_data(login_item)
        login_resp = self.get_response(login_url, method='POST', data=login_data)
        result, data = self.check_response(login_resp)
        if result:
            # self.logger.info(f"用户{self.kp_data['username']}:登录成功!")
            self.headers['Authorization'] = f"Bearer {data.get('access_token')}"
            self.headers['Content-Type'] = get_content_text()
            return data.get('org_id')
        else:
            self.logger.info('用户登录失败')

    def get_school_area(self):
        area_url = self.kp_data['area_url']
        area_params = {'orgId': self.orgid}
        area_resp = self.get_response(area_url, method='GET', params=area_params)
        result, data = self.check_response(area_resp)
        if result:
            school_areaid = data['data'][0]['id']
            return school_areaid
        else:
            self.logger.info('响应数据有误')

    @staticmethod
    def name_cover_code(grade_name):
        cover_func = lambda cn: {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,
                                 '七': 7, '八': 8, '九': 9}.get(cn, 0)
        if len(grade_name) >= 3:
            grade_int = cover_func(grade_name[0])
            if grade_int < 6:
                step_index = 1
            else:
                step_index = 2
            grade_index = grade_int
        else:
            step_index = 3
            grade_index = 9 + cover_func(grade_name[1])
        return str(step_index), str(grade_index)

    def get_grade(self, grade_name):
        step_code, grade_code = self.name_cover_code(grade_name)
        grade_url = self.kp_data['grade_url']
        grade_data = {"data": {"orgId": self.orgid, "includeGrades": 'true'}}
        grade_resp = self.get_response(grade_url, method='POST', data=grade_data)
        result, data = self.check_response(grade_resp)
        if result:
            grade_list = [
                (grade['id'], step_item['id'])
                for step_item in data['data']
                if step_item['code'] == step_code
                for grade in step_item['grades']
                if grade['code'] == grade_code
            ]
            return grade_list[0]
        else:
            self.logger.info('响应数据有误')

    def get_class(self, aid, eid, pid):
        class_url = self.kp_data['class_url']
        class_data = {"type": "1", "schoolAreaId": aid, "gradeId": eid, "stepId": pid}
        response = self.get_response(class_url, method='POST', data=class_data)
        result, data = self.check_response(response)
        if result:
            class_list = [class_item['classId'] for class_item in data['data'] if
                          class_item['className'] == self.kp_data['class_name']]
            return class_list[0]
        else:
            self.logger.info('响应数据有误')

    def get_student_data(self, school_area_id, class_id):
        student_url = self.kp_data['stu_url']
        student_data = {"classId": class_id, "schoolAreaId": school_area_id, "schoolId": self.orgid, "pageSize": 100}
        response = self.get_response(student_url, method='POST', data=student_data)
        result, data = self.check_response(response)
        if result:
            result_data = data.get("data").get("records")
            stu_zkzh_data = [item.get('zkzh') for item in result_data] if result_data else []
            stu_zkzh_data.sort()
            return stu_zkzh_data
        else:
            self.logger.info('响应数据有误')
            return []

    def find_card_by_name(self, card_name):
        card_url = self.kp_data['card_url']
        card_data = {"data": {"name": card_name, "orgId": self.orgid}, "pageSize": 100}
        card_resp = self.get_response(url=card_url, method='POST', data=card_data)
        result, data = self.check_response(card_resp)
        if result:
            card_id = data.get("data")[0].get("cardId")
            card_type = data.get("data")[0].get("cardType")
            return card_id, card_type
        else:
            self.logger.info('响应数据有误')

    @staticmethod
    def process_zgt(zgt):
        score_info = zgt.get('score')
        if zgt.get('type') == 1 or not score_info:
            return None
        return {
            'th': zgt.get('th'),
            'score': score_info['fullMark'],
            'scoreType': score_info['param']['scoreColumnType'],
            'scoreCounts': score_info['param']['scoreCounts'],
            'vals': score_info['param']['vals']
        }

    def get_zgt_preview_info(self, card_id):
        preview_url = self.kp_data['card_preview_url']
        preview_resp = self.get_response(preview_url.format(card_id), method='GET')
        result, data = self.check_response(preview_resp)
        if result:
            card_data = json.loads(data.get("data"))
            card_item = {'card_type': card_data.get("nCardType", 0)}
            paper_list = card_data.get('paperInfo', [])
            for index, paper in enumerate(paper_list, 1):
                question_list = [self.process_zgt(zgt) for zgt in paper.get('zgt', []) if
                                 self.process_zgt(zgt) is not None]
                card_item[f'paper_{index}'] = question_list
            return card_item
        else:
            self.logger.info('响应数据有误')

    def run(self):
        self.orgid = self.get_login_token()
        school_areaid = self.get_school_area()
        grade_tuple = self.get_grade(self.kp_data['grade_name'])
        class_id = self.get_class(school_areaid, *grade_tuple)
        if not (self.orgid and school_areaid and class_id):
            self.logger.info('必要参数获取失败！')
            return
        data = self.get_student_data(school_areaid, class_id)
        return data

    def find_card_type(self, card_name):
        self.orgid = self.get_login_token()
        card_tuple = self.find_card_by_name(card_name)
        if card_tuple is None:
            self.logger.info(f'系统内未找到题卡！')
            return False
        if card_tuple[1] != 4:
            self.logger.info(f'当前题卡不是手阅题卡')
            return False
        return card_tuple[0]


if __name__ == '__main__':
    student = StudentZkzhData()
    card_ids = student.find_card_type('手阅测试题卡')
    card_info = student.get_zgt_preview_info(card_ids)
    print(card_info)
