import requests
from QuestionCard.KpRequest.Handle_Logger import HandleLog
from QuestionCard.KpRequest.FormatHeaders import get_format_headers, headers_kp, dict_cover_data, get_content_text
from QuestionCard.KpRequest.NotifyMessage import read_config
from urllib.parse import urlparse
import json
import time


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
        login_resp = self.get_response(login_url, method='POST', data=dict_cover_data(login_item))
        result, data = self.check_response(login_resp)
        if not result:
            self.logger.info('用户登录失败')
            return
        self.headers['Authorization'] = f"Bearer {data.get('access_token')}"
        self.headers['Content-Type'] = get_content_text()
        org_tuple = self.get_login(data)
        if org_tuple is not None:
            self.logger.info(f"用户-{org_tuple[0]}:登录成功!")
            return org_tuple[1]
        else:
            self.logger.info('用户登录失败')

    def change_account(self, a_data):
        org_name = self.kp_data['org_name']
        account_info = [user for user in a_data['users'] if
                        user.get('companyEnable') and user.get('companyName') == org_name]
        if not account_info:
            self.logger.info(f'机构-{org_name}：没找到!')
            return
        user_url = self.kp_data['user_url']
        user_data = {'accountId': a_data['accountId'], 'randomStr': int(time.time() * 1000),
                     **{key: account_info[0][key] for key in ('userType', 'userId')}}
        user_resp = self.get_response(user_url, method='POST', data=user_data)
        result, data = self.check_response(user_resp)
        if result:
            self.headers['Authorization'] = f"Bearer {data['data']['accessToken']}"
            return data['data']['companyName'], data['data']['companyId']
        else:
            self.logger.info('响应数据有误')

    def get_login(self, data):
        valid_account_num = sum(1 for _ in data['data']['users'] if _.get('companyEnable'))
        if valid_account_num == 1:
            org_info = data['org_name'], data.get('org_id')
        elif valid_account_num > 1:
            org_info = self.change_account(data.get('data'))
        else:
            self.logger.info('当前账号无有效的机构！')
            org_info = None
        return org_info


if __name__ == '__main__':
    student = KpLogin()
    aa = student.get_login_token()
    print(aa)
