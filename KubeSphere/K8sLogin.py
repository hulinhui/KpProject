import base64
import json
import re
from QuestionCard.KpRequest.Handle_Logger import HandleLog
from QuestionCard.KpRequest.NotifyMessage import read_config
from QuestionCard.KpRequest.FormatHeaders import get_format_headers, headers_k8s
import requests
from urllib.parse import quote


class K8sLogin:
    def __init__(self):
        self.config = read_config('KUBESPHERE')
        self.domain = self.config['test_domain']
        self.logger = HandleLog()
        self.headers = get_format_headers(headers_k8s)

    def get_response(self, url, method='GET', params=None, data=None):
        """
        负责请求处理
        :param url: 请求url
        :param method: 请求方法
        :param params: 请求参数，get使用
        :param data: 请求body，post方法使用
        :return: response:请求响应对象
        """
        try:
            data = json.dumps(data) if isinstance(data, (dict, list)) else data
            response = requests.request(method=method.upper(), url=self.domain + url, headers=self.headers,
                                        params=params,
                                        data=data, allow_redirects=False)
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

    def get_login_salt(self, url):
        """
        获取登录页的salt，并对headers设置cookie，无cookie会请求失败
        cooike是请求登录页，自动设置，随时变化
        :param url: 请求登录url，get
        :return: salt_text  加密所需字段
        """
        login_response = self.get_response(url, method='GET')
        self.set_headers_cookie(login_response)
        text = login_response.text if login_response else ''
        match = re.search("var\ssalt\s=\s'(.*?)'", text, re.S)
        salt_text = match.group(1) if match else ''
        return salt_text

    def encrypt_pwd(self, salt):
        """
        密码加密，登录时只需要密码加密后的字符串
        :param salt: 加密字段
        :return: encrypt_pwd: 加密字符串
        """
        pwd_text = self.config['password']
        pwd_enc = base64.b64encode(pwd_text.encode('utf-8')).decode('utf-8')
        if len(pwd_enc) > len(salt):
            salt += pwd_enc[:len(pwd_enc) - len(salt)]
        ret = []
        prefix = []
        for i in range(len(salt)):
            tomix = ord(pwd_enc[i]) if i < len(pwd_enc) else 64
            sum_value = ord(salt[i]) + tomix
            prefix.append('0' if sum_value % 2 == 0 else '1')
            ret.append(chr(sum_value // 2))
        encoded_prefix = base64.b64encode(''.join(prefix).encode('utf-8')).decode('utf-8')
        return encoded_prefix + '@' + ''.join(ret)

    def set_headers_cookie(self, response):
        """
        设置cookies
        :param response: 响应对象
        :return: None
        """
        cookie_list = response.cookies.items() if response else None
        if not cookie_list:
            self.logger.warning('设置登录cookie失败！')
            return
        self.headers['Cookie'] = ';'.join([f'{k}={v}' for k, v in cookie_list])

    def login_send(self, url, encrypt_text):
        """
        登录
        :param url: 登录url，post
        :param encrypt_text: 密码加密串
        :return: None
        """
        login_data = f"username={self.config['account']}&encrypt={quote(encrypt_text)}"
        resposne = self.get_response(url, method='POST', data=login_data)
        if resposne:
            self.logger.info('KubeSpere登录成功!')
            self.set_headers_cookie(resposne)
        else:
            self.logger.warning('KubeSpere登录失败!')

    def login(self):
        """
        1、登录页面获取加密参数salt
        2、密码进行加密返回加密串
        3、使用加密串登录
        :return:
        """
        login_url = self.config['login_url']
        salt_text = self.get_login_salt(login_url)
        if not salt_text:
            self.logger.warning('获取登录页salt失败')
            return
        encrypt_text = self.encrypt_pwd(salt_text)
        self.login_send(login_url, encrypt_text)


if __name__ == '__main__':
    k8s = K8sLogin()
    k8s.login()
