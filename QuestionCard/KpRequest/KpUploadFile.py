from QuestionCard.KpRequest.KpLogin import KpLogin
from QuestionCard.PdfConvertImage import get_file_path, LazyModule


class KpUploadFile:
    def __init__(self, up_type):
        self.login = KpLogin()
        self.logger = self.login.logger
        self.up_list = ['stu', 'lin_stu', 'tea', 'score', 'lin_tea']
        self.upload_type = self._check_type(up_type)

    def _check_type(self, up_type):
        """
        检查上传类型合法性
        :param up_type: 上传类型
        :return: 合法的上传类型
        """
        if not isinstance(up_type, str):
            raise TypeError(f'Type of {up_type} is not str')
        if up_type not in self.up_list:
            raise Exception("上传类型不满足条件")
        return up_type

    def get_exam_data(self, org_id):
        """
        生成上传文件所需参数
        :param org_id: 机构id
        :return: 上传接口参数
        """
        # 调用考试模块对象(传参为登录模块对象)
        KpExam = LazyModule('QuestionCard.KpRequest.KpExam')
        exam, upload_data = KpExam.KpExam(self.login), None
        exam_id = exam.search_exam(org_id)
        if not exam_id: return upload_data
        if self.upload_type in ['stu', 'tea', 'score', 'lin_tea']:
            data = exam.search_paper(exam_id, org_id)
            upload_data = data.update(
                {'absent': 0, 'override': 'false', 'entrance': 1}) if self.upload_type == 'score' else data
        if self.upload_type == 'lin_stu':
            upload_data = exam.exam_detail_query(exam_id)
            CreateTempStu = LazyModule('QuestionCard.KpRequest.CreateTempStu')
            CreateTempStu.GenerateExcelStu().run('3+1+2')
        return upload_data

    def get_upload_info(self, org_id):
        """
        获取上传所需数据
        :param org_id    机构id
        :return: tuple  上传url、上传data、上传文件路径
        """
        # 获取配置信息数据
        data, folder_path = self.login.kp_data, get_file_path('excel')
        # 考试模块获取exam_id及paper_id
        upload_data = self.get_exam_data(org_id)
        upload_item = {
            'stu': (data['upload_stu_url'], upload_data, get_file_path('参考学生导入模板.xlsx', folder_path)),
            'lin_stu': (data['upload_stu_lin_url'], upload_data, get_file_path('临时考生上报模版.xlsx', folder_path)),
            'tea': (data['upload_tea_url'], upload_data, get_file_path('阅卷老师导入模板.xlsx', folder_path)),
            'score': (data['upload_score_url'], upload_data, get_file_path('上传成绩导入模版.xlsx', folder_path)),
            'lin_tea': (data['upload_tea_lin_url'], upload_data, get_file_path('阅卷教师上报模版.xlsx', folder_path))
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
        """
        上传文件
        :return:
        """
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
    uf = KpUploadFile(up_type='lin_stu')
    uf.run()
