import requests
from googleapiclient.discovery import build

class YouTubeAPI:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def get_live_chat_id(self, video_id):
        request = self.youtube.videos().list(part='liveStreamingDetails', id=video_id)
        response = request.execute()
        if 'items' in response and len(response['items']) > 0:
            return response['items'][0]['liveStreamingDetails']['activeLiveChatId']
        return None

    def get_latest_live_chat_message(self, live_chat_id, page_token=None):
        request = self.youtube.liveChatMessages().list(
            liveChatId=live_chat_id,
            part='snippet,authorDetails',
            maxResults=1,  # 获取最后一条消息
            pageToken=page_token
        )
        response = request.execute()
        return response

class ZhipuAI:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_ai_response(self, message):
        try:
            session = requests.Session()
            session.trust_env = False  # 忽略环境代理设置
            response = session.post(
                'https://open.bigmodel.cn/api/paas/v4/chat/completions',
                json={
                    "model": "glm-4-flash",
                    "messages": [
                        {"role": "system", "content": "你是虚拟主播..."},
                        {"role": "user", "content": message}
                    ],
                    "top_p": 0.7,
                    "temperature": 0.95,
                    "max_tokens": 128,
                    "tools": [{"type": "web_search", "web_search": {"search_result": True}}],
                    "stream": False,
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            print("zhipuai发生错误：{}".format(e))
            return None
