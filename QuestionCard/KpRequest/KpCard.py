import json
from QuestionCard.KpRequest.KpLogin import KpLogin


class KpCard:
    def __init__(self):
        self.object = KpLogin()
        self.org_id = self.object.get_login_token()

    def find_card_by_name(self, card_name):
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
        card_tuple = self.find_card_by_name(card_name)
        if card_tuple is None or card_tuple[1] != 4:
            self.object.logger.info(f'题卡不满足手阅的条件！')
            return False
        return card_tuple[0]


if __name__ == '__main__':
    card = KpCard()
    card_ids = card.find_card_type('高中物理0829')
    # card_info = card.get_zgt_preview_info(card_ids)
    print(card_ids)
