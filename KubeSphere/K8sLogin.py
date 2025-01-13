import base64
import json
import re
from QuestionCard.KpRequest.Handle_Logger import HandleLog
from QuestionCard.KpRequest.NotifyMessage import read_config
from QuestionCard.KpRequest.FormatHeaders import get_format_headers, headers_k8s, get_content_text
import requests
from urllib.parse import quote


class K8sLogin:
    def __init__(self):
        self.config = read_config(name='KUBESPHERE')
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
    def check_response(response, key='items'):
        """
        处理响应内容，进行响应结果判断
        :param key:
        :param response: 请求响应对象
        :return: result, json_data
        """
        json_data = {} if response is None else response.json()
        result = json_data['totalItems'] if json_data and 'totalItems' in json_data else False
        key_data = json_data.get(key, []) if result else []
        return key_data

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
        self.headers['Content-Type'] = get_content_text(flag=True)
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

    def users(self):
        user_url = self.config['user_url']
        user_resp = self.get_response(user_url, method='GET')
        result, r_data = self.check_response(user_resp)
        print(r_data)
        if result:
            print(r_data)
        else:
            self.logger.warning('获取数据失败!')

    def run_pipe(self, dev_id, p_info):
        p_name, p_parameters = p_info
        run_url = self.config['run_url'].format(dev_id, p_name)
        run_data = {"parameters": p_parameters}
        run_resp = self.get_response(url=run_url, method='POST', data=run_data)
        r_data = {} if run_resp is None else run_resp.json()
        if r_data:
            self.logger.info(f"{p_name}:运行成功！--->序号为：{r_data['id']}")
        else:
            self.logger.warning(f'{p_name}:运行失败')

    def get_issuer_params(self):
        issuer_url = self.config['issuer_url']
        issuer_resp = self.get_response(issuer_url, method='GET')
        r_data = {} if issuer_resp is None else issuer_resp.json()
        params_data = {r_data['crumbRequestField']: r_data['crumb']} if r_data else {}
        return params_data

    def get_pipelines(self, devops_id):
        pipe_url, pipe_names = self.config['pipe_url'], self.config['pipe_name'].split(',')
        pipe_reparams = {'start': 0, 'limit': 20,
                         'q': f'type:pipeline;organization:jenkins;pipeline:{devops_id}/*;excludedFromFlattening'
                              f':jenkins.branch.MultiBranchProject,hudson.matrix.MatrixProject&filter=no-folders'}
        pipe_resp = self.get_response(pipe_url, method='GET', params=pipe_reparams)
        json_data = {} if pipe_resp is None else pipe_resp.json()
        pipe_items = json_data.get('items', [])
        filtered_items = [item for item in pipe_items if item['name'] in pipe_names]
        pipe_params = [[{k: str(v) for k, v in param['defaultParameterValue'].items() if k != '_class'} for param in
                        items['parameters']] for items in filtered_items]
        pipe_names = [item['name'] for item in filtered_items]
        pipe_info = dict(zip(pipe_names, pipe_params))
        return pipe_info

    def get_devops_id(self, ws_name):
        dev_url, dev_names = self.config['dev_url'].format(ws_name), self.config['dev_name'].split(',')
        dev_resp = self.get_response(dev_url, method='GET')
        r_data = self.check_response(response=dev_resp)
        dev_ids = [i['metadata']['name'] for i in r_data if
                   i['metadata']['annotations']['kubesphere.io/alias-name'] in dev_names] if r_data else []
        return dev_ids

    def get_workspaces(self, ws_name):
        ws_url = self.config['ws_url']
        self.headers['Content-Type'] = get_content_text()
        ws_resp = self.get_response(ws_url, method='GET')
        r_data = self.check_response(response=ws_resp)
        exist_flag = bool(r_data) and any(_['metadata']['name'] == ws_name for _ in r_data)
        return exist_flag

    def run(self):
        cookies_str = self.headers.get('Cookie', None)
        if not cookies_str: self.login()
        ws_name = self.config['ws_name']
        if not self.get_workspaces(ws_name):
            self.logger.warning(f'企业空间-｛ws_name｝：名称不存在!')
            return
        dev_ids = self.get_devops_id(ws_name)
        if not dev_ids:
            self.logger.warning(f'devops工程未找到！')
            return
        self.headers.update(self.get_issuer_params())
        for dev_id in dev_ids:
            pipe_info = self.get_pipelines(dev_id)
            if not pipe_info: continue
            for p_info in pipe_info.items():
                self.run_pipe(dev_id, p_info)


if __name__ == '__main__':
    k8s = K8sLogin()
    k8s.run()
