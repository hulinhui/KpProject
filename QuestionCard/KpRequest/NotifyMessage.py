import base64
import hashlib
import hmac
import json
import os
import pathlib
import smtplib
import time
import urllib.parse
from configparser import RawConfigParser
from email.header import Header
from email.mime.text import MIMEText

import requests


def read_config(name):
    item_infos = {}
    config = RawConfigParser()
    dir_name = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(dir_name, 'notify.ini')
    if not os.path.exists(file_path):
        pathlib.Path(file_path).touch()  # 创建文件
    config.read(file_path, encoding='utf-8')
    for sec in config.sections():
        item_infos[sec] = {}
        for key, value in config.items(sec):
            item_infos[sec][key] = value
    return item_infos[name]


def get_sign_stamp(webhook_secret):
    timestamp = str(round(time.time() * 1000))
    secret_enc = webhook_secret.encode('utf-8')
    string_to_sign = f'{timestamp}\n{webhook_secret}'
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def get_request_result(url, params, method_type='GET'):
    response_result = None
    headers = {'Content-Type': 'application/json;charset=UTF-8'}
    if method_type.lower() == 'get':
        response_result = requests.get(url, params=params)
        print(response_result.request.url)
    else:
        response_result = requests.post(url, headers=headers, data=json.dumps(params))
    return response_result


def judge_result(response, push_type, response_key, response_code):
    if response is not None:
        if response.status_code == 200:
            try:
                result_data = response.json()
                if str(result_data.get(response_key)).lower() == response_code:
                    print(f'{push_type}消息推送成功！')
                else:
                    print(f'{push_type}消息推送失败！')
            except json.decoder.JSONDecodeError as e:
                print(response.text)
        else:
            print(f'{push_type}推送消息接口请求失败！')
    else:
        print(f'{push_type}无响应结果内容！')


def get_file_text():
    content = ''
    with open(os.path.join(os.path.dirname(__file__), 'log.txt'), encoding='utf-8') as f:
        for line in f:
            content += line + '\n'
    return content


# 钉钉机器人推送
def send_ding(title, mode=1):
    ding_items = read_config()
    message_text = get_file_text()
    webhook_keyword = ding_items['DINGDING']['ding_keyword']
    ding_params = {'msgtype': 'markdown', 'markdown': {'title': f'【{webhook_keyword}】{title}', 'text': message_text}}
    webhook_url_format = ding_items['DINGDING']['ding_url_format']
    if mode:
        webhook_secret = ding_items['DINGDING']['ding_secret']
        ding_timestamp, ding_sign = get_sign_stamp(webhook_secret)
        webhook_url = webhook_url_format.format(ding_items['DINGDING']['ding_webhook_token_two'], ding_timestamp,
                                                ding_sign)
    else:
        webhook_url = webhook_url_format.split('&')[0].format(ding_items['DINGDING']['ding_webhook_token_one'])
    errcode = ding_items['DINGDING']['ding_code_key']
    errcode_result = ding_items['DINGDING']['ding_code']
    push_type = ding_items['DINGDING']['ding_push_type']
    judge_result(get_request_result(webhook_url, ding_params, 'POST'), push_type, errcode, errcode_result)


def send_telegram():
    tg_items = read_config()
    message_text = get_file_text()
    tg_send_url = tg_items['TELEGRAM']['tg_url_format'].format(tg_items['TELEGRAM']['tg_token'])
    tg_params = {"chat_id": tg_items['TELEGRAM']['tg_chat_id'], "text": message_text}
    errcode = tg_items['TELEGRAM']['tg_code_key']
    errcode_result = tg_items['TELEGRAM']['tg_code_status']
    push_type = tg_items['TELEGRAM']['tg_push_type']
    judge_result(get_request_result(tg_send_url, tg_params, 'POST'), push_type, errcode, errcode_result)


def send_pushplus(pp_title):
    pp_items = read_config()
    message_text = get_file_text()
    pp_send_url = pp_items['PUSHPLUS']['pp_url_format']
    pp_params = {"token": pp_items['PUSHPLUS']['pp_token'], "title": pp_title, "content": message_text,
                 "template": "txt"}
    errcode = pp_items['PUSHPLUS']['pp_code_key']
    errcode_result = pp_items['PUSHPLUS']['pp_code_status']
    push_type = pp_items['PUSHPLUS']['pp_push_type']
    judge_result(get_request_result(pp_send_url, pp_params, 'post'), push_type, errcode, errcode_result)


