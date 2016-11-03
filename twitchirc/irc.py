import os
import re
import socket
import sys
import time
from json import loads
from urllib2 import urlopen

from enum import Enum

from twitchirc.exception import APIError, IRCException, AuthenticationError

TWITCH_CHAT_VIEWER_URL = 'http://tmi.twitch.tv/group/user/{channel}/chatters'
TWITCH_IRC_HOST = "irc.chat.twitch.tv"
TWITCH_IRC_PORT = 6667

State = Enum("CONNECTED", "DISCONNECTED", "RECONNECTING")

REGEXS = {"onMessage": "^:(\b\w+)!\1@\1.tmi.twitch.tv PRIVMSG #(\b\w+) :(.*)$",
          "onCommand": "^:(\b\w+)!\1@\1.tmi.twitch.tv PRIVMSG #(\b\w+) :{shebang}(\w*)\s?(.*)$",
          "onJoin": "^:(\b\w+)!\1@\1.tmi.twitch.tv JOIN #(\b\w+)$",
          "onPart": "^:(\b\w+)!\1@\1.tmi.twitch.tv PART #(\b\w+)$",
          "onMode": "^:jtv\s+MODE\s+#(\w+)\s+(-|\+)o\s+(.*)$",
          "onNotice": "^@msg-id=(\w*)\s+:tmi\.twitch\.tv\s+NOTICE\s+#(\w+)\s+:(.*)$",
          "onTargetHost": "^:tmi\.twitch\.tv\s+HOSTTARGET\s+#(\w+)\s+:(\w+)\s+(\d+)$",
          "onClearChat": "^:tmi\.twitch\.tv\s+CLEARCHAT\s+#(\w+)(\s+:(\w+))?$",
          "onUserNotice": "^:tmi\.twitch\.tv\s+USERNOTICE\s+#(\w+)\s+:(\w+)$"
          }


