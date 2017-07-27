
from __future__ import print_function
import sys
import io
import yaml
import time

from subprocess import Popen, PIPE, STDOUT

import speech_recognition as sr
from requests_toolbelt.multipart import encoder
from dcs.dcs_client import DcsClient
from player import PlayerManager
from speech import Speech

__author__ = "hyxbiao"
__version__ = "0.0.1"

class AudioIO(encoder.CustomBytesIO):
    pass

class AIKit(object):
    def __init__(self, filename):
        self._conf = yaml.load(open(filename))

        self._rec = sr.Recognizer()
        self._micro = sr.Microphone(sample_rate=16000)

        with self._micro as source:
            self._rec.adjust_for_ambient_noise(source)

        self._dcs = DcsClient(self._conf['dcs'])

        self._player = PlayerManager()

        self._speech = Speech(self._conf['aip'])

    def close(self):
        self._player.close()

    def run(self):

        audio_in = AudioIO()

        with self._micro as source:
            while True:
                audio_in.smart_truncate()
                #self._rec.adjust_for_ambient_noise(source)

                print("Say something!")
                data = self._rec.listen(source)
                print("Say done!")

                raw_audio_data = data.get_raw_data()
                #asr
                text = self._speech.asr(raw_audio_data)
                if text:
                    print("You say: " + text)
                    audio_out = self._speech.synthesis(text)
                    if audio_out is not False:
                        self._player.play(audio_out)

                audio_in.append(raw_audio_data)
                audio_outs = self._dcs.echo(audio_in)
                for audio_out in audio_outs:
                    self._player.play(audio_out)
    def play(self):

        url = "http://om5.alicdn.com/158/7158/2102766631/1795984292_1497581222641.mp3?auth_key=612b618cc7329cbe7f22d901f8821835-1501210800-0-null"
        self._player.play(url)

        time.sleep(30)
        print('next\n')
        url = "http://other.web.rd01.sycdn.kuwo.cn/dba2c10f664aecdcacff356f2bd54f97/59794291/resource/n1/26/46/2405753683.mp3"
        self._player.play(url)

        time.sleep(30)
        print('next\n')
        url = "http://other.web.rd01.sycdn.kuwo.cn/f7841fdf67a3252baf7656331b7a7295/5972035c/resource/n3/27/60/150178036.mp3"
        self._player.play(url)

        time.sleep(30)

def main():
    filename = 'config.yaml'
    aikit = AIKit(filename)
    aikit.run()
    #aikit.play()
    aikit.close()

if __name__ == '__main__':
    main()
