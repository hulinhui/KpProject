"""
作者: hulinhui6
日期：2025年07月08日
"""
import json


class AdminLogQuery:
    def __init__(self, login):
        self.login = login
        self.login.admin_login()

    def log_query(self):
        log_url = self.login.kp_data['admin_logurl']
        log_data = {"timeMode": 5, "fromTime": "2025-06-30 12:26:57", "endTime": "2025-07-05 20:00:00",
                    "keyword": "杨正祥", "reqBodyKeyword": "/exammark/submitNormalScore", "statusCode": 1,
                    "pageSize": 1000, "pageNo": 1}
        log_response = self.login.get_response(log_url, method='POST', data=log_data)
        result, r_data = self.login.check_response(log_response)
        if result:
            record_list = [record for record in r_data['data']['records']]
            return record_list
        else:
            error_msg = r_data.get("errorCode") and r_data.get("errorMsg") or '获取响应失败!'
            self.login.logger.info(error_msg)

    @staticmethod
    def parse_request(record_list):
        request_datas = list(map(json.loads, [record['requestData'] for record in record_list]))
        requestBody_datas = list(map(json.loads, [request['requestBody'] for request in request_datas]))
        encode_datas = [body['data']['encode'] for body in requestBody_datas]
        return encode_datas

    @staticmethod
    def check_encode(encodes):
        subencode_set = set(encodes)
        with open('李丽妃2.txt', encoding='utf-8') as f:
            sucencode_set = {line.strip() for line in f}
        return sucencode_set.symmetric_difference(subencode_set)

    def run(self):
        record_list = self.log_query()
        encodes = self.parse_request(record_list)
        diff_encode = self.check_encode(encodes)
        print(diff_encode)


if __name__ == '__main__':
    from KpAdmin.AdminLogin import AdminLogin

    adminlog = AdminLogQuery(AdminLogin())
    adminlog.run()