class IRC:
    SUBS_ON = "subs_on"
    SUBS_OFF = "subs_off"
    ALREADY_SUBS_ON = "already_subs_on"
    ALREADY_SUBS_OFF = "already_subs_off"
    SLOW_ON = "slow_on"
    SLOW_OFF = "slow_off"
    R9K_ON = "r9k_on"
    R9K_OFF = "r9k_off"
    ALREADY_R9K_ON = "already_r9k_on"
    ALREADY_R9K_OFF = "already_r9k_off"
    HOST_ON = "host_on"
    HOST_OFF = "host_off"
    BAD_HOST_HOSTING = "bad_host_hosting"
    HOSTS_REMAINING = "hosts_remaining"
    EMOTE_ONLY_ON = "emote_only_on"
    EMOTE_ONLY_OFF = "emote_only_off"
    ALREADY_EMOTE_ONLY_ON = "already_emote_only_on"
    ALREADY_EMOTE_ONLY_OFF = "already_emote_only_off"
    MSG_CHANNEL_SUSPENDED = "msg_channel_suspended"
    TIMEOUT_SUCCESS = "timeout_success"
    BAN_SUCCESS = "ban_success"
    UNBAN_SUCCESS = "unban_success"
    BAD_UNBAN_NO_BAN = "bad_unban_no_ban"
    ALREADY_BANNED = "already_banned"
    UNRECOGNIZED_CMD = "unrecognized_cmd"
    OP = "+"
    DEOP = "-"

    def __init__(self, oauthToken, username, overwriteSend=False, onResponse=None, onPong=None, onReconnect=None,
                 cmdShebang="!"):
        if not oauthToken or (type(oauthToken) != str and type(oauthToken) != unicode):
            raise TypeError("Invalid Oauth token")
        if not username or (type(username) != str and type(username) != unicode):
            raise TypeError("Invalid username")
        if not cmdShebang or (type(cmdShebang) != str and type(cmdShebang) != unicode):
            raise TypeError("Invalid command shebang")

        # Networks
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._state = State.DISCONNECTED

        # lets the dev directly send all outgoing messages bypassing the queues, excluding ping-pongs
        self._overwriteSend = overwriteSend
        self._cmdShebang = cmdShebang

        # Twitch Info
        self._oauthToken = oauthToken
        self._username = username.lower()  # usernames are lowercase

        # Callbacks
        self._callbacks = {}
        # lets the developer handle all incoming messages, excluding ping-pongs and reconnects
        self._callbacks['onResponse'] = onResponse

        self._callbacks['onPong'] = onPong
        self._callbacks['onReconnect'] = onReconnect

        # callbacks if the dev did not override onResponse
        self._callbacks['onCommand'] = None
        self._callbacks['onMessage'] = None
        self._callbacks['onJoin'] = None
        self._callbacks['onPart'] = None
        self._callbacks['onMode'] = None
        self._callbacks['onNotice'] = None
        self._callbacks['onTargetHost'] = None
        self._callbacks['onClearChat'] = None
        self._callbacks['onUserNotice'] = None

    """
    -----------------------------------------------------------------------------------------------
                                         Socket Functions
    -----------------------------------------------------------------------------------------------
    """

    def connect(self, timeout=60, host=TWITCH_IRC_HOST, port=TWITCH_IRC_PORT):
        """
        Connect and Log into the Twitch IRC server
        :param timeout:
        :param host:
        :param port:
        :return:
        """
        self._conn.settimeout(timeout)
        start = time.time()
        try:
            self._conn.connect(host, port)
            timeout -= (time.time() - start)  # check how long it took to connect and subtract
        except socket.error, e:
            print >> sys.stderr, 'Cannot connect to Twitch IRC server ({}:{}).'.format(host, port)
            print >> sys.stderr, '\tErrno:\t\t{errno}{newline}' \
                                 '\tMsg:\t\t{msg}{newline}'.format(errno=e[0], newline=os.linesep, msg=e[1])
            raise

        self._conn.send('PASS {}\r\n'.format(self._oauthToken))
        self._conn.send('NICK {}\r\n'.format(self._username))

        self._conn.settimeout(timeout)  # set the timeout based on the amount of time connect() took
        start = time.time()
        data = ""
        try:
            data += self._conn.recv(1024)
            timeout -= (time.time() - start)  # check how long it took to connect and subtract
        except socket.timeout:
            raise IRCException("Unable to receive authentication response from the Twitch IRC server")

        start = time.time()
        while timeout > 0:
            if ":tmi.twitch.tv NOTICE * :Login authentication failed" in data:
                raise AuthenticationError("Login authentication failed")

            if ":tmi.twitch.tv 001 " + self._username in data and ":tmi.twitch.tv 376 " + self._username in data:
                # logged in
                self._state = State.CONNECTED

                # receive membership state events (NAMES, JOIN, PART, or MODE)
                self._conn.send('CAP REQ :twitch.tv/membership\r\n')

                # Enables custom raw commands
                self._conn.send('CAP REQ :twitch.tv/commands')
                return

            try:
                self._conn.settimeout(timeout)  # set the timeout based on the amount of time recv() took
                data += self._conn.recv(1024)
                timeout -= (time.time() - start)  # check how long it took to recv and subtract
            except socket.timeout:
                raise IRCException("Unable to receive authentication response from the Twitch IRC server")

        # if we get here, we didn't get a response from the server within the timeout limit
        raise IRCException("Unable to receive authentication response from the Twitch IRC server")

        """
        (wrong oath && username) or (correct oath && right username)
        :tmi.twitch.tv NOTICE * :Login authentication failed

         else

        :tmi.twitch.tv 001 user :Welcome, GLHF!
        :tmi.twitch.tv 002 user :Your host is tmi.twitch.tv
        :tmi.twitch.tv 003 user :This server is rather new
        :tmi.twitch.tv 004 user :-
        :tmi.twitch.tv 375 user :-
        :tmi.twitch.tv 372 user :You are in a maze of twisty passages, all alike.
        :tmi.twitch.tv 376 user :>
        """

    def reconnect(self):
        self._state = State.RECONNECTING

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
            if self._overwriteSend:
                self._conn.send(cmd)
            else:
                # TODO add to queue
                pass

    def leaveChannels(self, channels):
        if type(channels) != list:
            raise TypeError("Channels must be type list")

        for channel in channels:
            cmd = "PART #{channel}\r\n".format(channel=channel)
            if self._overwriteSend:
                self._conn.send(cmd)
            else:
                # TODO add to queue
                pass

    def getViewers(self, channel):
        """

        Note: If there are greater than 1000 chatters in a room, NAMES will only return the list of OPs currently
        in the room. So we use the chatters API instead
        :param channel:
        :return:
        """
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
        if self._state == State.DISCONNECTED:
            raise IRCException("Disconnected from Twitch IRC server.")
        elif self._state == State.RECONNECTING:
            print "Reconnecting to Twitch server",
            while self._state == State.RECONNECTING:
                print ".",
                time.sleep(.5)
            # connected or disconnected..
            if self._state == State.DISCONNECTED:
                raise IRCException("Disconnected from Twitch IRC server.")

        if self._overwriteSend:
            self._conn.send(cmd)
        else:
            # add to queue
            pass

    def _recvWorker(self):
        while self._state == State.CONNECTED:
            data = self._readline()

            if 'PING :tmi.twitch.tv' == data:  # check for ping-pong
                if not self._callbacks['onPong']:
                    self.pong()
                else:
                    self._callbacks['onPong'](self, data)
            elif 'RECONNECT :tmi.twitch.tv' == data:  # reconnects
                if not self._callbacks['onReconnect']:
                    self.reconnect()
                else:
                    self._callbacks['onReconnect'](self, data)
            else:
                if not self._callbacks['onResponse']:
                    self._onResponse(data)
                else:
                    self._callbacks['onResponse'](self, data)

    """
    -----------------------------------------------------------------------------------------------
                                                Callbacks
    -----------------------------------------------------------------------------------------------
    """

    def addCallbacks(self, onPong=None, onMessage=None):
        pass

    def _onResponse(self, line):
        for key, regex in REGEXS.iteritems():
            if key == "onCommand":
                regex = re.compile(regex.format(cmdShebang=self._cmdShebang))
            else:
                regex = re.compile(regex)

            match = regex.search(line)
            if match:
                if key == "onMessage":
                    if self._callbacks["onMessage"]:
                        # channel, viewer, message
                        self._callbacks["onMessage"](match.group(2), match.group(1), match.group(3))
                elif key == "onCommand":
                    if self._callbacks["onCommand"]:
                        # channel, viewer, command, value
                        # value may be None
                        self._callbacks["onCommand"](match.group(2), match.group(1), match.group(3), match.group(4))
                elif key == "onJoin":
                    if self._callbacks["onJoin"]:
                        # channel, viewer
                        self._callbacks["onJoin"](match.group(2), match.group(1))
                elif key == "onPart":
                    if self._callbacks["onPart"]:
                        # channel, viewer
                        self._callbacks["onPart"](match.group(2), match.group(1))
                elif key == "onMode":
                    if self._callbacks["onMode"]:
                        # channel, viewer, opcode
                        # opcode = [-+]
                        self._callbacks["onMode"](match.group(1), match.group(3), match.group(2))
                elif key == "onNotice":
                    if self._callbacks["onNotice"]:
                        # channel, msg-id, msg
                        self._callbacks["onNotice"](match.group(2), match.group(1), match.group(3))
                elif key == "onTargetHost":
                    if self._callbacks["onTargetHost"]:
                        # hosting_channel, target_channel, amount
                        # target_channel = '-' when hosting stops
                        self._callbacks["onTargetHost"](match.group(1), match.group(2), match.group(3))
                elif key == "onClearChat":
                    # TODO Check if user matchgroup is None
                    if self._callbacks["onClearChat"]:
                        # channel, username
                        # username may be None if it was a channel clear
                        self._callbacks["onClearChat"](match.group(1), match.group(2))
                elif key == "onUserNotice":
                    if self._callbacks["onUserNotice"]:
                        # channel, message
                        self._callbacks["onUserNotice"](match.group(1), match.group(2))
                else:
                    # TODO got a match, but didn't handle callback
                    print "Didn't handle matched callback", key, regex
                return
        print >> sys.stderr, "Unknown response type.\n\t", line
