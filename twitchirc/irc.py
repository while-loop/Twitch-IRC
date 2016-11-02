import socket

from twitchirc.exception import IRCError

TWITCH_CHAT_VIEWER_URL = 'http://tmi.twitch.tv/group/user/{channelName}/chatters'


class IRC:
    def __init__(self, oauthToken, clientID, port=6667, moddedSend=False, onPongCallback=None, onMessageCallack=None):
        if not oauthToken or (type(oauthToken) != str and type(oauthToken) != unicode):
            raise IRCError("Invalid Oauth token")
        if not clientID:
            raise IRCError("Invalid Client ID")

        # Networks
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._moddedSend = moddedSend

        # Twitch Info
        self._oauthToken = oauthToken
        self._clientID = clientID

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
        pass

    def leaveChannels(self, channels):
        pass

    def getViewers(self, channelName):
        pass

    """
    -----------------------------------------------------------------------------------------------
                                       Communication Functions
    -----------------------------------------------------------------------------------------------
    """

    def pong(self):
        self._conn.sendall('PONG :tmi.twitch.tv\r\n')

    def getSendQueue(self):
        pass

    def sendMessage(self, channelName, msg, hasCLRF=False):
        if not
        pass

    def _sendRawCommand(self, cmd):
        pass

    """
    -----------------------------------------------------------------------------------------------
                                                Callbacks
    -----------------------------------------------------------------------------------------------
    """

    def _onMessage(self):
        pass
