import inspect
import socket
import unittest
from optparse import OptionParser
from types import FunctionType

import sys

import time
from mock import MagicMock

from twitchirc.irc import IRC


class TestCallbacks(unittest.TestCase):
    CHANNEL = "testchannel"
    VIEWER = "testviewer"
    USER = "testuser"
    tests = None

    def setUp(self, shebang='!'):
        if not TestCallbacks.tests:
            TestCallbacks.tests = {}
            for x, y in TestCallbacks.__dict__.items():
                if type(y) == FunctionType and y.func_name[:4] == "test" and "zzzzz" not in y.func_name:
                    TestCallbacks.tests[y.func_name] = False

        self.chat = IRC("nooauth", TestCallbacks.USER, cmdShebang=shebang)
        self.chat._conn = MagicMock(name='socket', spec=socket.socket)

        self.login = ":tmi.twitch.tv 001 " + TestCallbacks.USER + "\r\n :tmi.twitch.tv 376 " + TestCallbacks.USER

    def tearDown(self):
        time.sleep(.005)  # allow the callbacks to be executed
        self.chat.close()

    def setAndConnect(self, msg):
        recvs = [self.login, '', ]
        recvs.extend(list(msg))
        self.chat._conn.recv.side_effect = recvs
        self.chat.connect()

    def test_on_message(self):
        MESSAGE = "testmessage"
        func = inspect.stack()[0][3]

        def onMessage(channel, viewer, message):
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            self.assertEqual(message, MESSAGE)
            TestCallbacks.tests[func] = True

        self.chat.addCallbacks(onMessage=onMessage)
        msg = ":{viewer}!{viewer}@{viewer}.tmi.twitch.tv PRIVMSG #{channel} :{message}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL, message=MESSAGE)

        self.setAndConnect(msg)

    def test_on_command(self):
        SHEBANG = "!"
        COMMAND = "command"
        VALUE = "value"
        func = inspect.stack()[0][3]

        def onCommand(channel, viewer, command, value):
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            self.assertEqual(command, COMMAND)
            self.assertEqual(value, VALUE)
            TestCallbacks.tests[func] = True

        self.chat.addCallbacks(onCommand=onCommand)
        msg = ":{viewer}!{viewer}@{viewer}.tmi.twitch.tv PRIVMSG #{channel} :{shebang}{command} {value}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL, shebang=SHEBANG, command=COMMAND, value=VALUE)

        self.setAndConnect(msg)

    def test_on_command_with_shebang(self):
        SHEBANG = '#'
        COMMAND = "shebangcommand"
        VALUE = "shebangvalue"
        func = inspect.stack()[0][3]

        self.tearDown()
        self.setUp(shebang=SHEBANG)

        def onCommand(channel, viewer, command, value):
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            self.assertEqual(command, COMMAND)
            self.assertEqual(value, VALUE)
            TestCallbacks.tests[func] = True

        self.chat.addCallbacks(onCommand=onCommand)
        msg = ":{viewer}!{viewer}@{viewer}.tmi.twitch.tv PRIVMSG #{channel} :{shebang}{command} {value}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL, shebang=SHEBANG, command=COMMAND, value=VALUE)

        self.setAndConnect(msg)

    def test_on_join(self):
        func = inspect.stack()[0][3]

        def onJoin(channel, viewer):
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            TestCallbacks.tests[func] = True

        self.chat.addCallbacks(onJoin=onJoin)
        msg = ":{viewer}!{viewer}@{viewer}.tmi.twitch.tv JOIN #{channel}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL)

        self.setAndConnect(msg)

    def test_on_part(self):
        func = inspect.stack()[0][3]

        def onPart(channel, viewer):
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            TestCallbacks.tests[func] = True

        self.chat.addCallbacks(onPart=onPart)
        msg = ":{viewer}!{viewer}@{viewer}.tmi.twitch.tv PART #{channel}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL)

        self.setAndConnect(msg)

    def test_on_mode_op(self):
        OPCODE = IRC.OP
        func = inspect.stack()[0][3]

        def onMode(channel, viewer, opcode):
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            self.assertEqual(opcode, OPCODE)
            TestCallbacks.tests[func] = True

        self.chat.addCallbacks(onMode=onMode)
        msg = ":jtv MODE #{channel} {op}o {viewer}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL, op=OPCODE)

        self.setAndConnect(msg)

    def test_on_mode_deop(self):
        OPCODE = IRC.DEOP
        func = inspect.stack()[0][3]

        def onMode(channel, viewer, opcode):
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            self.assertEqual(opcode, OPCODE)
            TestCallbacks.tests[func] = True

        self.chat.addCallbacks(onMode=onMode)
        msg = ":jtv MODE #{channel} {op}o {viewer}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL, op=OPCODE)

        self.setAndConnect(msg)

    def test_on_notice_already_r9k_on(self):
        ID = IRC.ALREADY_R9K_ON
        MSG = "This room is already in r9k mode."
        func = inspect.stack()[0][3]

        def onNotice(channel, id, msg):
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(id, ID)
            self.assertEqual(msg, MSG)
            TestCallbacks.tests[func] = True

        self.chat.addCallbacks(onNotice=onNotice)
        msg = "@msg-id={id} :tmi.twitch.tv NOTICE #{channel} :{message}\r\n".format(
            id=ID, channel=TestCallbacks.CHANNEL, message=MSG)

        self.setAndConnect(msg)

    def test_on_notice_emote_only_on(self):
        ID = IRC.EMOTE_ONLY_ON
        MSG = "This room is now in emote-only mode."
        func = inspect.stack()[0][3]

        def onNotice(channel, id, msg):
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(id, ID)
            self.assertEqual(msg, MSG)
            TestCallbacks.tests[func] = True

        self.chat.addCallbacks(onNotice=onNotice)
        msg = "@msg-id={id} :tmi.twitch.tv NOTICE #{channel} :{message}\r\n".format(
            id=ID, channel=TestCallbacks.CHANNEL, message=MSG)

        self.setAndConnect(msg)

    def test_on_host_target(self):
        HOSTING = "hostingchannel"
        TARGET = self.CHANNEL
        AMOUNT = 8675309
        func = inspect.stack()[0][3]

        def onHostTarget(hosting, target, amount):
            self.assertEqual(hosting, HOSTING)
            self.assertEqual(target, TARGET)
            self.assertEqual(amount, AMOUNT)
            TestCallbacks.tests[func] = True

        self.chat.addCallbacks(onHostTarget=onHostTarget)
        msg = ":tmi.twitch.tv HOSTTARGET #{hosting} :{target} {amount}\r\n".format(
            hosting=HOSTING, target=TARGET, amount=AMOUNT)

        self.setAndConnect(msg)

    def test_on_stop_host_target(self):
        HOSTING = "hostingchannel"
        AMOUNT = 9001
        TARGET = None
        func = inspect.stack()[0][3]

        def onHostTarget(hosting, target, amount):
            self.assertEqual(hosting, HOSTING)
            self.assertEqual(target, TARGET)
            self.assertEqual(amount, AMOUNT)
            TestCallbacks.tests[func] = True

        self.chat.addCallbacks(onHostTarget=onHostTarget)
        msg = ":tmi.twitch.tv HOSTTARGET #{hosting} :- {amount}\r\n".format(
            hosting=HOSTING, amount=AMOUNT)

        self.setAndConnect(msg)

    def test_on_clear_chat_viewer(self):
        func = inspect.stack()[0][3]

        def onClearChat(channel, viewer):
            self.assertEqual(channel, self.CHANNEL)
            self.assertEqual(viewer, self.VIEWER)
            TestCallbacks.tests[func] = True

        self.chat.addCallbacks(onClearChat=onClearChat)
        msg = ":tmi.twitch.tv CLEARCHAT #{channel} :{viewer}\r\n".format(
            channel=self.CHANNEL, viewer=self.VIEWER)

        self.setAndConnect(msg)

    def test_on_clear_chat_channel(self):
        func = inspect.stack()[0][3]

        def onClearChat(channel, viewer):
            self.assertEqual(channel, self.CHANNEL)
            self.assertEqual(viewer, None)
            TestCallbacks.tests[func] = True

        self.chat.addCallbacks(onClearChat=onClearChat)
        msg = ":tmi.twitch.tv CLEARCHAT #{channel}\r\n".format(
            channel=self.CHANNEL)

        self.setAndConnect(msg)

    def test_on_usernotice(self):
        MSG = "Yo, NiCe StReAm BrUh!"
        func = inspect.stack()[0][3]

        def onUserNotice(channel, msg):
            self.assertEqual(channel, self.CHANNEL)
            self.assertEqual(msg, MSG)
            TestCallbacks.tests[func] = True

        self.chat.addCallbacks(onUserNotice=onUserNotice)
        msg = ":tmi.twitch.tv USERNOTICE #{channel} :{message}\r\n".format(
            channel=self.CHANNEL, message=MSG)

        self.setAndConnect(msg)

    def test_on_response_override(self):
        func = inspect.stack()[0][3]
        LINE = ":{viewer}!{viewer}@{viewer}.tmi.twitch.tv PRIVMSG #{channel} :{message}\r\n" \
            .format(viewer=self.VIEWER, channel=self.CHANNEL, message="This is a message")

        def onResponse(chat, line):
            self.assertIsNotNone(chat)
            self.assertEqual(line, LINE.replace("\r\n", ""))
            TestCallbacks.tests[func] = True

        self.tearDown()
        self.chat = IRC("nooauth", TestCallbacks.USER, onResponse=onResponse)
        self.chat._conn = MagicMock(name='socket', spec=socket.socket)
        self.setAndConnect(LINE)

    def test_on_pong_override(self):
        func = inspect.stack()[0][3]
        LINE = "PING :tmi.twitch.tv\r\n"

        def onPong(chat, line):
            self.assertIsNotNone(chat)
            self.assertEqual(line, LINE.replace("\r\n", ""))
            TestCallbacks.tests[func] = True

        self.tearDown()
        self.chat = IRC("nooauth", TestCallbacks.USER, onPong=onPong)
        self.chat._conn = MagicMock(name='socket', spec=socket.socket)
        self.setAndConnect(LINE)

    def test_on_reconnect_override(self):
        func = inspect.stack()[0][3]
        LINE = "RECONNECT :tmi.twitch.tv\r\n"

        def onReconnect(chat, line):
            self.assertIsNotNone(chat)
            self.assertEqual(line, LINE.replace("\r\n", ""))
            TestCallbacks.tests[func] = True

        self.tearDown()
        self.chat = IRC("nooauth", TestCallbacks.USER, onReconnect=onReconnect)
        self.chat._conn = MagicMock(name='socket', spec=socket.socket)
        self.setAndConnect(LINE)

    def test_zzzzz_tests_passed(self):
        for func, passed in TestCallbacks.tests.iteritems():
            self.assertTrue(passed, "Failed Function: {}".format(func))


if __name__ == '__main__':
    unittest.main()
