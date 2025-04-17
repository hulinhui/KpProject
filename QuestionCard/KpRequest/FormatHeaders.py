from lxpy import copy_headers_dict

headers_kp = '''
Host: test.yjzhixue.com
Authorization: Basic c2NvYmFsYTo4NDEzMTQyMQ==
Connection: keep-alive
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6
'''

headers_k8s = '''
Host: 192.168.0.70:30880
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0
Cookie: lang=zh; currentUser=hulinhui; currentUser.sig=A9_cBfoHmVg4txmejFMfZM0Fu6I; kubesphere:sess.sig=RQc1aewbsFxFF2XfXwKb4n3yxTs; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6Imh1bGluaHVpIiwidWlkIjoiNzM0NTBiY2MtMjc5Ni00MjU3LWI1MTUtOTZiOGU5NzIyNTFkIiwidG9rZW5fdHlwZSI6ImFjY2Vzc190b2tlbiIsImV4cCI6MTc0NDY5NDA0NCwiaWF0IjoxNzQ0Njg2ODQ0LCJpc3MiOiJrdWJlc3BoZXJlIiwibmJmIjoxNzQ0Njg2ODQ0fQ.h3KSgt4YwYNz5H90NWkMQXEJ34ched4Nwmw26fL56lE; expire=1744694054186; refreshToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6Imh1bGluaHVpIiwidWlkIjoiNzM0NTBiY2MtMjc5Ni00MjU3LWI1MTUtOTZiOGU5NzIyNTFkIiwidG9rZW5fdHlwZSI6InJlZnJlc2hfdG9rZW4iLCJleHAiOjE3NDQ3MDEyNDQsImlhdCI6MTc0NDY4Njg0NCwiaXNzIjoia3ViZXNwaGVyZSIsIm5iZiI6MTc0NDY4Njg0NH0.ZFON5E8i4tCRj8YX_Bl3ECU5LMhSjnSZT1JNtIOGOi4
'''


def get_format_headers(text, **kwargs):
    format_headers = copy_headers_dict(text)
    if kwargs:
        format_headers.update(kwargs)
    return format_headers


def dict_cover_data(item):
    return '&'.join(f'{key}={value}' for key, value in item.items())


def get_content_text(flag=None):
    text = 'application/{}'
    return text.format('json') if flag is None else text.format('x-www-form-urlencoded')


if __name__ == '__main__':
    headers_item = get_format_headers(headers_kp)
    print(headers_item)
