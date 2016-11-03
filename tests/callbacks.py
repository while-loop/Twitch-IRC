import socket
import unittest

import time

import twitchirc
from twitchirc.irc import IRC, State
from mock import ANY, patch, MagicMock


class MyMocks():
    def socket_connect(self):  # socket.socket.connect
        msg = "socket connect"
        print msg

    def irc_connect(self):
        msg = "irc connect"
        print msg


class TestCallbacks(unittest.TestCase):
    CHANNEL = "testchannel"
    VIEWER = "testviewer"
    MESSAGE = "testmessage"
    USER = "testuser"

    def setUp(self):
        self.chat = IRC("nooauth", TestCallbacks.USER)
        self.chat._conn = MagicMock(name='socket', spec=socket.socket)

        self.login = ":tmi.twitch.tv 001 " + TestCallbacks.USER + "\r\n :tmi.twitch.tv 376 " + TestCallbacks.USER


    def test_on_message(self):
        def test(channel, viewer, message):
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            self.assertEqual(message, TestCallbacks.MESSAGE)

        self.chat.addCallbacks(onMessage=test)
        msg = ":{viewer}!{viewer}@{viewer}.tmi.twitch.tv PRIVMSG #{channel} :{message}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL, message=TestCallbacks.MESSAGE)

        recvs = [self.login, '', ]
        recvs.extend(list(msg))
        self.chat._conn.recv.side_effect = recvs
        self.chat.connect()
        time.sleep(1)
        self.assertTrue(True)



if __name__ == '__main__':
    unittest.main()
