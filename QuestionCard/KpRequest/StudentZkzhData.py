import json
import requests
from QuestionCard.KpRequest.Handle_Logger import HandleLog
from QuestionCard.KpRequest.FormatHeaders import get_format_headers, headers_kp, dict_cover_data, get_content_text
from QuestionCard.KpRequest.NotifyMessage import read_config
from urllib.parse import urlparse


class StudentZkzhData:
    def __init__(self):
        self.domain = None
        self.kp_data = read_config('KP')
        self.headers = self.init_headers()
        self.logger = HandleLog()

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
        result = json_data['success'] if json_data and 'success' in json_data else False
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
            self.logger.info(f"用户{self.kp_data['username']}:登录成功!")
            self.headers['Authorization'] = f"Bearer {data.get('access_token')}"
            self.headers['Content-Type'] = get_content_text()
            return data.get('org_id')
        else:
            self.logger.info('用户登录失败')

    def get_school_area(self, org_id):
        area_url = self.kp_data['area_url']
        area_params = {'orgId': org_id}
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

    def get_grade(self, grade_name, org_id):
        step_code, grade_code = self.name_cover_code(grade_name)
        grade_url = self.kp_data['grade_url']
        grade_data = {"data": {"orgId": org_id, "includeGrades": 'true'}}
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

    def get_student_data(self, school_id, school_area_id, class_id):
        student_url = self.kp_data['stu_url']
        student_data = {"classId": class_id, "schoolAreaId": school_area_id,
                        "schoolId": school_id}
        response = self.get_response(student_url, method='POST', data=student_data)
        result, data = self.check_response(response)
        if result:
            result_data = data.get("data").get("records")
            stu_zkzh_data = [(item.get('zkzh'), item.get('studentName')) for item in result_data] if result_data else []
            return stu_zkzh_data
        else:
            self.logger.info('响应数据有误')
            return []

    def run(self):
        org_id = self.get_login_token()
        school_areaid = self.get_school_area(org_id)
        grade_tuple = self.get_grade(self.kp_data['grade_name'], org_id)
        class_id = self.get_class(school_areaid, *grade_tuple)
        if not (org_id and school_areaid and class_id):
            self.logger.info('必要参数获取失败！')
            return
        data = self.get_student_data(org_id, school_areaid, class_id)
        return data


if __name__ == '__main__':
    student = StudentZkzhData()
    student.run()
