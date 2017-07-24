
from __future__ import print_function
import sys
from aip import AipSpeech

__author__ = "hyxbiao"
__version__ = "0.0.1"

class Speech(object):
    def __init__(self, conf):
        self._conf = conf

        APP_ID = self._conf['app_id']
        API_KEY = self._conf['api_key']
        SECRET_KEY = self._conf['secret_key']
        self._aipSpeech = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

    def asr(self, audio):

        res = self._aipSpeech.asr(audio)

        if res['err_no'] == 0:
            return res['result'][0]

        err = 'err_no: {}, msg: {}'.format(res['err_no'], res['err_msg'])
        print(err)
        return False

    def synthesis(self, text):
        options = self._conf['synthesis']['options']
        res = self._aipSpeech.synthesis(text, options=options)
        if not isinstance(res, dict):
            return res

        err = 'err_no: {}, msg: {}'.format(res['err_no'], res['err_msg'])
        print(err)
        return False
