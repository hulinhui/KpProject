import urllib3
from urllib3.exceptions import InsecureRequestWarning
from QuestionCard.KpRequest.Handle_Logger import HandleLog
from QuestionCard.KpRequest.FormatHeaders import get_format_headers, headers_kp, dict_cover_data, get_content_text
from QuestionCard.KpRequest.NotifyMessage import read_config
from urllib.parse import urlparse
import json
import time
import requests

# 忽略警告
urllib3.disable_warnings(category=InsecureRequestWarning)


class KpLogin:
    def __init__(self):
        self.domain = None
        self.headers = None
        self.kp_data = read_config('KP')
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
                                        params=params,
                                        data=data,
                                        files=files,
                                        verify=False)
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

    def create_login_data(self, login_type='token'):
        kp_token, r_data = self.kp_data.get('kp_token'), None
        self.headers = self.init_headers()
        if login_type == 'token' and kp_token:
            self.headers['Authorization'] = f"Bearer {kp_token}"
            r_data = self.get_user_info()
        if r_data is None:
            r_data = self.account_login()
        return r_data

    def get_user_info(self):
        uinfo_url = self.kp_data['userinfo_url']
        uinfo_resp = self.get_response(url=uinfo_url, method='GET')
        result, r_data = self.check_response(uinfo_resp)
        if result:
            data = r_data and r_data.get('data') or None
            if data is None: return data
            data['users'] = [_ for _ in data['users'] if _['companyId'] == data['orgId']]
            return data
        else:
            error_msg = r_data.get("errorCode") and r_data.get("errorMsg") or '获取响应失败!'
            self.logger.info(error_msg)

    def account_login(self):
        self.headers['Content-Type'] = get_content_text('from')
        login_url = self.kp_data['login_url']
        login_item = {'username': self.kp_data['username'], 'password': self.kp_data['passwd'],
                      'randomStr': '38716_1518792598512', 'code': 'ep3e',
                      'verCode': '', 'grant_type': 'password', 'scope': 'server', 'encrypted': 'false'}
        login_resp = self.get_response(login_url, method='POST', data=dict_cover_data(login_item))
        result, r_data = self.check_response(login_resp)
        if result:
            self.headers['Authorization'] = f"Bearer {r_data.get('access_token')}"
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
            return data['data']
            # return data['data']['name'], data['data']['orgId'], data['data']['orgType'], data['data']['userId']
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
        org_info = self.change_account(data) if valid_account_num > 1 else data if valid_account_num == 1 else (
                self.logger.info('当前账号无有效的机构！') or None)
        info_list = [org_info[key] for key in ['name', 'orgId'] + (keys or [])] if org_info else None
        return info_list

    def get_login_token(self, keys=None):
        """
        登录:
        :return: org_id  机构id
        """
        account_data = self.create_login_data(login_type='token')
        if not account_data: return
        info_list = self.get_org_info(account_data, keys)
        info_list and self.logger.info(f"用户-{info_list.pop(0)}:登录成功!")
        info_data = info_list and info_list[0] if len(info_list) == 1 else info_list
        return info_data


if __name__ == '__main__':
    student = KpLogin()
    aa = student.get_login_token(keys=['orgType', 'orgNo', 'orgName', 'orgLevel'])
    print(aa)
