from lxpy import copy_headers_dict

headers_kp = '''
Host: test.local.yjzhixue.com
Authorization: Basic c2NvYmFsYTo4NDEzMTQyMQ==
Connection: keep-alive
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6
'''

headers_k8s = '''
Host: 192.168.0.70:30880
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0
Cookie: ang=zh; currentUser.sig=A9_cBfoHmVg4txmejFMfZM0Fu6I; currentUser=hulinhui; kubesphere:sess.sig=oN62dy8icW9O4J3z7UnCl4TxZhg; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6Imh1bGluaHVpIiwidWlkIjoiNzM0NTBiY2MtMjc5Ni00MjU3LWI1MTUtOTZiOGU5NzIyNTFkIiwidG9rZW5fdHlwZSI6ImFjY2Vzc190b2tlbiIsImV4cCI6MTczNjQyNTU5MCwiaWF0IjoxNzM2NDE4MzkwLCJpc3MiOiJrdWJlc3BoZXJlIiwibmJmIjoxNzM2NDE4MzkwfQ.l5upv6hKxsHZS4G1YsmR2cyyXjZR3SiTeRP4h_rR3oc; expire=1736425600916; refreshToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6Imh1bGluaHVpIiwidWlkIjoiNzM0NTBiY2MtMjc5Ni00MjU3LWI1MTUtOTZiOGU5NzIyNTFkIiwidG9rZW5fdHlwZSI6InJlZnJlc2hfdG9rZW4iLCJleHAiOjE3MzY0MzI3OTAsImlhdCI6MTczNjQxODM5MCwiaXNzIjoia3ViZXNwaGVyZSIsIm5iZiI6MTczNjQxODM5MH0.cgF6BSi8UsPJ_qLLPM8u_IVtYOgh86Vsrv4xxYHless
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
