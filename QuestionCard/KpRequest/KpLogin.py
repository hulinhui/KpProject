import requests
from QuestionCard.KpRequest.Handle_Logger import HandleLog
from QuestionCard.KpRequest.FormatHeaders import get_format_headers, headers_kp, dict_cover_data, get_content_text
from QuestionCard.KpRequest.NotifyMessage import read_config
from urllib.parse import urlparse
import json


class KpLogin:
    def __init__(self):
        self.orgid = None
        self.domain = None
        self.kp_data = read_config('KP')
        self.logger = HandleLog()
        self.headers = self.init_headers()

    def init_headers(self):
        self.domain = [self.kp_data[key] for key in self.kp_data.keys() if key.startswith(self.kp_data['env_flag'])][0]
        header_item = {'Host': urlparse(self.domain).hostname, 'Content-Type': get_content_text('form')}
        headers = get_format_headers(headers_kp, **header_item)
        return headers

    def get_response(self, url, method='GET', params=None, data=None):
        try:
            data = json.dumps(data) if isinstance(data, (dict, list)) else data
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
            self.logger.info(f"用户{data['org_name']}:登录成功!")
            self.headers['Authorization'] = f"Bearer {data.get('access_token')}"
            self.headers['Content-Type'] = get_content_text()
            return data.get('org_id')
        else:
            self.logger.info('用户登录失败')


if __name__ == '__main__':
    student = KpLogin()
    student.get_login_token()
