
from __future__ import print_function
import sys
import io
import yaml

from subprocess import Popen, PIPE, STDOUT

import speech_recognition as sr
from requests_toolbelt.multipart import encoder
from dcs.dcs_client import DcsClient

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

    def run(self):

        audio_in = AudioIO()

        with self._micro as source:
            while True:
                audio_in.smart_truncate()
                #self._rec.adjust_for_ambient_noise(source)

                print("Say something!")
                data = self._rec.listen(source)
                print("Say done!")
                audio_in.append(data.get_raw_data())
                audio_out = self._dcs.echo(audio_in)
                if audio_out:
                    self.play(audio_out)

    def play(self, stream):
        if stream.startswith('http'):
            p = Popen(['mplayer', '-cache', '1024', stream], 
                    stdout=PIPE, stderr=STDOUT)
        else:
            #p = Popen(['mplayer', '-cache', '1024', '-idle', '-slave', '-'], 
            p = Popen(['mplayer', '-cache', '1024', '-'], 
                    stdout=PIPE, stdin=PIPE, stderr=STDOUT)   
            stdout = p.communicate(input=stream)[0]

def main():
    filename = 'config.yaml'
    aikit = AIKit(filename)
    aikit.run()

if __name__ == '__main__':
    main()
