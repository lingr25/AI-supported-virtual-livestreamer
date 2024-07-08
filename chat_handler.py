class ChatHandler:
    def __init__(self, youtube_api, zhipuai_api, speech_synthesizer):
        self.youtube_api = youtube_api
        self.zhipuai_api = zhipuai_api
        self.speech_synthesizer = speech_synthesizer

    def handle_message(self, author, message_text):
        print(f"New message from {author}: {message_text}")
        ai_response = self.zhipuai_api.get_ai_response(message_text)
        if ai_response:
            action = self.extract_action(ai_response)
            filtered_response = self.filter_response(ai_response)
            if action:
                self.simulate_keypress(action)
            self.speech_synthesizer.speak_text(filtered_response)
        print(f"AI回复: {ai_response}")

    def filter_response(self, response):
        actions = ["愉悦", "思考", "害羞", "好奇", "卖萌", "惊讶", "快乐", "震惊", "失落"]
        for action in actions:
            response = response.replace(f"【{action}】", "")
        return response

    def extract_action(self, response):
        start = response.find('【')
        end = response.find('】')
        if start != -1 and end != -1:
            return response[start+1:end]
        return None
