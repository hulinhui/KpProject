"""
作者: hulinhui6
日期：2025年04月16日
注意：运行脚本之前请先配置数据信息：创建考试相关配置及登录账号需为管理员
"""
import time
import random
import string


def config_reminder_decorator(content):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_flag = input(f'请确认参数(例如：{content})是否已设置(输入y or n)：')
            if start_flag.lower() == 'y':
                result = func(*args, **kwargs)
                return result
            else:
                print('请配置好对应的参数再来执行操作吧！')

        return wrapper

    return decorator


class KpCreateExam:
    def __init__(self, l_object):
        self.login_object = l_object
        self.data = self.login_object.kp_data
        self.logger = self.login_object.logger

    def create_org_data(self):
        """
        生成考试所需的机构信息
        :return: org_item 机构信息item
        """
        key_list = ['orgType', 'orgNo', 'orgName', 'mobile', 'userId', 'name', 'orgLevel']
        value_names = self.login_object.get_login_token(key_list)
        key_names = ['orgId'] + key_list[:-1] + ['examLevel']
        org_item = dict(zip(key_names, value_names))
        return org_item

    @staticmethod
    def name_cover_code(grade_name):
        """
        获取学阶代码及年级代码
        学阶code：1、小学 2、初中 3、高中
        年级code：1-9（一到9年级）、10-12（高一、高二、高三）
        :param grade_name:
        :return: step_index，grade_index
        """
        cover_func = lambda cn: {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,
                                 '七': 7, '八': 8, '九': 9}.get(cn, 0)
        if len(grade_name) >= 3:
            grade_int = cover_func(grade_name[0])
            if grade_int <= 6:
                step_index = 1
            else:
                step_index = 2
            grade_index = grade_int
        else:
            step_index = 3
            grade_index = 9 + cover_func(grade_name[1])
        return str(step_index), str(grade_index)

    def get_grade(self, orgid):
        """
        获取年级id、学阶id
        :param orgid: 机构id
        :return: 年级代码，年级信息item（包含年级id、学阶id、机构id）
        """
        grade_name = self.data['e_grade_name']
        step_code, grade_code = self.name_cover_code(grade_name)
        grade_url = self.login_object.kp_data['grade_url']
        grade_data = {"data": {"orgId": orgid, "includeGrades": 'true'}}
        grade_resp = self.login_object.get_response(grade_url, method='POST', data=grade_data)
        result, data = self.login_object.check_response(grade_resp)
        if result:
            grade_list = [(grade['id'], step_item['id']) for step_item in data['data'] if step_item['code'] == step_code
                          for grade in step_item['grades'] if grade['code'] == grade_code]
            grade_id, step_id = grade_list[0]
            grade_item = {'gradeId': grade_id, 'gradeLevelIds': [step_id], 'orgId': orgid}
            return int(grade_code), grade_item
        else:
            self.logger.warning('响应数据有误')
            return None, None

    def exam_map_info(self, org_type):
        """
        根据名称映射到传参对应字段
        :param org_type: 机构类型（教育局还是单校）
        :return: value_list 所需传参的列表
        """
        key_tuple = org_type, self.data['e_model'], self.data['e_numtype'], self.data['e_type'], self.data['e_source']
        info_item = {
            'orgFlag': {1: '联考', 2: '校内考'},
            'examModel': {'普通': 0, '文理分科': 3, '3+1+2新高考': 2, '3+3新高考': 1},
            'numType': {'准考证号': 0, '学号': 1, '学生账号后8位': 2},
            'examType': {'周测': 'WEEKLY_EXAM', '单元': 'UNIT_EXAM', '月考': 'MONTHLY_EXAM', '期中': 'MID_TERM_EXAM',
                         '期末': 'FINAL_EXAM', '模拟': 'MOCK_EXAM', '其他': 'OTHERS_EXAM'},
            'stuSource': {'基础信息': 0, '临时考生': 1}
        }
        value_list = [item.get(key) for item, key in zip(info_item.values(), key_tuple)]
        if org_type == 2: value_list[-1] = 0
        return value_list

    def create_basic_data(self, org_item):
        """
        生成考试所需的考试信息，包含机构信息
        :param org_item: 机构信息字典
        :return: exam_item 返回包含机构信息的字典数据
        """
        org_id, org_type = org_item['orgId'], org_item['orgType']
        edate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        edate_str = edate.translate(str.maketrans('', '', '-: '))
        grade_code, grade_item = self.get_grade(org_id)
        emap_info = self.exam_map_info(org_type)
        exam_item = {"examDate": edate, "examGrade": grade_code, "examModel": emap_info[1], "stuSource": emap_info[4],
                     "examName": f"{emap_info[0] + edate_str}", "examType": emap_info[3], "numType": emap_info[2]}
        exam_item.update(**org_item, **{'gradeinfo': grade_item})
        exam_item['add_red'] = True if self.data['e_from'] == '补录' else None
        return exam_item

    def query_grade_subject(self, grade_item, sub_count=20):
        """
        查询年级科目
        :param grade_item: 年级所需参数
        :param sub_count: 获取科目数量[前n科]
        :return: data 科目数据列表
        """
        subject_url = self.data['subject_url']
        subject_data = {'data': grade_item, 'pageSize': sub_count, 'pageNum': 1}
        subject_response = self.login_object.get_response(url=subject_url, method='POST', data=subject_data)
        result, r_data = self.login_object.check_response(subject_response)
        if result:
            data = r_data and r_data.get('data') or None
            return data
        else:
            self.logger.info('获取响应失败!')

    def query_edu_schools(self, grade_item):
        """
        教育局查询学校
        :param grade_item: 查询参数
        :return: school_list 包含学校id、学校名称的列表
        """
        name_list = self.data['school_name'].split(',')
        school_url = self.data['school_edu_url']
        school_data = {"eduId": grade_item['orgId'], "type": "3", "stepId": grade_item['gradeLevelIds'][0]}
        school_resp = self.login_object.get_response(school_url, method='POST', data=school_data)
        result, data = self.login_object.check_response(school_resp)
        if result:
            school_list = [(school_item['id'], school_item['name']) for school_item in data['data'] if
                           school_item['name'] in name_list]
            return school_list
        else:
            self.logger.warning('响应数据有误')

    def new_class_subject(self, subject_item, sub_count=20, cls_count=20):
        """
        新高考模式查询班级
        :param subject_item: 查询传参
        :param sub_count: 获取科目数量[前n科]
        :param cls_count: 获取班级数量[前n班]
        :return: schoolList 学校班级数据
        """
        class_url = self.data['new_class']
        class_response = self.login_object.get_response(url=class_url, method='POST', data=subject_item)
        result, r_data = self.login_object.check_response(class_response)
        if result:
            sub_data = r_data and r_data.get('data') or None
            schoolList = [{'subjectId': i['subjectId'], 'school_list': [
                {'schoolId': j['schoolId'], 'schoolName': j['schoolName'],
                 'classList': [{'schoolId': j['schoolId'], 'schoolName': j['schoolName'], 'classType': 1, **c} for c in
                               j['classList'][:cls_count]]} for j in i['schoolList']]} for i in sub_data[:sub_count]]
            return schoolList
        else:
            self.logger.info('获取响应失败!')

    def old_class_subject(self, subject_item, cls_count=20):
        """
        普通模式查询班级
        :param subject_item: 科目传参
        :param cls_count: 获取班级数量[前n班]
        :return: data 学校班级数据
        """
        class_url = self.data['old_class']
        class_data = {'data': subject_item, 'pageSize': cls_count, 'pageNum': 1}
        class_response = self.login_object.get_response(url=class_url, method='POST', data=class_data)
        result, r_data = self.login_object.check_response(class_response)
        if result:
            data = r_data and r_data.get('data') or None
            return data
        else:
            self.logger.info('获取响应失败!')

    def get_subject_class(self, b_item, sub_count, cls_count):
        """
        查询科目对应的班级信息及人数
        :param b_item: 考试所需参数item
        :param sub_count: 科目数[前n科]
        :param cls_count: 班级数[前n班]
        :return: schoolList 学校相关数据列表
        """
        emodel, otype, oid, oname = b_item['examModel'], b_item['orgType'], b_item['orgId'], b_item['orgName']
        g_item = b_item.pop('gradeinfo')
        schoolinfos = [(oid, oname)] if otype == 2 else self.query_edu_schools(g_item)
        if emodel > 0:
            schoolIds = [_[0] for _ in schoolinfos]
            subject_item = {'modelType': str(emodel), 'gradeId': g_item['gradeId'], 'schoolIds': schoolIds}
            schoolList = self.new_class_subject(subject_item, sub_count=sub_count, cls_count=cls_count)
        else:
            g_item['gradeLevelId'] = g_item.pop('gradeLevelIds')[0]
            subject_item = g_item | {'classType': 1}
            class_list = self.old_class_subject(subject_item, cls_count=cls_count) if otype == 2 else []
            schoolList = [{'schoolId': _[0], 'schoolName': _[1], 'classList': class_list} for _ in schoolinfos]
        return schoolList

    def create_papers_data(self, exam_item):
        """
        生成考试的papers数据
        :param exam_item: 考试所需参数item
        :return: None
        """
        g, e, i, n = [exam_item[key] for key in ['gradeinfo', 'examModel', 'orgId', 'orgName']]
        a, b, c, d = [exam_item.pop(key) for key in ['mobile', 'userId', 'name', 'add_red']]
        s_count, c_count = int(self.data['s_num']), int(self.data['c_num'])
        subject_list = self.query_grade_subject(g, sub_count=s_count)
        g['subjectId'] = subject_list[0]['subjectId']
        schoolList = self.get_subject_class(exam_item, sub_count=s_count, cls_count=c_count)
        school_item = schoolList if e else [{'subjectId': subject['subjectId'], 'school_list': schoolList} for
                                            subject in subject_list]
        scanner_list = [{"isAdmin": 2, "mobile": a, "orgId": i, "orgName": n, "teacherId": b, "teacherName": c}]
        paper_list = [{'inputRecord': d, 'paperName': s['subjectName'], 'scannerList': scanner_list,
                       'schoolList': v['school_list'], 'subjectList': [s]} for s in subject_list for v in school_item if
                      s['subjectId'] == v['subjectId']]
        exam_item['papers'] = paper_list

    def generate_exam(self, create_data):
        """
        创建考试
        :param create_data: 创建考试data
        :return: exam_id 考试id
        """
        create_url = self.data['create_exam_url']
        create_exam_resp = self.login_object.get_response(url=create_url, method='POST', data=create_data)
        result, r_data = self.login_object.check_response(create_exam_resp)
        if result:
            exam_id = r_data.get("data") or None
            return exam_id
        else:
            self.logger.info('获取响应失败!')

    def send_sms(self, sms_env, paper_id, type_id):
        """
        调用发送验证码接口，获取验证码(正式环境才调这个方法，测试环境不调)
        :param sms_env:  短信运行环境
        :param paper_id: 科目id
        :param type_id: 类型（考试，科目，重评，学生删除等类型）
        :return: verify_code 验证码
        """
        verify_code = ''.join(random.choices(string.digits, k=6))
        if sms_env == 'prod':
            sms_url, sms_mobile = self.data['sendsms_url'], self.data['phone']
            sms_data = {"mobile": sms_mobile, "paperId": paper_id, "type": type_id}
            sms_response = self.login_object.get_response(url=sms_url, method='POST', data=sms_data)
            result, r_data = self.login_object.check_response(sms_response)
            self.logger.info(f'手机号{sms_mobile}-验证码已发送！' if result else r_data['errorMsg'])
            time.sleep(2)
            verify_code = result and input('请输入6位数字验证码：') or verify_code
        return verify_code

    def generate_authcode(self, paper_id, type_id):
        """
        通过正确的验证码，获取授权码
        :param paper_id: 科目id
        :param type_id:  类型（考试，科目，重评，学生删除等类型）
        :return: authcode 授权码
        """
        verify_url, verify_env = self.data['verify_url'], self.data['env_flag']
        verify_code = self.send_sms(verify_env, paper_id, type_id)
        verify_data = {"mobile": self.data['phone'], "paperId": paper_id, "type": type_id, "code": verify_code}
        verify_response = self.login_object.get_response(url=verify_url, method='POST', data=verify_data)
        result, r_data = self.login_object.check_response(verify_response)
        if result:
            authcode = r_data.get("data") or None
            return authcode
        else:
            self.logger.info(r_data.get('errorMsg'))

    def del_exam(self, exam_id, code):
        del_url = self.data['delexam_url']
        del_data = {'data': {'examId': exam_id, 'authCode': code, 'userRoleCodes': ['ROLE_ORG_MANAGER']}}
        del_response = self.login_object.get_response(url=del_url, method='POST', data=del_data)
        result, r_data = self.login_object.check_response(del_response)
        if result:
            self.logger.info('考试删除成功!')
        else:
            self.logger.info('获取响应失败!')

    @config_reminder_decorator(content='考试配置及登录账号')
    def run_create(self):
        """
        1、生成考试所需的机构信息（crate_org_data）
        2、生成考试所需的考试信息（create_basic_data）
        3、生成考试所需的papers信息（create_papers_data）
        4、创建考试（generate_exam）
        :return:
        """
        org_item = self.create_org_data()
        exam_item = self.create_basic_data(org_item)
        self.create_papers_data(exam_item)
        exam_id = self.generate_exam(exam_item)
        self.logger.info(exam_id)
        return exam_id

    @config_reminder_decorator(content='登录账号必须为管理员')
    def run_delete(self, exam_id=None):
        """
        删除考试
        :param exam_id: 考试id
        :return:
        """
        examId = input('请输入需要删除的考试id:') if exam_id is None else exam_id
        # 登录
        self.login_object.get_login_token()
        # 获取授权码
        authcode = self.generate_authcode(examId, 0)
        # 删除考试
        self.del_exam(examId, authcode)


if __name__ == '__main__':
    from KpLogin import KpLogin

    kp_login = KpLogin()
    kce = KpCreateExam(kp_login)
    kce.run_delete()
