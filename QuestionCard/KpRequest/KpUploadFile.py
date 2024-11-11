from QuestionCard.KpRequest.KpLogin import KpLogin
from QuestionCard.KpRequest.KpExam import KpExam
from QuestionCard.PdfConvertImage import get_file_path


class KpUploadFile:
    def __init__(self, up_type):
        self.login = KpLogin()
        self.logger = self.login.logger
        self.up_list = ['stu', 'tea', 'score']
        self.upload_type = self._check_type(up_type)

    def _check_type(self, up_type):
        if not isinstance(up_type, str):
            raise TypeError(f'Type of {up_type} is not str')
        if up_type not in self.up_list:
            raise Exception("上传类型不满足条件")
        return up_type

    def create_excel_data(self):
        pass

    def get_upload_info(self, org_id):
        """
        获取上传所需数据
        :param org_id    机构id
        :return: tuple  上传url、上传data、上传文件路径
        """
        # 获取配置信息数据
        data = self.login.kp_data
        # 调用考试模块对象(传参为登录模块对象)
        exam = KpExam(self.login)
        # 考试模块获取exam_id及paper_id
        upload_data = exam.get_exam_info(org_id)
        folder_path = get_file_path('excel')
        upload_item = {
            'stu': (data['upload_stu_lin_url'], upload_data, get_file_path('临时考生导入模板.xlsx', folder_path)),
            'tea': (data['upload_tea_url'], upload_data, get_file_path('阅卷老师导入模板.xlsx', folder_path)),
            'score': (data['upload_score_url'], upload_data, get_file_path('上传成绩导入模版.xlsx', folder_path))
        }
        return upload_item.get(self.upload_type, "无效的输入")

    def upload_file(self, upload_tuple):
        """
        通过文件上传发送请求
        :return: None
        """
        # 请求URL、请求data、文件路径file_path(同时使用files和data参数，通常会将data也作为一个字典来传递)
        upload_url, upload_data, file_path = upload_tuple
        # 清除Content-Type字段(files参数会自动帮我们加上Content-Type,如果我传了就会覆盖自动添加的，导致请求失败)
        del self.login.headers['Content-Type']
        # 请求文件对象
        with open(file_path, 'rb') as fp:
            upload_response = self.login.get_response(url=upload_url, method='POST', data=upload_data,
                                                      files={'file': fp})
        result, data = self.login.check_response(upload_response)
        if not result:
            # 接口数据返回失败，一种是接口直接返回（errormsg），另一种是记录到错误提示+
            error_data = data['data']
            # error_data存在则输出错误提示，否则输出errormsg信息
            error_data and [self.logger.info(f'上传失败-->{i["msg"]}--{i["desc"]}') for i in
                            error_data] or self.logger.info(f'上传失败-->{data["errorMsg"]}')
        else:
            # 接口返回成功
            self.logger.info(f'上传成功!')

    def run(self):
        # 登录
        org_id = self.login.get_login_token()
        # 获取上传接口所需data
        upload_tuple = self.get_upload_info(org_id)
        # 判断考试相关参数是否有效
        if upload_tuple[1] is None:
            self.logger.warning('考试信息获取失败！')
            return
        # 上传文件
        self.upload_file(upload_tuple)


if __name__ == '__main__':
    uf = KpUploadFile(up_type='tea')
    uf.run()
