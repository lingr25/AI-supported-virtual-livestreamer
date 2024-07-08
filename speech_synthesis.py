import azure.cognitiveservices.speech as speechsdk

class SpeechSynthesizer:
    def __init__(self, speech_key, region):
        self.speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=region)
        self.audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=self.audio_config
        )
        self.speech_config.speech_synthesis_voice_name = 'zh-CN-XiaoshuangNeural'

    def speak_text(self, text):
        try:
            speech_synthesis_result = self.speech_synthesizer.speak_text_async(text).get()
            if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print("文本 [{}] 的语音已合成。".format(text))
            elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = speech_synthesis_result.cancellation_details
                print("azure发生错误：{}".format(cancellation_details.reason))
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    if cancellation_details.error_details:
                        print("错误详情：{}".format(cancellation_details.error_details))
        except Exception as e:
            print("azure发生错误：{}".format(e))
