"""
    This example demonstrates the use of onResponse() and the overrideSend feature.

    WARNING: This will send the commands directly to the IRC. If you send commands too fast in a short
    period of time, you WILL get temp banned from IRC.
    Please implement a method to handle queuing commands

    Note:
    For better efficiency, try to distribute channel loads to multiple bot instances on different IPs and connections
    Ex: 2 servers running 8 instances of Twitch-IRC each.
    208 channels in use. Each bot would manage 13 channels.

    Each bot would be able to send 20messages/30secs (100/30 for Mod bots) for a total of 320messages/30secs (1600/30 )
    across all bots.
    https://discuss.dev.twitch.tv/t/max-messages-per-user-channel-ip/6321/3
    https://discuss.dev.twitch.tv/t/twitch-chat-limitations-for-mod-bots/986/13
"""

# common chat Regular expressions can be found at
# https://github.com/while-loop/Twitch-IRC/blob/master/twitchirc/irc.py#L20

import os
import random
import re
import sys
import time

from twitchirc.exception import IRCException, AuthenticationError
from twitchirc.irc import IRC, REGEXS


class MyIRC(IRC):
    def __init__(self, oauthToken, username, overrideSend=False, customshebang="!"):
        """
        Constructor to set up IRC and a custom DAO
        :param string oauthToken:
        :param string username:
        :param boolean overrideSend:
        """
        super(MyIRC, self).__init__(oauthToken, username, overrideSend=overrideSend, cmdShebang=customshebang)
        self.mDB = MockDAO()

    def onResponse(self, line):
        """
        Override the onResponse function. This will disable all callbacks and will have to manually
        parse irc messages

        This example looks only for channel commands and sends back a response to the chat
        :param line:
        :return: None
        """
        regex = re.compile(REGEXS["onCommand"].format(shebang=self.cmdShebang))
        match = regex.search(line)
        if match:
            # channel, viewer, command, value
            # match.group(2), match.group(1), match.group(3), match.group(4)
            print match.group(2), match.group(1), match.group(3), match.group(4)

            if match.group(3) == "exit":
                response = "Goodbye, world!"
                print "Sending response:\n\t{}".format(response)
                self.sendMessage(match.group(2), response)
                time.sleep(1)
                self.shutdown()
                return

            if random.random() > .80:
                # get the response to a command from the DB
                response = self.mDB.getCommandValue(match.group(2), match.group(3))

                # WARNING: This will send the message directly to the channel. If you send messages too fast in a short
                # period of time, you WILL get 8 hour banned from IRC.
                # Please implement a method to queue commands to IRC
                self.sendMessage(match.group(2), "@{}, {}".format(match.group(1), response))

    def onPing(self):
        """
        Override onPing to log when the server is issuing Pings.
        Also, send back pong to the server.
        :return:
        """
        self.mDB.log(time.time(), "onPing")

        self.sendCommand("PONG :tmi.twitch.tv\r\n")
        # OR
        super(MyIRC, self).onPing()

    def shutdown(self):
        """
        Override shutdown to take care of my DAO and call super allow the bot to gracefully shutdown
        :return: None
        """

        self.mDB.close()
        super(MyIRC, self).shutdown()


class MockDAO(object):
    """
        Mock DAO to simulate saving/retrieving information to a Database
    """

    def log(self, timestamp, msg):
        print timestamp, msg

    def getChannels(self, botID):
        return ["loltyler1", "trickg2g"]

    def getCommandValue(self, channel, command):
        return "I like turtles."

    def close(self):
        print "Closing MockDB connection"


if __name__ == '__main__':
    # construct IRC with oauth and twitch username
    tIRC = MyIRC("oauth:abcdefghijklmnopqrstuvwxyz", "username", overrideSend=True, customshebang="#")

    try:
        tIRC.connect()  # connect to the irc server and login
    except (AuthenticationError, IRCException) as e:
        print >> sys.stderr, e
        sys.exit(255)

    # WARNING: This will send the JOIN commands directly to the IRC. If you send messages too fast in a short
    # period of time, you WILL get temp banned from IRC.
    # Please implement a method to JOIN commands to IRC
    tIRC.joinChannels(tIRC.mDB.getChannels("bot8675309"))

    tIRC.serverForever()  # keep the main program from exiting
    print "done"
    os.kill(os.getpid(), 9)
