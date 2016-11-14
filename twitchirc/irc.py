import os
import re
import socket
import sys
import time
from json import loads
from threading import Thread
from urllib2 import urlopen

from enum import Enum

from twitchirc.exception import APIError, IRCException, AuthenticationError

TWITCH_CHAT_VIEWER_URL = 'http://tmi.twitch.tv/group/user/{channel}/chatters'
TWITCH_IRC_HOST = "irc.chat.twitch.tv"
TWITCH_IRC_PORT = 6667

State = Enum("CONNECTED", "DISCONNECTED", "RECONNECTING")

REGEXS = {"onMessage": r"^:(\w+)!\1@\1\.tmi\.twitch\.tv\s+PRIVMSG\s+#(\w+)\s+:(.*)$",
          "onCommand": r"^:(\b\w+)!\1@\1.tmi.twitch.tv PRIVMSG #(\b\w+) :{shebang}(\w*)\s?(.*)$",
          "onJoin": r"^:(\b\w+)!\1@\1.tmi.twitch.tv JOIN #(\b\w+)$",
          "onPart": r"^:(\b\w+)!\1@\1.tmi.twitch.tv PART #(\b\w+)$",
          "onMode": r"^:jtv\s+MODE\s+#(\w+)\s+(-|\+)o\s+(.*)$",
          "onNotice": r"^@msg-id=(\w*)\s+:tmi\.twitch\.tv\s+NOTICE\s+#(\w+)\s+:(.*)$",
          "onHostTarget": r"^:tmi\.twitch\.tv\s+HOSTTARGET\s+#(\w+)\s+:(\w+)\s+(\d+)$",
          "onHostTargetStop": r"^:tmi\.twitch\.tv\s+HOSTTARGET\s+#(\w+)\s+:-\s+(\d+)$",
          "onClearChat": r"^:tmi\.twitch\.tv\s+CLEARCHAT\s+#(\w+)(\s+:(\w+))?$",
          "onUserNotice": r"^:tmi\.twitch\.tv\s+USERNOTICE\s+#(\w+)\s+:(.*)$"
          }


