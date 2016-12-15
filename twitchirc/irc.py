import multiprocessing
import os
import re
import socket
import sys
import threading
import time
from json import loads
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
          "onUserNotice": r"^:tmi\.twitch\.tv\s+USERNOTICE\s+#(\w+)\s+:(.*)$",
          "onUserState": r"^:tmi\.twitch\.tv\s+USERSTATE\s+#(\w+)$",
          "onRoomState": r"^:tmi\.twitch\.tv\s+ROOMSTATE\s+#(\w+)$",
          "onIRCInfo": r"^:{username}\.tmi\.twitch\.tv\s+\d+\s+{username}\s+(.*)"
          }


class IRC(object):
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

    def __init__(self, oauthToken, username, overrideSend=False, modBot=False):
        """
        Setup and initialize the IRC object with the configurations given. Call connect() after the constructor

        :param oauthToken: twitch oauth token include the `oauth:` prefix
        :param username: twitch.tv username associated with the ouath token
        """
        if not oauthToken or (type(oauthToken) != str and type(oauthToken) != unicode):
            raise TypeError("Invalid Oauth token")
        if not username or (type(username) != str and type(username) != unicode):
            raise TypeError("Invalid username")

        # Networks
        self.__conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__state = State.DISCONNECTED

        self.cmdShebang = "!"
        self.__overrideSend = overrideSend

        # Threads
        self.__shutdown = False
        manager = multiprocessing.Manager()
        self.__joinQueue = manager.Queue()
        self.__sendQueue = manager.Queue()
        self.__workers = []  # 0 = recv thread
        # 1 = join thread
        # 2 = send thread

        # Twitch Info
        self.__oauthToken = oauthToken
        self.__username = username.lower()  # usernames are lowercase
        self.__modBot = modBot
        self.__channels = set()

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
        :exception socket.error when unable to connect to Twitch IRC server
        :exception IRCException when unable to receive authentication response
        :exception AuthenticationError when failed to login
        """
        self.__conn.settimeout(timeout)
        start = time.time()
        try:
            self.__conn.connect((host, port))
            timeout -= (time.time() - start)  # check how long it took to connect and subtract
        except socket.error, e:
            print >> sys.stderr, 'Cannot connect to Twitch IRC server ({}:{}).'.format(host, port)
            print >> sys.stderr, '\tErrno:\t\t{errno}{newline}' \
                                 '\tMsg:\t\t{msg}{newline}'.format(errno=e[0], newline=os.linesep, msg=e[1])
            raise

        self.__conn.send('PASS {}\r\n'.format(self.__oauthToken))
        self.__conn.send('NICK {}\r\n'.format(self.__username))

        self.__conn.settimeout(timeout)  # set the timeout based on the amount of time connect() took
        start = time.time()
        data = ""
        try:
            data += self.__conn.recv(1024)
            timeout -= (time.time() - start)  # check how long it took to connect and subtract
        except socket.timeout:
            raise IRCException("Unable to receive authentication response from the Twitch IRC server")

        start = time.time()
        while timeout > 0:
            if ":tmi.twitch.tv NOTICE * :Login authentication failed" in data:
                raise AuthenticationError("Login authentication failed")

            if ":tmi.twitch.tv 001 " + self.__username in data and ":tmi.twitch.tv 376 " + self.__username in data:
                # logged in
                self.__state = State.CONNECTED

                # receive membership state events (NAMES, JOIN, PART, or MODE)
                self.__conn.send('CAP REQ :twitch.tv/membership\r\n')
                data = self.__conn.recv(1024)

                # Enables custom raw commands
                self.__conn.send('CAP REQ :twitch.tv/commands\r\n')
                time.sleep(.5)
                data = self.__conn.recv(1024)

                # Enables tags
                # self.__conn.send('CAP REQ :twitch.tv/tags\r\n')
                # data = self.__conn.recv(1024)

                self.__startThreads()

                self.joinChannels(list(self.__channels))
                return

            try:
                self.__conn.settimeout(timeout)  # set the timeout based on the amount of time recv() took
                data += self.__conn.recv(1024)
                timeout -= (time.time() - start)  # check how long it took to recv and subtract
            except socket.timeout:
                raise IRCException("Unable to receive authentication response from the Twitch IRC server")

        # if we get here, we didn't get a response from the server within the timeout limit
        raise IRCException("Unable to receive authentication response from the Twitch IRC server")

    def onReconnect(self):
        self.__state = State.RECONNECTING
        self.close()
        self.connect()

    def __readline(self):
        line = []
        while self.__state == State.CONNECTED:
            c = None
            try:
                c = self.__conn.recv(1)
            except StopIteration:  # fake the type of request when running tests
                self.__state = State.DISCONNECTED
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
        self.__state = State.DISCONNECTED  # should also close recv thread
        self.__conn.close()

    def serverForever(self, pollInterval=0.5):
        while not self.__shutdown:
            time.sleep(pollInterval)

    def shutdown(self):
        self.__shutdown = True
        self.close()

    """
    -----------------------------------------------------------------------------------------------
                                         Channel Functions
    -----------------------------------------------------------------------------------------------
    """

    def joinChannel(self, channel):
        self.joinChannels([channel])

    def partChannel(self, channel):
        self.partChannels([channel])

    def joinChannels(self, channels):
        if type(channels) != list:
            raise TypeError("Channels must be type list")

        for channel in channels:
            cmd = "JOIN #{channel}\r\n".format(channel=channel)
            self.__channels.add(channel)
            if self.__overrideSend:
                self.__conn.send(cmd)
            else:
                self.__joinQueue.put(cmd)

    def partChannels(self, channels):
        if type(channels) != list:
            raise TypeError("Channels must be type list")

        for channel in channels:
            cmd = "PART #{channel}\r\n".format(channel=channel)
            self.__channels.remove(channel)
            if self.__overrideSend:
                self.__conn.send(cmd)
            else:
                self.__joinQueue.put(cmd)

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

    def onPing(self):
        self.__conn.sendall('PONG :tmi.twitch.tv\r\n')

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
        if self.__state == State.DISCONNECTED:
            raise IRCException("Disconnected from Twitch IRC server.")
        elif self.__state == State.RECONNECTING:
            print "Reconnecting to Twitch server",
            self.onReconnect()
            # connected or disconnected..
            if self.__state != State.CONNECTED:
                raise IRCException("Disconnected from Twitch IRC server.")

        if self.__overrideSend:
            self.__conn.send(cmd)
        else:
            self.__sendQueue.put(cmd)

    def __startThreads(self):
        # start recv'ing messages from IRC
        self.__workers.append(threading.Thread(target=self.__recvWorker))

        # start the join queue timer thread. 50 reqs per 15 secs
        self.__workers.append(threading.Thread(target=self.__ircCommandWorker, args=(self.__joinQueue, 15, 50)))

        # start the send queue timer thread. 20 commands per 30 secs
        commands = 100 if self.__modBot else 20
        self.__workers.append(threading.Thread(target=self.__ircCommandWorker, args=(self.__sendQueue, 30, commands)))

        for t in self.__workers:
            t.start()

    def __recvWorker(self):
        while self.__state == State.CONNECTED:
            data = self.__readline()

            if 'PING :tmi.twitch.tv' == data:  # check for ping-pong
                self.onPing()
            elif 'RECONNECT :tmi.twitch.tv' == data:  # reconnects
                self.onReconnect()
            else:
                self.onResponse(data)

    def __ircCommandWorker(self, q, timeLimit, commandLimit):
        """ Join channels given in the worker queue.
            This function executes joins as given in queue. If the max rate is reached, it will sleep
            until the new rate window is reached. Instead of strictly executing commands at .3 sec intervals
            The limit is 50 JOINs per 15 seconds. https://help.twitch.tv/customer/portal/articles/1302780-twitch-irc
            Ex: send 47 joins back to back: .7 secs total
                request to join 6 channels: joins 3 channels (.3 secs total) and sleeps for 14 secs.
                    then joins the other 3 channels
        """
        timeTrack = time.time()
        commandsExecd = 0
        while self.__state == State.CONNECTED:
            command = q.get()
            print '__ircCommandWorker:', command
            secsPassed = time.time() - timeTrack
            if secsPassed > timeLimit:
                timeTrack = time.time()
                commandsExecd = 0
            elif secsPassed <= timeLimit and commandsExecd >= commandLimit:
                time.sleep(timeLimit - secsPassed)
                timeTrack = time.time()
                commandsExecd = 0

            if self.__state == State.CONNECTED:
                self.__conn.send(command)
            q.task_done()
            commandsExecd += 1
            time.sleep(.5)

    """
    -----------------------------------------------------------------------------------------------
                                                Callbacks
    -----------------------------------------------------------------------------------------------
    """

    def onResponse(self, line):
        """
        receive twitch commands or messages directly from the IRC socket
        :param line:
        :return:
        """
        # print line
        for key in sorted(REGEXS.iterkeys()):  # sort because onMessage replaces onCommand
            regex = REGEXS[key]
            if key == "onCommand":
                # TODO fix shebangs that create regex errors (^, \\, etc)
                regex = re.compile(regex.format(shebang=self.cmdShebang))
            elif key == "onIRCInfo":
                regex = re.compile(regex.format(username=self.__username))
            else:
                regex = re.compile(regex)

            match = regex.search(line)
            if match:
                if key == "onMessage":
                    # channel, viewer, message
                    self.onMessage(match.group(2), match.group(1), match.group(3))
                elif key == "onCommand":
                    # channel, viewer, command, value
                    # value may be None
                    self.onCommand(match.group(2), match.group(1), match.group(3), match.group(4))
                elif key == "onJoin":
                    # channel, viewer, state
                    self.onJoinPart(match.group(2), match.group(1), IRC.JOIN)
                elif key == "onPart":
                    # channel, viewer, state
                    self.onJoinPart(match.group(2), match.group(1), IRC.PART)
                elif key == "onMode":
                    # channel, viewer, state
                    # opcode = [-+]
                    self.onMode(match.group(1), match.group(3), match.group(2))
                elif key == "onNotice":
                    # channel, msg-id, msg
                    self.onNotice(match.group(2), match.group(1), match.group(3))
                elif key == "onHostTarget":
                    # hosting_channel, target_channel, amount
                    # target_channel = None when hosting stops
                    amount = int(match.group(3))
                    self.onHostTarget(match.group(1), match.group(2), amount)
                elif key == "onHostTargetStop":
                    # hosting_channel, target_channel, amount
                    # target_channel = None when hosting stops
                    amount = int(match.group(2))
                    self.onHostTarget(match.group(1), None, amount)
                elif key == "onClearChat":
                    # channel, viewer
                    # username may be None if it was a channel clear
                    viewer = None
                    if match.lastindex == 2:
                        viewer = match.group(3)
                    self.onClearChat(match.group(1), viewer)
                elif key == "onUserNotice":
                    # channel, message
                    self.onUserNotice(match.group(1), match.group(2))
                elif key == "onUserState":
                    # channel
                    self.onUserState(match.group(1))
                elif key == "onRoomState":
                    # channel
                    self.onRoomState(match.group(1))
                elif key == "onIRCInfo":
                    # channel
                    self.onIRCInfo(match.group(1))
                else:
                    # TODO got a match, but didn't handle callback
                    print "Didn't handle matched callback", key, regex
                return
        print >> sys.stderr, "Unknown response type.\n\t", line

    def onMessage(self, channel, viewer, message):
        """
        receive a user message from a channel
        :param string channel:
        :param string viewer:
        :param string message:
        :return: None
        """
        return

    def onCommand(self, channel, viewer, command, value):
        """
        receive a bot command by a user from a channel

        a custom shebang can be given to the IRC constructor with `cmdShebang=`.
        :param string channel:
        :param string viewer:
        :param string command:
        :param string value: May be `None` type
        :return: None
        """
        return

    def onJoinPart(self, channel, viewer, state):
        """
        get notified when a viewer enters/leaves a channel irc
        :param string channel:
        :param string viewer:
        :param string state: (IRC.JOIN|IRC.PART)
        :return: None
        """
        return

    def onMode(self, channel, viewer, state):
        """
        get notified when a viewer gets opped/deopped (moderator status) in a channel irc
        :param string channel:
        :param string viewer:
        :param string state: (IRC.OP|IRC.DEOP)
        :return: None
        """
        return

    def onNotice(self, channel, msgID, message):
        """
        general notices from the server (state change, feeback, etc)

        A list of channel notices can be found in
        the official IRC [documentation][https://github.com/justintv/Twitch-API/blob/master/IRC.md#notice].
        :param string channel:
        :param string msgID: MessageIDs can be accessed by IRC.ID_*
        :param string message:
        :return: None
        """
        return

    def onHostTarget(self, hostingChannel, targetChannel, amount):
        """
        notification when a channel starts/stops hosting another channel
        :param string hostingChannel:
        :param string targetChannel: may be `None` type if the command is a host stop command
        :param integer amount:
        :return: None
        """
        return

    def onClearChat(self, channel, viewer):
        """
        notification when a channel's/viewer's chat has been cleared
        :param string channel:
        :param string viewer: may be `None` type if the channel chat has been cleared
        :return: None
        """
        return

    def onUserNotice(self, channel, message):
        """
        notice from a user currently only used for re-subscription messages
        :param string channel:
        :param string message:
        :return: None
        """
        return

    def onUserState(self, channel):
        """
        state of this user in channel
        :param string channel:
        :return: None
        """
        return

    def onRoomState(self, channel):
        """
        roomstate of channel
        :param string channel:
        :return: None
        """
        return

    def onIRCInfo(self, line):
        """
        info from irc socket
        :param string line:
        :return: None
        """
        return
