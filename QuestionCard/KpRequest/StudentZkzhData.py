import json
import requests
from QuestionCard.KpRequest.Handle_Logger import HandleLog
from QuestionCard.KpRequest.FormatHeaders import get_format_headers, headers_kp
from QuestionCard.KpRequest.NotifyMessage import read_config


class StudentZkzhData:
    def __init__(self):
        self.kp_data = read_config('KP')
        self.headers = get_format_headers(headers_kp, 'Authorization', self.kp_data.get('kp_token'))
        self.logger = HandleLog()

    def get_response(self, url, method='GET', data=None):
        try:
            data = json.dumps(data) if data else data
            response = requests.request(method=method.upper(), url=url, headers=self.headers, data=data)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response
        except Exception as e:
            self.logger.info(e)

    @staticmethod
    def check_response(response, return_value=None):
        json_data = {} if response is None else response.json()
        data = json_data['code'] if json_data and 'code' in json_data else 0
        result = True if data == 200 else False
        if return_value is not None:
            return result
        else:
            return result, json_data

    def get_student_data(self):
        student_data = {"classId": "237172308521030611919", "schoolAreaId": "237172283877937703507",
                        "schoolId": "237172283877907003491"}
        response = self.get_response(self.kp_data['kp_stu_url'], method='POST', data=student_data)
        result, data = self.check_response(response)
        if result:
            result_data = data.get("data").get("records")
            stu_zkzh_data = [(item.get('zkzh'), item.get('studentName')) for item in result_data] if result_data else []
            return stu_zkzh_data
        else:
            self.logger.info('响应数据有误')
            return []


if __name__ == '__main__':
    student = StudentZkzhData()
    data = student.get_student_data()
    print(data)
