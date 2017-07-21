
from __future__ import print_function
import sys
import io
import requests

from hyper.contrib import HTTP20Adapter
from hyper import HTTPConnection
from hyper import HTTP20Connection
from requests_toolbelt.multipart import encoder
from requests_toolbelt.multipart import decoder
import Queue

import json

__author__ = "hyxbiao"
__version__ = "0.0.1"


class TimeOutHTTP20Adapter(HTTP20Adapter):
    def __init__(self, timeout = 5):
        super(TimeOutHTTP20Adapter, self).__init__()
        self.timeout = timeout

    def get_connection(self, host, port, scheme, cert=None):
        conn = super(TimeOutHTTP20Adapter, self).get_connection(host, port, scheme, cert)
        if conn._sock:
            conn._sock.settimeout(self.timeout)
        return conn


class DcsClient(object):
    def __init__(self, conf):
        self._conf = conf

        self._base_url = '{}://{}'.format(self._conf['protocol'], self._conf['host'])
        self._api_directive = self._base_url + self._conf['api']['directive'] 
        self._api_events = self._base_url + self._conf['api']['events'] 

        self._sess = requests.Session()
        self._sess.mount(self._base_url, HTTP20Adapter())
        #self._sess.mount(self._base_url, TimeOutHTTP20Adapter(30))

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
            return None

        name, stream = self.get_audio_out(r)
        return stream

    def get_audio_out(self, response):

        data = decoder.MultipartDecoder.from_response(response)
        for part in data.parts:
            print(part.headers)
            content_type = part.headers['Content-Type']
            if content_type == 'application/octet-stream':
                pass
            else:
                print(part.content)

        stream = None
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
