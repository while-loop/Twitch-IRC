"""
    This example demonstrates the use of chat callbacks


    For better efficiency, try to distrubute channel loads to multiple bot instances on different IPs and connections
    Ex: 2 servers running 8 instances of Twitch-IRC each.
    208 channels in use. Each bot would manage 13 channels.

    Each bot would be able to send 20messages/30secs (100/30 for Mod bots) for a total of 320messages/30secs (1600/30 )
    across all bots.
    https://discuss.dev.twitch.tv/t/max-messages-per-user-channel-ip/6321/3
    https://discuss.dev.twitch.tv/t/twitch-chat-limitations-for-mod-bots/986/13
"""
import os
import random
import sys
import time

from twitchirc.exception import IRCException, AuthenticationError
from twitchirc.irc import IRC


class MyIRC(IRC):
    def onMessage(self, channel, viewer, message):
        print "[onMessage] Received message from {} in #{}: {}".format(viewer, channel, message)

        if random.random() > .99:
            response = "@{}.. Cool story, bro.".format(viewer)
            print "Sending response:\n\t{}".format(response)
            self.sendMessage(channel, response)

    def onCommand(self, channel, viewer, command, value):
        print "[onCommand] Received command from {} in #{}: {}:{}".format(viewer, channel, command, value)

        if command == "exit":
            response = "Goodbye, world!"
            print "Sending response:\n\t{}".format(response)
            self.sendMessage(channel, response)
            time.sleep(1)
            self.shutdown()

    def onJoinPart(self, channel, viewer, state):
        print "[onJoinPart] {} {}ED #{}".format(viewer, state, channel)

    def onMode(self, channel, viewer, state):
        print "[onMode] {}OP'd {} in #{}".format(state, viewer, channel)

    def onClearChat(self, channel, viewer):
        if viewer:
            print "[onClearChat] Chat cleared for {} in #{}".format(viewer, channel)
        else:
            print "[onClearChat] Chat cleared for all in #{}".format(channel)


if __name__ == '__main__':
    # construct IRC with oauth and twitch username
    irc = MyIRC("oauth:abcdefghijklmnopqrstuvwxyz", "username")

    try:
        irc.connect()  # connect to the irc server and login
    except (AuthenticationError, IRCException) as e:
        print >> sys.stderr, e
        sys.exit(255)

    irc.joinChannels(["loltyler1", "trick2g"])

    irc.serverForever()  # keep the main program from exiting
    print "done"
    os.kill(os.getpid(), 9)
