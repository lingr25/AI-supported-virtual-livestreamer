from api import YouTubeAPI, ZhipuAI
from speech_synthesis import SpeechSynthesizer
from chat_handler import ChatHandler, LiveChatPoller
from action_control import ActionControl
import os
import sys
import time

REQUIRED_ENV_VARS = ["YOUTUBE_API_KEY", "ZHIPUAI_API_KEY", "AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"]
IDLE_SECONDS = 45
IDLE_PROMPT = "说点什么吧，不要冷场啦"


def load_config():
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        print("缺少环境变量: " + ", ".join(missing))
        print("请先设置这些环境变量后再运行，例如: export YOUTUBE_API_KEY=xxx")
        sys.exit(1)
    return {name: os.environ[name] for name in REQUIRED_ENV_VARS}


def main():
    config = load_config()

    youtube_api = YouTubeAPI(config["YOUTUBE_API_KEY"])
    zhipuai_api = ZhipuAI(config["ZHIPUAI_API_KEY"])
    speech_synthesizer = SpeechSynthesizer(config["AZURE_SPEECH_KEY"], config["AZURE_SPEECH_REGION"])
    action_control = ActionControl()

    chat_handler = ChatHandler(youtube_api, zhipuai_api, speech_synthesizer, action_control)

    default_video_id = '7cfEOOSIoJE'
    video_id = input(f"请输入直播视频ID (按Enter使用默认值 {default_video_id}): ")
    if not video_id.strip():
        video_id = default_video_id
    video_id = video_id.strip()

    live_chat_id = youtube_api.get_live_chat_id(video_id)
    if not live_chat_id:
        print("Live chat ID not found for the given video ID.（该视频可能不在直播中）")
        return

    poller = LiveChatPoller(youtube_api, chat_handler, live_chat_id)
    action_control.start_random_action_thread()

    while True:
        try:
            wait_seconds = poller.poll()
        except Exception as e:
            print("获取弹幕发生错误：{}".format(e))
            wait_seconds = LiveChatPoller.MIN_POLL_INTERVAL

        # 如果45秒没有弹幕，则调用智谱AI
        if time.time() - poller.last_message_time > IDLE_SECONDS:
            ai_response = zhipuai_api.get_ai_response(IDLE_PROMPT)
            if ai_response:
                chat_handler.respond(ai_response)
            poller.last_message_time = time.time()

        time.sleep(wait_seconds)


if __name__ == "__main__":
    main()
