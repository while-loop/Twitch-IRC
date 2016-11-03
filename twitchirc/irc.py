import socket
from json import loads
from urllib2 import urlopen

from twitchirc.exception import APIError

TWITCH_CHAT_VIEWER_URL = 'http://tmi.twitch.tv/group/user/{channel}/chatters'


class IRC:
    def __init__(self, oauthToken, port=6667, moddedSend=False, onPongCallback=None, onMessageCallack=None):
        if not oauthToken or (type(oauthToken) != str and type(oauthToken) != unicode):
            raise TypeError("Invalid Oauth token")

        # Networks
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._moddedSend = moddedSend

        # Twitch Info
        self._oauthToken = oauthToken

        # Callbacks
        self._onPongCallback = onPongCallback if onPongCallback else self.pong
        self._onMessageCallack = onMessageCallack if onMessageCallack else self._onMessage

    """
    -----------------------------------------------------------------------------------------------
                                         Socket Functions
    -----------------------------------------------------------------------------------------------
    """

    def connect(self):
        pass

    def _readline(self):
        line = []
        while True:
            c = self._conn.recv(1)

            if c == '\n':
                break
            else:
                line.append(c)

        size = len(line) - 1
        if line[size] == '\r':  # IRC newlines are \r\n
            del line[size]

        return ''.join(line)

    """
    -----------------------------------------------------------------------------------------------
                                         Channel Functions
    -----------------------------------------------------------------------------------------------
    """

    def joinChannels(self, channels):
        if type(channels) != list:
            raise TypeError("Channels must be type list")

        for channel in channels:
            cmd = "JOIN #{channel}\r\n".format(channel=channel)
            if self._moddedSend:
                self._conn.send(cmd)
            else:
                # TODO add to queue
                pass

    def leaveChannels(self, channels):
        if type(channels) != list:
            raise TypeError("Channels must be type list")

        for channel in channels:
            cmd = "PART #{channel}\r\n".format(channel=channel)
            if self._moddedSend:
                self._conn.send(cmd)
            else:
                # TODO add to queue
                pass

    def getViewers(self, channel):
        try:
            data = urlopen(TWITCH_CHAT_VIEWER_URL.format(channel=channel)).read().decode('utf-8')
        except:
            raise APIError('Unable to connect Twitch API')

        data = loads(data)
        ret = {'viewers': data.pop('chatters'), 'count': data['chatter_count']}
        return ret

    """
    -----------------------------------------------------------------------------------------------
                                       Communication Functions
    -----------------------------------------------------------------------------------------------
    """

    def pong(self):
        self._conn.sendall('PONG :tmi.twitch.tv\r\n')

    def getSendQueue(self):
        pass

    def sendMessage(self, channelName, msg):
        if msg[:len(msg) - 3] != "\r\n":
            msg += "\r\n"

        formattedMsg = 'PRIVMSG #{channelName} :{msg}'.format(channelName=channelName, msg=msg)
        self._sendRawCommand(formattedMsg)

    def sendCommand(self, cmd):
        self._sendRawCommand(cmd)

    def _sendRawCommand(self, cmd):
        if self._moddedSend:
            self._conn.send(cmd)
        else:
            # add to queue
            pass

    """
    -----------------------------------------------------------------------------------------------
                                                Callbacks
    -----------------------------------------------------------------------------------------------
    """

    def _onMessage(self):
        pass