class IRC:
    ID_SUBS_ON = "subs_on"
    ID_SUBS_OFF = "subs_off"
    ID_ALREADY_SUBS_ON = "already_subs_on"
    ID_ALREADY_SUBS_OFF = "already_subs_off"
    ID_SLOW_ON = "slow_on"
    ID_SLOW_OFF = "slow_off"
    ID_R9K_ON = "r9k_on"
    ID_R9K_OFF = "r9k_off"
    ID_ALREADY_R9K_ON = "already_r9k_on"
    ID_ALREADY_R9K_OFF = "already_r9k_off"
    ID_HOST_ON = "host_on"
    ID_HOST_OFF = "host_off"
    ID_BAD_HOST_HOSTING = "bad_host_hosting"
    ID_HOSTS_REMAINING = "hosts_remaining"
    ID_EMOTE_ONLY_ON = "emote_only_on"
    ID_EMOTE_ONLY_OFF = "emote_only_off"
    ID_ALREADY_EMOTE_ONLY_ON = "already_emote_only_on"
    ID_ALREADY_EMOTE_ONLY_OFF = "already_emote_only_off"
    ID_MSG_CHANNEL_SUSPENDED = "msg_channel_suspended"
    ID_TIMEOUT_SUCCESS = "timeout_success"
    ID_BAN_SUCCESS = "ban_success"
    ID_UNBAN_SUCCESS = "unban_success"
    ID_BAD_UNBAN_NO_BAN = "bad_unban_no_ban"
    ID_ALREADY_BANNED = "already_banned"
    ID_UNRECOGNIZED_CMD = "unrecognized_cmd"
    OP = "+"
    DEOP = "-"
    JOIN = "JOIN"
    PART = "PART"

    def __init__(self, oauthToken, username, overwriteSend=False, onResponse=None, onPing=None, onReconnect=None,
                 cmdShebang="!"):
        """
        Setup and initialize the IRC object with the configurations given. Call connect() after the constructor

        :param oauthToken: twitch oauth token include the `oauth:` prefix
        :param username: twitch.tv username associated with the ouath token
        :param overwriteSend: skip the send rate limiter feature
        :param onResponse: override any response coming directly from the IRC socket
        :param onPing: override the onPing handler
        :param onReconnect: override the onReconnect handler
        :param cmdShebang: add a custom command shebang to the pre-processing feature
        """
        if not oauthToken or (type(oauthToken) != str and type(oauthToken) != unicode):
            raise TypeError("Invalid Oauth token")
        if not username or (type(username) != str and type(username) != unicode):
            raise TypeError("Invalid username")
        if not cmdShebang or (type(cmdShebang) != str and type(cmdShebang) != unicode):
            raise TypeError("Invalid command shebang")

        # Networks
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._state = State.DISCONNECTED

        # Threads
        self._recvThread = Thread(target=self._recvWorker)
        self._shutdown = False

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

        self._callbacks['onPing'] = onPing
        self._callbacks['onReconnect'] = onReconnect

        # callbacks if the dev did not override onResponse
        self._callbacks['onCommand'] = None
        self._callbacks['onMessage'] = None
        self._callbacks['onJoinPart'] = None
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
        """
        self._conn.settimeout(timeout)
        start = time.time()
        try:
            self._conn.connect((host, port))
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
                self._conn.send('CAP REQ :twitch.tv/commands\r\n')

                self._conn.recv(1024)
                self._recvThread.start()
                return

            try:
                self._conn.settimeout(timeout)  # set the timeout based on the amount of time recv() took
                data += self._conn.recv(1024)
                timeout -= (time.time() - start)  # check how long it took to recv and subtract
            except socket.timeout:
                raise IRCException("Unable to receive authentication response from the Twitch IRC server")

        # if we get here, we didn't get a response from the server within the timeout limit
        raise IRCException("Unable to receive authentication response from the Twitch IRC server")

    def reconnect(self):
        self._state = State.RECONNECTING
        self.close()
        self.connect()

    def _readline(self):
        line = []
        while True:
            c = None
            try:
                c = self._conn.recv(1)
            except StopIteration:  # fake the type of request when running tests
                self._state = State.DISCONNECTED
                line = list("PING :tmi.twitch.tv")
                break

            if c == '\n':
                break
            else:
                line.append(c)

        size = len(line) - 1

        if size > 0 and line[size] == '\r':  # IRC newlines are \r\n
            del line[size]

        return ''.join(line)

    def close(self):
        self._state = State.DISCONNECTED  # should also close recv thread
        self._conn.close()

    def serverForever(self, pollInterval=0.5):
        while not self._shutdown:
            time.sleep(pollInterval)

    def shutdown(self):
        self._shutdown = True

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
        """
        Send a message to the specified channel
        :param channelName: channel to send the message to
        :param msg: message to send
        """
        if msg[:len(msg) - 3] != "\r\n":
            msg += "\r\n"

        formattedMsg = 'PRIVMSG #{channelName} :{msg}'.format(channelName=channelName, msg=msg)
        self.sendCommand(formattedMsg)

    def sendCommand(self, cmd):
        if self._state == State.DISCONNECTED:
            raise IRCException("Disconnected from Twitch IRC server.")
        elif self._state == State.RECONNECTING:
            print "Reconnecting to Twitch server",
            self.reconnect()
            # connected or disconnected..
            if self._state != State.CONNECTED:
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
                if not self._callbacks['onPing']:
                    self.pong()
                else:
                    self._callbacks['onPing'](self, data)
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

    def addCallbacks(self, onMessage=None, onCommand=None, onJoinPart=None, onMode=None, onNotice=None,
                     onHostTarget=None, onClearChat=None, onUserNotice=None):
        self._callbacks['onCommand'] = onCommand
        self._callbacks['onMessage'] = onMessage
        self._callbacks['onJoinPart'] = onJoinPart
        self._callbacks['onMode'] = onMode
        self._callbacks['onNotice'] = onNotice
        self._callbacks['onHostTarget'] = onHostTarget
        self._callbacks['onClearChat'] = onClearChat
        self._callbacks['onUserNotice'] = onUserNotice

    def _onResponse(self, line):
        # print line
        for key in sorted(REGEXS.iterkeys()):  # sort because onMessage replaces onCommand
            regex = REGEXS[key]
            if key == "onCommand":
                regex = re.compile(
                    regex.format(shebang=self._cmdShebang))  # TODO fix shebangs that create regex errors (^, \\, etc)
            else:
                regex = re.compile(regex)

            match = regex.search(line)
            if match:
                if key == "onMessage":
                    if self._callbacks["onMessage"]:
                        # channel, viewer, message
                        self._callbacks["onMessage"](self, match.group(2), match.group(1), match.group(3))
                elif key == "onCommand":
                    if self._callbacks["onCommand"]:
                        # channel, viewer, command, value
                        # value may be None
                        self._callbacks["onCommand"](self, match.group(2), match.group(1), match.group(3),
                                                     match.group(4))
                elif key == "onJoin":
                    if self._callbacks["onJoinPart"]:
                        # channel, viewer, state
                        self._callbacks["onJoinPart"](self, match.group(2), match.group(1), IRC.JOIN)
                elif key == "onPart":
                    if self._callbacks["onJoinPart"]:
                        # channel, viewer, state
                        self._callbacks["onJoinPart"](self, match.group(2), match.group(1), IRC.PART)
                elif key == "onMode":
                    if self._callbacks["onMode"]:
                        # channel, viewer, opcode
                        # opcode = [-+]
                        self._callbacks["onMode"](self, match.group(1), match.group(3), match.group(2))
                elif key == "onNotice":
                    if self._callbacks["onNotice"]:
                        # channel, msg-id, msg
                        self._callbacks["onNotice"](self, match.group(2), match.group(1), match.group(3))
                elif key == "onHostTarget":
                    if self._callbacks["onHostTarget"]:
                        # hosting_channel, target_channel, amount
                        # target_channel = None when hosting stops
                        amount = int(match.group(3))
                        self._callbacks["onHostTarget"](self, match.group(1), match.group(2), amount)
                elif key == "onHostTargetStop":
                    if self._callbacks["onHostTarget"]:
                        # hosting_channel, target_channel, amount
                        # target_channel = None when hosting stops
                        amount = int(match.group(2))
                        self._callbacks["onHostTarget"](self, match.group(1), None, amount)
                elif key == "onClearChat":
                    if self._callbacks["onClearChat"]:
                        # channel, viewer
                        # username may be None if it was a channel clear
                        viewer = None
                        if match.lastindex == 2:
                            viewer = match.group(3)
                        self._callbacks["onClearChat"](self, match.group(1), viewer)
                elif key == "onUserNotice":
                    if self._callbacks["onUserNotice"]:
                        # channel, message
                        self._callbacks["onUserNotice"](self, match.group(1), match.group(2))
                else:
                    # TODO got a match, but didn't handle callback
                    print "Didn't handle matched callback", key, regex
                return
        print >> sys.stderr, "Unknown response type.\n\t", line
