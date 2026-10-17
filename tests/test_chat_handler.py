"""离线单元测试：用 sys.modules 桩替换 pyautogui / googleapiclient / azure 等依赖，无需显示器和真实 API。

运行: python3 -m unittest discover -s tests
"""
import os
import sys
import types
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# 桩模块（依赖可能未安装，且测试环境没有显示器）
sys.modules.setdefault('pyautogui', mock.MagicMock())
sys.modules.setdefault('requests', mock.MagicMock())
_gac = types.ModuleType('googleapiclient')
_gac.discovery = mock.MagicMock()
sys.modules.setdefault('googleapiclient', _gac)
sys.modules.setdefault('googleapiclient.discovery', _gac.discovery)
_azure = mock.MagicMock()
for name in ('azure', 'azure.cognitiveservices', 'azure.cognitiveservices.speech'):
    sys.modules.setdefault(name, _azure)

from action_control import ActionControl  # noqa: E402
from chat_handler import ChatHandler, LiveChatPoller  # noqa: E402


def make_item(i, text=None):
    return {
        'id': f'msg{i}',
        'snippet': {'type': 'textMessageEvent', 'displayMessage': text or f'弹幕{i}'},
        'authorDetails': {'displayName': f'user{i}'},
    }


class ChatHandlerTest(unittest.TestCase):
    def setUp(self):
        self.zhipu = mock.Mock()
        self.speech = mock.Mock()
        self.action = ActionControl()
        self.action.simulate_keypress = mock.Mock()
        self.handler = ChatHandler(mock.Mock(), self.zhipu, self.speech, self.action)

    def test_known_tag_presses_key_and_speaks_without_tag(self):
        self.zhipu.get_ai_response.return_value = '【害羞】谢谢你的夸奖~'
        self.handler.handle_message('user', '你好可爱')
        self.action.simulate_keypress.assert_called_once_with(4)
        self.speech.speak_text.assert_called_once_with('谢谢你的夸奖~')

    def test_unknown_tag_is_stripped_and_no_keypress(self):
        self.zhipu.get_ai_response.return_value = '【生气】哼！【开心】'
        self.handler.handle_message('user', 'hi')
        self.action.simulate_keypress.assert_not_called()
        self.speech.speak_text.assert_called_once_with('哼！')

    def test_no_ai_response(self):
        self.zhipu.get_ai_response.return_value = None
        self.handler.handle_message('user', 'hi')
        self.action.simulate_keypress.assert_not_called()
        self.speech.speak_text.assert_not_called()


class LiveChatPollerTest(unittest.TestCase):
    def test_backlog_skipped_then_new_messages_processed_in_order(self):
        yt = mock.Mock()
        yt.get_latest_live_chat_message.side_effect = [
            {'items': [make_item(1), make_item(2)], 'nextPageToken': 'p1', 'pollingIntervalMillis': 2000},
            {'items': [make_item(3), make_item(4)], 'nextPageToken': 'p2', 'pollingIntervalMillis': 8000},
            {'items': [], 'nextPageToken': 'p3'},
        ]
        handler = mock.Mock()
        poller = LiveChatPoller(yt, handler, 'chat')

        self.assertEqual(poller.poll(), 5)  # max(5s, 2s)
        handler.handle_message.assert_not_called()  # 历史弹幕不回放

        self.assertEqual(poller.poll(), 8)  # max(5s, 8s)
        self.assertEqual(
            [c.args for c in handler.handle_message.call_args_list],
            [('user3', '弹幕3'), ('user4', '弹幕4')],
        )
        self.assertEqual(poller.poll(), 5)
        self.assertEqual(handler.handle_message.call_count, 2)
        tokens = [c.args[1] for c in yt.get_latest_live_chat_message.call_args_list]
        self.assertEqual(tokens, [None, 'p1', 'p2'])

    def test_duplicate_ids_not_reprocessed(self):
        yt = mock.Mock()
        yt.get_latest_live_chat_message.side_effect = [
            {'items': [], 'nextPageToken': 'p1'},
            {'items': [make_item(1)], 'nextPageToken': 'p2'},
            {'items': [make_item(1)], 'nextPageToken': 'p3'},
        ]
        handler = mock.Mock()
        poller = LiveChatPoller(yt, handler, 'chat')
        for _ in range(3):
            poller.poll()
        handler.handle_message.assert_called_once_with('user1', '弹幕1')

    def test_flood_capped_to_latest(self):
        yt = mock.Mock()
        yt.get_latest_live_chat_message.side_effect = [
            {'items': [], 'nextPageToken': 'p1'},
            {'items': [make_item(i) for i in range(20)], 'nextPageToken': 'p2'},
        ]
        handler = mock.Mock()
        poller = LiveChatPoller(yt, handler, 'chat')
        poller.poll()
        poller.poll()
        authors = [c.args[0] for c in handler.handle_message.call_args_list]
        self.assertEqual(authors, [f'user{i}' for i in range(15, 20)])


class GetLiveChatIdTest(unittest.TestCase):
    def test_not_live_returns_none(self):
        import api
        yt = api.YouTubeAPI.__new__(api.YouTubeAPI)
        yt.youtube = mock.Mock()
        yt.youtube.videos().list().execute.return_value = {'items': [{'id': 'x'}]}
        self.assertIsNone(yt.get_live_chat_id('x'))
        yt.youtube.videos().list().execute.return_value = {'items': [{'liveStreamingDetails': {}}]}
        self.assertIsNone(yt.get_live_chat_id('x'))
        yt.youtube.videos().list().execute.return_value = {
            'items': [{'liveStreamingDetails': {'activeLiveChatId': 'abc'}}]}
        self.assertEqual(yt.get_live_chat_id('x'), 'abc')


class MainConfigTest(unittest.TestCase):
    def test_missing_env_exits(self):
        import main
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                main.load_config()


if __name__ == '__main__':
    unittest.main()
