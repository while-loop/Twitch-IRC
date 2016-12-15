"""
    This example demonstrates the use of chat callbacks
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
        print >> sys.stderr, e.message
        sys.exit(255)

    irc.joinChannels(["loltyler1", "trick2g"])

    irc.serverForever()  # keep the main program from exiting
    print "done"
    os.kill(os.getpid(), 9)
