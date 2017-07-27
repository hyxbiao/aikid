
from __future__ import print_function
import sys
import time

from subprocess import Popen, PIPE, STDOUT
import threading

__author__ = "hyxbiao"
__version__ = "0.0.1"

class MPlayer(object):
    def __init__(self, args=None, daemon=False,
                 stdin=PIPE, stdout=PIPE, stderr=PIPE):
        command = ['mplayer', '-quiet', '-msglevel', 'global=6', '-msglevel', 'cplayer=4', '-cache', '1024'] 
        if daemon:
            command += ['-idle', '-slave']
        if args:
            command += args
        self._player = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE)   
        self._daemon = daemon
        if daemon:
            self._thread = threading.Thread(target=self._ondata, 
                                            args=(self._player.stdout, self._player.stderr))
            self._thread.setDaemon(True)
            self._thread.start()

    def close(self):
        if self._daemon:
            self.cmd('quit')
        self._player.kill()

    @classmethod
    def talk(cls, data):
        player = cls(['-'])
        return player.communicate(data)

    @classmethod
    def play(cls, path):
        player = cls([path], stdin=None, stdout=None, stderr=None)
        return player

    def communicate(self, data):
        stdout = self._player.communicate(data)
        return stdout

    def send(self, data):
        self._player.stdin.write(data)
        self._player.stdin.flush()
        #self._player.wait()

    def cmd(self, command):
        print(command)
        self.send(command + '\n')

    def _ondata(self, stdout, stderr):
        while True:
            out = stdout.readline()
            if out:
                print('stdout: ' + out)
            err = stderr.readline()
            if err:
                print('stderr: ' + err)
            time.sleep(0.1)


class PlayerManager(object):
    def __init__(self):

        self._mp3_player = MPlayer(daemon=True)

        #self._echo_player = MPlayer(['-'], daemon=True)

    def play(self, stream):
        print('start play')
        if stream.startswith('http'):
            self._mp3_player.cmd('stop')
            self._mp3_player.cmd('loadfile ' + stream)
        else:
            #self._echo_player.send(stream)
            MPlayer.talk(stream)

    def close(self):
        self._mp3_player.close()
