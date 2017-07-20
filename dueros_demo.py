
from __future__ import print_function
import sys
import io
sys.path.insert(0, '/Users/hyxbiao/dep/github/http/hyper')
import requests

from hyper.contrib import HTTP20Adapter
from hyper import HTTPConnection
from hyper import HTTP20Connection
from requests_toolbelt.multipart import encoder
from requests_toolbelt.multipart import decoder
import sounddevice as sd
import speech_recognition as sr
from subprocess import Popen, PIPE, STDOUT
import Queue

import json

class TimeOutHTTP20Adapter(HTTP20Adapter):
    def __init__(self, timeout = 5):
        super(TimeOutHTTP20Adapter, self).__init__()
        self.timeout = timeout

    def get_connection(self, host, port, scheme, cert=None):
        conn = super(TimeOutHTTP20Adapter, self).get_connection(host, port, scheme, cert)
        if conn._sock:
            conn._sock.settimeout(self.timeout)
        return conn

class AudioIO2(io.RawIOBase):
    def __init__(self):
        self._q = Queue.Queue()

    def read(self, size=-1):
        buf = b""
        while size == -1 or len(buf) < size:
            try:
                data = self._q.get_nowait()
            except queue.Empty:
                break
            buf += data
        return buf

    def write(self, b):
        self._q.put(b)


class AudioIO(encoder.CustomBytesIO):
    def __init__(self, size=1024):
        super(AudioIO, self).__init__()
        self._size = size
        #self._q = Queue.Queue()
        #self._left = b""

    @property
    def qlen(self):
        #hack
        return 1

    def empty(self):
        return self._q.empty()

    def full(self):
        return self.len() > self._size

    def qread(self, size=-1):
        buf = self._left
        while size == -1 or len(buf) < size:
            try:
                data = self._q.get_nowait()
            except queue.Empty:
                break
            if len(buf) + len(data) > size:
                left_size = size - len(buf)
                buf += data[:left_size]
                self._left = data[left_size:]
            else:
                buf += data
        return buf

    def qwrite(self, b):
        self._q.put(b)

audio = AudioIO()

def gen(m):
    while not audio.empty():
        yield m.read()

def create():
    conn = HTTP20Connection(
            'dueros-h2.baidu.com:443'
            )
    headers = {
        'authorization': 'Bearer 23.0e617b06679ee45113810a4252139a71.2592000.1502932213.151016915-9892205',
        'dueros-device-id': 'hyxbiao-smart',
    }
    create = conn.request('GET', '/dcs/v1/directives', headers=headers)
    resp = conn.get_response(create)

    print (resp.status)

    print(resp.read())

def post_callback(monitor):
    pass

def event(audio_data):
    metadata = {
        'clientContext': [],
        'event': {},
    }
    metadata['event']['header'] = {
        "namespace" : "ai.dueros.device_interface.voice_input",
        "name" : "ListenStarted",
        "messageId" : "71c0cf96-6243-4fff-853d-7d63ef4123dd",
        "dialogRequestId" : "e5c713d0-f5ec-48c6-89bf-a023c38512d7"
    }
    metadata['event']['payload'] = {
        "format" : "AUDIO_L16_RATE_16000_CHANNELS_1"
    }
    metadata['clientContext'] = [{
        "header" : {
            "namespace" : "ai.dueros.device_interface.audio_player",
            "name" : "PlaybackState"
        },
        "payload" : {
            "token" : "",
            "offsetInMilliseconds" : 0,
            "playerActivity" : "IDLE"
        }
    }, {
        "header" : {
            "namespace" : "ai.dueros.device_interface.voice_output",
            "name" : "SpeechState"
        },
        "payload" : {
            "token" : "",
            "offsetInMilliseconds" : 0,
            "playerActivity" : "FINISHED"
        }
    }, {
        "header" : {
            "namespace" : "ai.dueros.device_interface.alerts",
            "name" : "AlertsState"

        },
        "payload" : {
            "allAlerts" : [ ],
            "activeAlerts" : [ ]
        }
    }, {
        "header" : {
            "namespace" : "ai.dueros.device_interface.speaker_controller",
            "name" : "VolumeState"
        },
        "payload" : {
            "volume" : 50,
            "muted" : False
        }
    }]
    meta = json.dumps(metadata)

    files = {
        'metadata': (None, meta, 'application/json; charset=UTF-8', None),
        'audio': (None, audio_data),
    }
    multiple_files = [
        ('metadata', ('metadata', meta, 'application/json; charset=UTF-8')),
        ('audio', ('audio', audio_data, 'application/octet-stream')),
    ]
    multipart_encoder = encoder.MultipartEncoder(
        fields=multiple_files
    )

    monitor_encoder = encoder.MultipartEncoderMonitor(multipart_encoder, post_callback)

    s = requests.Session()

    #s.mount('https://dueros-h2.baidu.com', TimeOutHTTP20Adapter(30))
    s.mount('https://dueros-h2.baidu.com', HTTP20Adapter())
    headers = {
        'authorization': 'Bearer 23.0e617b06679ee45113810a4252139a71.2592000.1502932213.151016915-9892205',
        'dueros-device-id': 'hyxbiao-smart',
    }
    #headers['Content-Type'] = multipart_encoder.content_type
    headers['Content-Type'] = monitor_encoder.content_type
    '''
    r = s.post('https://dueros-h2.baidu.com/dcs/v1/events', 
            headers=headers,
            files=files,
            stream=True)
    '''

    r = s.post('https://dueros-h2.baidu.com/dcs/v1/events', 
            headers=headers,
            #data=multipart_encoder,
            data=monitor_encoder,
            #data=gen(monitor_encoder),
            timeout=60,
            stream=True)

    print (r.status_code)

    play(r)
    r.close()

def play(r):
    p = Popen(['mplayer', '-cache', '1024', '-'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)   
    print(r.headers)
    multipart_data = decoder.MultipartDecoder.from_response(r)
    #wfp = open('out.mp3', 'wb')
    for part in multipart_data.parts:
        print(part.headers)
        content_type = part.headers['Content-Type']
        if content_type == 'application/octet-stream':
            stdout = p.communicate(input=part.content)[0]
            #print(out.decode())
            #wfp.write(part.content)
            #sd.play(part.content)
            #break
        else:
            print(part.content)
    #wfp.close()

def input_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    #audio_queue.put(indata)
    #audio.write(indata)
    audio.append(indata)

def io_callback(indata, outdata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    outdata[:] = indata

def rec():
    #with sd.RawStream(samplerate=16000, channels=1, callback=io_callback):
    #    raw_input('Press enter to continue: ')

    #stream = sd.RawStream(channels=2, callback=io_callback)
    #sd.RawInputStream(samplerate=44100, channels=2, callback=input_callback)
    print('start record')
    with sd.RawInputStream(samplerate=16000, channels=1, dtype='int16', callback=input_callback):
        print('Press enter to continue: ')
        raw_input('Press enter to continue: ')
        print('start event')
        #while not audio.full():
        #    sd.sleep(1)

def speech():
    r = sr.Recognizer()
    m = sr.Microphone(sample_rate=16000)
    with m as source:
        r.adjust_for_ambient_noise(source)

        while True:
            print("Say something!")
            data = r.listen(source)
            print("Say done!")
            audio.append(data.get_raw_data())
            event(audio)

def main():
    #create()
    #fp = open('test_mic.wav', 'rb')
    #fp.seek(44, 0)
    #audio_data = fp.read()
    #fp.close()

    #event(audio_data)
    #event(fp)
    #rec()
    speech()
    #event(audio)
    #test()

if __name__ == '__main__':
    main()
