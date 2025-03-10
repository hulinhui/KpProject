import base64
import json
import re
import time

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
        self.headers = None

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
        self.headers = get_format_headers(headers_k8s)
        login_response = self.get_response(url)
        text, cookie_item = (login_response.text, login_response.cookies) if login_response else ('', {})
        cookie_str = ';'.join([f'{k}={v}' for k, v in cookie_item.items()]) if cookie_item else ''
        match = re.search("var\ssalt\s=\s'(.*?)'", text, re.S)
        salt_text = match.group(1) if match else ''
        return salt_text, cookie_str

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

    def login_send(self, url, salt_text):
        """
        登录
        :param url: 登录url，post
        :param salt_text: 加密参数salt
        :return: 登录后的cookie字符串
        """
        encrypt_text = self.encrypt_pwd(salt_text)
        login_data = f"username={self.config['account']}&encrypt={quote(encrypt_text)}"
        self.headers['Content-Type'] = get_content_text(flag=True)
        response = self.get_response(url, method='POST', data=login_data)
        if response:
            self.logger.info('KubeSpere-account登录成功✅!')
            login_cookie_str = ';'.join([f'{k}={v}' for k, v in response.cookies.items()])
            return login_cookie_str
        else:
            self.logger.warning('KubeSpere登录失败❌!')

    @staticmethod
    def check_valid_cookie():
        """
        判断cookie是否过期，是否有效
        :return:
        """
        match = re.search('expire=(\d+);', headers_k8s, re.S)
        expire_stamp = int(int(match.group(1))) / 1000 if match else 0
        expire_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expire_stamp))
        state = True if expire_stamp > int(time.time()) else False
        return state, expire_time

    def login(self):
        """
        1、判断请求头中是否存在cookie，判断cookie是否过期，过期执行登录，未过期跳过登录
        2、登录页面获取加密参数salt和cookie字符串
        3、设置cookie给登录接口使用及加密操作
        4、使用加密串登录，登录成功设置登录后的cookie
        :return:
        """
        state, expire_time = self.check_valid_cookie()
        if not state:
            login_url = self.config['login_url']
            salt_text, cookie_str = self.get_login_salt(login_url)
            if not (salt_text and cookie_str):
                self.logger.warning('获取登录页salt失败')
                return
            self.headers['Cookie'] = cookie_str
            login_cookie = self.login_send(login_url, salt_text)
            self.headers['Cookie'] = login_cookie
        else:
            self.logger.info(f'KubeSpere-cookie登录成功✅->cookie有效期至:{expire_time}')
            self.headers = get_format_headers(headers_k8s)
        self.headers['Content-Type'] = get_content_text()

    def get_workspaces(self, ws_name):
        """
        判断测试空间是否存在
        :param ws_name: 空间名称
        :return: bool 存在标记
        """
        ws_url = self.config['ws_url']
        ws_resp = self.get_response(ws_url, method='GET')
        r_data = self.check_response(response=ws_resp)
        exist_flag = bool(r_data) and any(_['metadata']['name'] == ws_name for _ in r_data)
        return exist_flag

    def get_devops_id(self, ws_name):
        """
        根据空间名称获取需要运行的工程id
        :param ws_name: 空间名称
        :return: [dev_id] 工程id组成的列表
        """
        dev_url, dev_str = self.config['dev_url'].format(ws_name), self.config['dev_name']
        dev_names = dev_str.split(',') if ',' in dev_str else [dev_str]
        dev_resp = self.get_response(dev_url, method='GET')
        r_data = self.check_response(response=dev_resp)
        dev_ids = [i['metadata']['name'] for i in r_data if
                   i['metadata']['annotations']['kubesphere.io/alias-name'] in dev_names] if r_data else []
        return dev_ids

    def get_issuer_params(self):
        """
        获取运行流水线的必要请求头参数
        :return:
        """
        issuer_url = self.config['issuer_url']
        issuer_resp = self.get_response(issuer_url, method='GET')
        r_data = {} if issuer_resp is None else issuer_resp.json()
        params_data = {r_data['crumbRequestField']: r_data['crumb']} if r_data else {}
        return params_data

    def pipename_format(self):
        """
        格式化为正确的流水线名称
        :return:
        """
        pipe_str = self.config['pipe_name']
        name_list = pipe_str.split(',') if ',' in pipe_str else [pipe_str]
        pipe_names = list(
            map(lambda s: f"{s.split('_')[1]}-nginx" if s.startswith('pre_') else f'kp-exam-{s}', name_list))
        return pipe_names

    def get_pipelines(self, devops_id, env):
        """
        查询工程下运行流水线的名称及运行参数
        :param devops_id: 工程id
        :param env: 推送镜像环境
        :return: ｛流水线名称:运行参数列表｝
        """
        pipe_url, pipe_names = self.config['pipe_url'], self.pipename_format()
        pipe_reparams = {'start': 0, 'limit': 20,
                         'q': f'type:pipeline;organization:jenkins;pipeline:{devops_id}/*;excludedFromFlattening'
                              f':jenkins.branch.MultiBranchProject,hudson.matrix.MatrixProject&filter=no-folders'}
        pipe_resp = self.get_response(pipe_url, method='GET', params=pipe_reparams)
        pipe_items = [] if pipe_resp is None else pipe_resp.json().get('items', [])
        filtered_items = [item for item in pipe_items if item['name'] in pipe_names]
        pipe_params = [[{k: str(v) if v or env == 'test' else 'True' for k, v in param['defaultParameterValue'].items()
                         if k != '_class'} for param in items['parameters']] for items in filtered_items]
        pipe_names = [item['name'] for item in filtered_items]
        pipe_info = dict(zip(pipe_names, pipe_params))
        return pipe_info

    def print_run_info(self, info):
        """
        打印流水线运行参数
        :param info: 流水线信息
        :return: 流水线名称，运行参数，版本号
        """
        p_name, p_parameters = info
        p_parameters = p_parameters[:2] + [p_parameters.pop()] + p_parameters[2:] if p_parameters and p_parameters[
            2].get('name') == 'push_aliyuncs' else p_parameters
        branch_name, version, deployed, push_aliyuncs = [_['value'] for _ in p_parameters]
        test_flag = '✅' if deployed == 'True' else '❌'
        prod_flag = '✅' if push_aliyuncs == 'True' else '❌'
        self.logger.info(
            f'开始运行流水线-->【{p_name}:{branch_name}:{version}】,测试环境：{test_flag},线上环境：{prod_flag}')
        return p_name, p_parameters, version

    def run_pipe(self, dev_id, p_info):
        """
        运行单个流水线
        :param dev_id: devops工程id
        :param p_info: （流水线名称,运行参数）
        :return:
        """
        p_name, p_parameters, version = self.print_run_info(p_info)
        run_url = self.config['run_url'].format(dev_id, p_name)
        run_resp = self.get_response(url=run_url, method='POST', data={"parameters": p_parameters})
        r_data = {} if run_resp is None else run_resp.json()
        if r_data:
            version_no = f"{p_name}:{version}.{r_data['id']}"
            self.logger.info(f"{p_name}:运行成功✅！--->版本号为：{version_no}")
        else:
            self.logger.warning(f'{p_name}:运行失败❌')

    def run(self):
        """
        1、k8s流水线登录
        2、查询企业空间是否存在
        3、查询devops工程是否存在
        4、循环遍历devops工程
        5、循环遍历devops工程下的流水线
        :return:
        """
        self.login()
        ws_name, env_name = self.config['ws_name'], self.config['env_name']
        if not self.get_workspaces(ws_name):
            self.logger.warning(f'企业空间-｛ws_name｝：名称不存在!')
            return
        dev_ids = self.get_devops_id(ws_name)
        if not dev_ids:
            self.logger.warning(f'devops工程未找到！')
            return
        self.headers.update(self.get_issuer_params())
        for dev_id in dev_ids:
            pipe_info = self.get_pipelines(dev_id, env_name)
            if not pipe_info: continue
            for p_info in pipe_info.items():
                self.run_pipe(dev_id, p_info)


if __name__ == '__main__':
    k8s = K8sLogin()
    k8s.run()
