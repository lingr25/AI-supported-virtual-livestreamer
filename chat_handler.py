import re
import time

# 匹配任意【...】动作/表情标签
TAG_PATTERN = re.compile(r'【([^【】]*)】')


class ChatHandler:
    def __init__(self, youtube_api, zhipuai_api, speech_synthesizer, action_control):
        self.youtube_api = youtube_api
        self.zhipuai_api = zhipuai_api
        self.speech_synthesizer = speech_synthesizer
        self.action_control = action_control

    def handle_message(self, author, message_text):
        print(f"New message from {author}: {message_text}")
        ai_response = self.zhipuai_api.get_ai_response(message_text)
        if ai_response:
            self.respond(ai_response)
        print(f"AI回复: {ai_response}")

    def respond(self, ai_response):
        """根据AI回复触发动作（如有已知标签）并朗读去掉标签后的文本。"""
        action = self.extract_action(ai_response)
        filtered_response = self.filter_response(ai_response)
        # 只有已知的动作标签才按键，未知标签直接忽略
        if action in self.action_control.action_map:
            self.action_control.simulate_keypress(self.action_control.action_map[action])
        if filtered_response:
            self.speech_synthesizer.speak_text(filtered_response)

    def filter_response(self, response):
        return TAG_PATTERN.sub('', response).strip()

    def extract_action(self, response):
        match = TAG_PATTERN.search(response)
        if match:
            return match.group(1).strip()
        return None


class LiveChatPoller:
    """轮询 YouTube 直播聊天。第一次轮询只记录位置，不回放历史弹幕。"""

    MIN_POLL_INTERVAL = 5  # 秒
    MAX_MESSAGES_PER_POLL = 5  # 每次轮询最多回复的弹幕数（取最新的几条），避免回复积压过久

    def __init__(self, youtube_api, chat_handler, live_chat_id):
        self.youtube_api = youtube_api
        self.chat_handler = chat_handler
        self.live_chat_id = live_chat_id
        self.page_token = None
        self.first_poll = True
        self.seen_ids = set()
        self.last_message_time = time.time()

    def poll(self):
        """拉取一次弹幕并处理新消息，返回建议的下次轮询等待秒数。"""
        response = self.youtube_api.get_latest_live_chat_message(self.live_chat_id, self.page_token)
        items = response.get('items', [])

        new_items = []
        for item in items:
            message_id = item.get('id')
            if message_id in self.seen_ids:
                continue
            self.seen_ids.add(message_id)
            if item.get('snippet', {}).get('type', 'textMessageEvent') != 'textMessageEvent':
                continue
            new_items.append(item)

        if len(self.seen_ids) > 5000:
            self.seen_ids = {item.get('id') for item in items}

        if self.first_poll:
            # 跳过开播前/启动前的历史弹幕
            if new_items:
                print(f"跳过 {len(new_items)} 条历史弹幕")
            self.first_poll = False
        else:
            if len(new_items) > self.MAX_MESSAGES_PER_POLL:
                skipped = len(new_items) - self.MAX_MESSAGES_PER_POLL
                print(f"弹幕过多，跳过较早的 {skipped} 条")
                new_items = new_items[-self.MAX_MESSAGES_PER_POLL:]
            for item in new_items:
                author = item.get('authorDetails', {}).get('displayName', '')
                message_text = item.get('snippet', {}).get('displayMessage', '')
                if not message_text:
                    continue
                self.chat_handler.handle_message(author, message_text)
                self.last_message_time = time.time()

        self.page_token = response.get('nextPageToken', self.page_token)
        interval_ms = response.get('pollingIntervalMillis') or 0
        return max(self.MIN_POLL_INTERVAL, interval_ms / 1000.0)
