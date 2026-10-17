# AI 辅助虚拟主播

读取 YouTube 直播弹幕，调用智谱 AI（glm-4-flash）生成回复，用 Azure 语音合成朗读出来，
并根据回复中的【表情】标签用 pyautogui 模拟按键，触发 VTube Studio 中绑定的表情/动作热键。
45 秒没有弹幕时会主动找话题，另外每 15 秒随机触发一个动作。

## 运行

```bash
pip install -r requirements.txt

export YOUTUBE_API_KEY=你的YouTube Data API密钥
export ZHIPUAI_API_KEY=你的智谱AI密钥
export AZURE_SPEECH_KEY=你的Azure语音密钥
export AZURE_SPEECH_REGION=你的Azure区域   # 例如 eastasia

python main.py
```

Windows（PowerShell）用 `$env:YOUTUBE_API_KEY="..."` 设置环境变量。
启动后输入正在直播的视频 ID（直接回车使用默认值）。启动前已有的历史弹幕不会被回复。

## 表情标签与按键

AI 回复中的标签对应的按键（需要在 VTube Studio 里把热键绑定到这些数字键，并让其窗口能接收按键）：

| 标签 | 按键 | 标签 | 按键 |
|---|---|---|---|
| 【愉悦】 | 2 | 【惊讶】 | 7 |
| 【思考】 | 3 | 【快乐】 | 8 |
| 【害羞】 | 4 | 【震惊】 | 9 |
| 【好奇】 | 5 | 【失落】 | 0 |
| 【卖萌】 | 6 | | |

未知标签不会按键，所有【...】标签在朗读前都会被去掉。系统提示词在 `api.py` 的 `SYSTEM_PROMPT` 中修改。

## 测试

```bash
python -m unittest discover -s tests
```

测试使用桩模块，不需要安装依赖，也不会访问真实 API。
