
from __future__ import print_function
import sys
import io
sys.path.insert(0, '/Users/hyxbiao/dep/github/http/hyper')
import requests

import ssl
from hyper.contrib import HTTP20Adapter
from hyper import HTTPConnection
from hyper import HTTP20Connection
from requests_toolbelt.multipart import encoder
from requests_toolbelt.multipart import decoder
import Queue

import json

__author__ = "hyxbiao"
__version__ = "0.0.1"


class DcsClient(object):
    def __init__(self, conf):
        self._conf = conf

        self._base_url = '{}://{}'.format(self._conf['protocol'], self._conf['host'])
        self._api_directive = self._base_url + self._conf['api']['directive'] 
        self._api_events = self._base_url + self._conf['api']['events'] 

        self._sess = requests.Session()
        self._sess.mount(self._base_url, HTTP20Adapter())

    def init_downstream(self):
        headers = self._build_headers()
        r = self._sess.get(self._api_directive, 
                            headers=headers,
                            stream=True)
        pass

    def echo(self, speech):
        headers = self._build_headers()

        metadata = self._build_meta()
        meta = json.dumps(metadata)
        multiple_files = [
            ('metadata', ('metadata', meta, 'application/json; charset=UTF-8')),
            ('audio', ('audio', speech, 'application/octet-stream')),
        ]
        data = encoder.MultipartEncoder(
            fields=multiple_files
        )
        headers['Content-Type'] = data.content_type

        try:
            r = self._sess.post(self._api_events,
                    headers=headers,
                    data=data,
                    #timeout=60,
                    stream=True)
        except ssl.SSLError as e:
            print(e)
            return []

        return self.get_audio_out(r)
        #name, stream = self.get_audio_out(r)
        #return stream

    def get_audio_out(self, response):

        data = decoder.MultipartDecoder.from_response(response)
        '''
        for part in data.parts:
            print(part.headers)
            content_type = part.headers['Content-Type']
            if content_type == 'application/octet-stream':
                pass
            else:
                print(part.content)
        stream = None
        name = None
        '''

        for part in data.parts:
            print(part.headers)
            content_type = part.headers['Content-Type']
            if content_type == 'application/octet-stream':
                stream = part.content
                print('------------Audio Speak, length: {}'.format(len(stream)))
                yield stream

            else:
                print(part.content)
                cmd = json.loads(part.content)
                name = cmd['directive']['header']['name']
                if name == 'Speak':
                    continue
                elif name == 'Play':
                    payload = cmd['directive']['payload']
                    stream = payload['audioItem']['stream']['url']
                    print('------------Audio Play: ' + stream)
                    yield stream
        '''
        speak_cmd = json.loads(data.parts[0].content)
        header = speak_cmd['directive']['header']
        payload = speak_cmd['directive']['payload']
        name = header['name']
        if name == 'Speak':
            stream = data.parts[1].content
        elif name == 'Play':
            stream = payload['audioItem']['stream']['url']
        else:
            #raise ValueError('Not support name: {}'.format(name))
            pass

        return name, stream
        '''

    def _build_headers(self):
        headers = {
            'authorization': 'Bearer ' + self._conf['oauth_token'],
            'dueros-device-id': self._conf['device_id'],
        }
        return headers

    def _build_meta(self):
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
                "volume" : 80,
                "muted" : False
            }
        }]
        return metadata
