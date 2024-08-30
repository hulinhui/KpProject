from lxpy import copy_headers_dict

headers_kp = '''
Host: test.local.yjzhixue.com
Connection: keep-alive
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0
Content-Type: application/json;charset=UTF-8
Accept: application/json, text/plain, */*
Accept-Encoding: gzip, deflate, br, zstd
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6
'''


def get_format_headers(text, **kwargs):
    format_headers = copy_headers_dict(text)
    if kwargs:
        format_headers.update(kwargs)
    return format_headers


if __name__ == '__main__':
    headers_item = get_format_headers(headers_kp)
    print(headers_item)
