from api import YouTubeAPI, ZhipuAI
from speech_synthesis import SpeechSynthesizer
from chat_handler import ChatHandler
from action_control import ActionControl
import time

def main():
    youtube_api_key = 'YOUR_YOUTUBE_API_KEY'
    zhipuai_api_key = "YOUR_ZHIPUAI_API_KEY"
    speech_key = "YOUR_SPEECH_KEY"
    speech_region = "YOUR_SPEECH_REGION"

    youtube_api = YouTubeAPI(youtube_api_key)
    zhipuai_api = ZhipuAI(zhipuai_api_key)
    speech_synthesizer = SpeechSynthesizer(speech_key, speech_region)
    action_control = ActionControl()

    chat_handler = ChatHandler(youtube_api, zhipuai_api, speech_synthesizer)

    default_video_id = '7cfEOOSIoJE'
    video_id = input(f"请输入直播视频ID (按Enter使用默认值 {default_video_id}): ")
    if not video_id.strip():
        video_id = default_video_id

    live_chat_id = youtube_api.get_live_chat_id(video_id)
    if live_chat_id:
        last_message_id = None
        page_token = None
        last_message_time = time.time()

        action_control.start_random_action_thread()

        while True:
            live_chat_messages = youtube_api.get_latest_live_chat_message(live_chat_id, page_token)

            if 'items' in live_chat_messages and len(live_chat_messages['items']) > 0:
                latest_message = live_chat_messages['items'][-1]  # 获取最后一条消息
                message_id = latest_message['id']

                if message_id != last_message_id:
                    last_message_id = message_id
                    author = latest_message['authorDetails']['displayName']
                    message_text = latest_message['snippet'].get('displayMessage', '')
                    chat_handler.handle_message(author, message_text)
                    last_message_time = time.time()

            # 更新 page_token
            page_token = live_chat_messages.get('nextPageToken', None)

            # 如果45秒没有弹幕，则调用智谱AI
            if time.time() - last_message_time > 45:
                ai_response = zhipuai_api.get_ai_response("说点什么吧，不要冷场啦")
                if ai_response:
                    action = chat_handler.extract_action(ai_response)
                    filtered_response = chat_handler.filter_response(ai_response)
                    if action:
                        action_control.simulate_keypress(action_control.action_map.get(action, 2))
                    speech_synthesizer.speak_text(filtered_response)
                last_message_time = time.time()

            time.sleep(5)
    else:
        print("Live chat ID not found for the given video ID.")

if __name__ == "__main__":
    main()