def send_email(title, way_text):
    email_items = read_config()['EMAIL']
    message_text = MIMEText(get_file_text(), 'plain', 'utf-8')
    message_text['From'] = Header(email_items[f'em_{way_text}_sender'])
    message_text['To'] = Header(email_items[f'em_{way_text}_receiver'])
    message_text['Subject'] = Header(title, 'utf-8')
    try:
        smtp = smtplib.SMTP_SSL(email_items[f'em_{way_text}_server'])
        smtp.login(email_items[f'em_{way_text}_sender'], email_items[f'em_{way_text}_passwd'])
        smtp.sendmail(email_items[f'em_{way_text}_sender'], email_items[f'em_{way_text}_receiver'],
                      message_text.as_string())
        smtp.quit()
        print('邮件发送成功！')
    except smtplib.SMTPException as e:
        print(e)
        print('Error: 无法发送邮件')


def send_email_api(title, way_text):
    ea_items = read_config()
    message_text = get_file_text()
    ea_send_url = ea_items['EMAIL']['em_email_url']
    ea_params = {"token": ea_items['EMAIL']['em_email_token'], "title": title, "text": message_text,
                 "to": ea_items['EMAIL'][f'em_{way_text}_receiver']}
    errcode = ea_items['EMAIL']['em_code_key']
    errcode_result = ea_items['EMAIL']['em_code_status']
    push_type = ea_items['EMAIL']['em_push_type']
    judge_result(get_request_result(ea_send_url, ea_params), push_type, errcode, errcode_result)


def send_ServerChan(title):
    sc_items = read_config()
    message_text = get_file_text()
    sc_send_url = sc_items['SERVERCHAN']['sc_url_format'].format(sc_items['SERVERCHAN']['sc_token'])
    sc_params = {"title": title, "desp": message_text}
    errcode = sc_items['SERVERCHAN']['sc_code_key']
    errcode_result = sc_items['SERVERCHAN']['sc_code_status']
    push_type = sc_items['SERVERCHAN']['sc_push_type']
    judge_result(get_request_result(sc_send_url, sc_params), push_type, errcode, errcode_result)


def sendWechat():  # 此方式不支持
    we_items = read_config()
    message_text = get_file_text()
    token_url = we_items['WECHAT']['we_token_url']
    token_params = {"corpid": we_items['WECHAT']['we_corpid'], "corpsecret": we_items['WECHAT']['we_secret']}
    send_params = {"touser": "@all", "msgtype": "text", "agentid": we_items['WECHAT']['we_agentid'],
                   "text": {"content": message_text}, "safe": "0"}
    errcode = we_items['WECHAT']['we_code_key']
    errcode_result = we_items['WECHAT']['we_code_status']
    push_type = we_items['WECHAT']['we_push_type']
    try:
        response = get_request_result(token_url, token_params).json()
        access_token = response.get('access_token')
    except Exception as e:
        print(e)
    else:
        send_url = we_items['WECHAT']['we_url_format'].format(access_token)
        judge_result(get_request_result(send_url, send_params, 'post'), push_type, errcode, errcode_result)


def send_ifttt():
    ft_items = read_config()
    message_text = get_file_text()
    ft_send_url = ft_items['IFTTT']['ft_url_format'].format(ft_items['IFTTT']['ft_event'], ft_items['IFTTT']['ft_key'])
    ft_params = {"value1": message_text}
    errcode = ft_items['IFTTT']['ft_code_key']
    errcode_result = ft_items['IFTTT']['ft_code_status']
    push_type = ft_items['IFTTT']['ft_push_type']
    judge_result(get_request_result(ft_send_url, ft_params, 'post'), push_type, errcode, errcode_result)


def send_qmsg(mode=1):
    qq_items = read_config()
    message_text = get_file_text()
    if mode:
        send_url = qq_items['QMSG']['qq_url_format'].format(qq_items['QMSG']['qq_url_key'])
        params = {'msg': message_text, 'qq': qq_items['QMSG']['qq_code']}
    else:
        send_url = qq_items['QMSG']['qq_group_url_format'].format(qq_items['QMSG']['qq_url_key'])
        params = {'msg': message_text, 'group': qq_items['QMSG']['qq_group_code']}
    errcode = qq_items['QMSG']['qq_code_key']
    errcode_result = qq_items['QMSG']['qq_code_status']
    push_type = qq_items['QMSG']['qq_push_type']
    judge_result(get_request_result(send_url, params=params), push_type, errcode, errcode_result)


if __name__ == '__main__':
    # send_ding('3-19title', 0)
    # send_qmsg()
    # send_telegram()
    # send_pushplus('测试天气消息')
    sendWechat()
