import json


class KpCard:
    def __init__(self, login_object):
        self.object = login_object
        self.org_id = self.object.org_id

    def find_card_by_name(self, card_name):
        """
        在机构中查找card_name题卡的信息
        :param card_name: 题卡名称
        :return: 题卡id，题卡类型
        """
        card_url = self.object.kp_data['card_url']
        card_data = {"data": {"name": card_name, "orgId": self.org_id}, "pageSize": 100}
        card_resp = self.object.get_response(url=card_url, method='POST', data=card_data)
        result, data = self.object.check_response(card_resp)
        if result:
            card_id = data.get("data")[0].get("cardId")
            card_type = data.get("data")[0].get("cardType")
            return card_id, card_type
        else:
            self.object.logger.info('响应数据有误')

    @staticmethod
    def process_zgt(zgt):
        """
        从主观题item中筛选出有用的数据，组成字典
        :param zgt: 主观题信息
        :return: 单题信息
        """
        score_info = zgt.get('score')
        if zgt.get('type') == 1 or not score_info:
            return None
        return {
            'th': zgt.get('th'),
            'score': score_info['fullMark'],
            'scoreType': score_info['param']['scoreColumnType'],
            'scoreCounts': score_info['param']['scoreCounts'],
            'vals': score_info['param']['vals']
        }

    def get_zgt_preview_info(self, card_id):
        """
        获取题卡预览信息-解答题信息（定位点及分数）
        :param card_id: 题卡id
        :return: card_item 解答题信息
        """
        preview_url = self.object.kp_data['card_preview_url']
        preview_resp = self.object.get_response(preview_url.format(card_id), method='GET')
        result, data = self.object.check_response(preview_resp)
        if result:
            card_data = json.loads(data.get("data"))
            card_item = {'card_type': card_data.get("nCardType", 0)}
            paper_list = card_data.get('paperInfo', [])
            for index, paper in enumerate(paper_list, 1):
                question_list = [self.process_zgt(zgt) for zgt in paper.get('zgt', []) if
                                 self.process_zgt(zgt) is not None]
                card_item[f'paper_{index}'] = question_list
            return card_item
        else:
            self.object.logger.info('响应数据有误')

    def find_card_type(self, card_name):
        """
        1、登录操作
        2、查询题卡信息（题卡id及题卡类型）
        3、判断题卡id及题卡类型
        :param card_name: 题卡名称
        :return: 题卡id
        """
        if self.object.org_id is None: self.object.get_login_token()
        card_tuple = self.find_card_by_name(card_name)
        if card_tuple is None or card_tuple[1] != 4:
            self.object.logger.info(f'题卡不满足手阅的条件！')
            return False
        return card_tuple[0]


if __name__ == '__main__':
    from QuestionCard.KpRequest.KpLogin import KpLogin

    KpLogin = KpLogin()
    card = KpCard(KpLogin)
    card_ids = card.find_card_type('高中数学20250306165618')
    # card_info = card.get_zgt_preview_info(card_ids)
    print(card_ids)
