import inspect
import socket
import time
import unittest
from types import FunctionType

from mock import MagicMock

from twitchirc.irc import IRC


class mIRC(IRC):
    sock = MagicMock(name='socket', spec=socket.socket)

    def createSocket(self):
        return mIRC.sock


class TestCallbacks(unittest.TestCase):
    CHANNEL = "testchannel"
    VIEWER = "testviewer"
    USER = "testuser"
    tests = None

    def setUp(self):
        if not TestCallbacks.tests:
            TestCallbacks.tests = {}
            for x, y in TestCallbacks.__dict__.items():
                if type(y) == FunctionType and y.func_name[:4] == "test" and "zzzzz" not in y.func_name:
                    TestCallbacks.tests[y.func_name] = False

        self.login = ":tmi.twitch.tv 001 " + TestCallbacks.USER + "\r\n :tmi.twitch.tv 376 " + TestCallbacks.USER

    def tearDown(self):
        time.sleep(.005)  # allow the callbacks to be executed
        try:
            self.chat.shutdown()
        except AttributeError:
            pass

    def setAndConnect(self, msg, shebang='!', clz=mIRC):
        recvs = [self.login, '', '']
        recvs.extend(list(msg))
        mIRC.sock.recv.side_effect = recvs
        self.chat = clz("nooauth", TestCallbacks.USER, cmdShebang=shebang)
        self.chat.connect()

    def test_on_message(self):
        MESSAGE = "testmessage"
        func = inspect.stack()[0][3]

        def callback(irc, channel, viewer, message):
            self.assertIsNotNone(irc)
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            self.assertEqual(message, MESSAGE)
            TestCallbacks.tests[func] = True

        class TESTIRC(mIRC):
            def onMessage(self, channel, viewer, message):
                callback(self, channel, viewer, message)

        msg = ":{viewer}!{viewer}@{viewer}.tmi.twitch.tv PRIVMSG #{channel} :{message}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL, message=MESSAGE)

        self.setAndConnect(msg, clz=TESTIRC)

    def test_on_command(self):
        SHEBANG = "!"
        COMMAND = "command"
        VALUE = "value"
        func = inspect.stack()[0][3]

        def callback(irc, channel, viewer, command, value):
            self.assertIsNotNone(irc)
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            self.assertEqual(command, COMMAND)
            self.assertEqual(value, VALUE)
            TestCallbacks.tests[func] = True

        class TESTIRC(mIRC):
            def onCommand(self, channel, viewer, command, value):
                callback(self, channel, viewer, command, value)

        msg = ":{viewer}!{viewer}@{viewer}.tmi.twitch.tv PRIVMSG #{channel} :{shebang}{command} {value}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL, shebang=SHEBANG, command=COMMAND, value=VALUE)

        self.setAndConnect(msg, SHEBANG, TESTIRC)

    def test_on_command_with_shebang(self):
        SHEBANG = '#'
        COMMAND = "shebangcommand"
        VALUE = "shebangvalue"
        func = inspect.stack()[0][3]

        def callback(irc, channel, viewer, command, value):
            self.assertIsNotNone(irc)
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            self.assertEqual(command, COMMAND)
            self.assertEqual(value, VALUE)
            TestCallbacks.tests[func] = True

        class TESTIRC(mIRC):
            def onCommand(self, channel, viewer, command, value):
                callback(self, channel, viewer, command, value)

        msg = ":{viewer}!{viewer}@{viewer}.tmi.twitch.tv PRIVMSG #{channel} :{shebang}{command} {value}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL, shebang=SHEBANG, command=COMMAND, value=VALUE)

        self.setAndConnect(msg, SHEBANG, TESTIRC)

    def test_on_join(self):
        func = inspect.stack()[0][3]

        def callback(irc, channel, viewer, state):
            self.assertIsNotNone(irc)
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            self.assertEqual(state, IRC.JOIN)
            TestCallbacks.tests[func] = True

        class TESTIRC(mIRC):
            def onJoinPart(self, channel, viewer, state):
                callback(self, channel, viewer, state)

        msg = ":{viewer}!{viewer}@{viewer}.tmi.twitch.tv JOIN #{channel}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL)

        self.setAndConnect(msg, clz=TESTIRC)

    def test_on_part(self):
        func = inspect.stack()[0][3]

        def callback(irc, channel, viewer, state):
            self.assertIsNotNone(irc)
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            self.assertEqual(state, IRC.PART)
            TestCallbacks.tests[func] = True

        class TESTIRC(mIRC):
            def onJoinPart(self, channel, viewer, state):
                callback(self, channel, viewer, state)

        msg = ":{viewer}!{viewer}@{viewer}.tmi.twitch.tv PART #{channel}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL)

        self.setAndConnect(msg, clz=TESTIRC)

    def test_on_mode_op(self):
        OPCODE = IRC.OP
        func = inspect.stack()[0][3]

        def callback(irc, channel, viewer, opcode):
            self.assertIsNotNone(irc)
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            self.assertEqual(opcode, OPCODE)
            TestCallbacks.tests[func] = True

        class TESTIRC(mIRC):
            def onMode(self, channel, viewer, opcode):
                callback(self, channel, viewer, opcode)

        msg = ":jtv MODE #{channel} {op}o {viewer}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL, op=OPCODE)

        self.setAndConnect(msg, clz=TESTIRC)

    def test_on_mode_deop(self):
        OPCODE = IRC.DEOP
        func = inspect.stack()[0][3]

        def callback(irc, channel, viewer, opcode):
            self.assertIsNotNone(irc)
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(viewer, TestCallbacks.VIEWER)
            self.assertEqual(opcode, OPCODE)
            TestCallbacks.tests[func] = True

        msg = ":jtv MODE #{channel} {op}o {viewer}\r\n".format(
            viewer=TestCallbacks.VIEWER, channel=TestCallbacks.CHANNEL, op=OPCODE)

        class TESTIRC(mIRC):
            def onMode(self, channel, viewer, opcode):
                callback(self, channel, viewer, opcode)

        self.setAndConnect(msg, clz=TESTIRC)

    def test_on_notice_already_r9k_on(self):
        ID = IRC.ID_ALREADY_R9K_ON
        MSG = "This room is already in r9k mode."
        func = inspect.stack()[0][3]

        def callback(irc, channel, msgid, message):
            self.assertIsNotNone(irc)
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(msgid, ID)
            self.assertEqual(message, MSG)
            TestCallbacks.tests[func] = True

        msg = "@msg-id={id} :tmi.twitch.tv NOTICE #{channel} :{message}\r\n".format(
            id=ID, channel=TestCallbacks.CHANNEL, message=MSG)

        class TESTIRC(mIRC):
            def onNotice(self, channel, msgid, message):
                callback(self, channel, msgid, message)

        self.setAndConnect(msg, clz=TESTIRC)

    def test_on_notice_emote_only_on(self):
        ID = IRC.ID_EMOTE_ONLY_ON
        MSG = "This room is now in emote-only mode."
        func = inspect.stack()[0][3]

        def callback(irc, channel, msgid, message):
            self.assertIsNotNone(irc)
            self.assertEqual(channel, TestCallbacks.CHANNEL)
            self.assertEqual(msgid, ID)
            self.assertEqual(message, MSG)
            TestCallbacks.tests[func] = True

        msg = "@msg-id={id} :tmi.twitch.tv NOTICE #{channel} :{message}\r\n".format(
            id=ID, channel=TestCallbacks.CHANNEL, message=MSG)

        class TESTIRC(mIRC):
            def onNotice(self, channel, msgid, message):
                callback(self, channel, msgid, message)

        self.setAndConnect(msg, clz=TESTIRC)

    def test_on_host_target(self):
        HOSTING = "hostingchannel"
        TARGET = self.CHANNEL
        AMOUNT = 8675309
        func = inspect.stack()[0][3]

        def callback(irc, hosting, target, amount):
            self.assertIsNotNone(irc)
            self.assertEqual(hosting, HOSTING)
            self.assertEqual(target, TARGET)
            self.assertEqual(amount, AMOUNT)
            TestCallbacks.tests[func] = True

        msg = ":tmi.twitch.tv HOSTTARGET #{hosting} :{target} {amount}\r\n".format(
            hosting=HOSTING, target=TARGET, amount=AMOUNT)

        class TESTIRC(mIRC):
            def onHostTarget(self, hosting, target, amount):
                callback(self, hosting, target, amount)

        self.setAndConnect(msg, clz=TESTIRC)

    def test_on_stop_host_target(self):
        HOSTING = "hostingchannel"
        AMOUNT = 9001
        TARGET = None
        func = inspect.stack()[0][3]

        def callback(irc, hosting, target, amount):
            self.assertIsNotNone(irc)
            self.assertEqual(hosting, HOSTING)
            self.assertEqual(target, TARGET)
            self.assertEqual(amount, AMOUNT)
            TestCallbacks.tests[func] = True

        msg = ":tmi.twitch.tv HOSTTARGET #{hosting} :- {amount}\r\n".format(
            hosting=HOSTING, amount=AMOUNT)

        class TESTIRC(mIRC):
            def onHostTarget(self, hosting, target, amount):
                callback(self, hosting, target, amount)

        self.setAndConnect(msg, clz=TESTIRC)

    def test_on_clear_chat_viewer(self):
        func = inspect.stack()[0][3]

        def callback(irc, channel, viewer):
            self.assertIsNotNone(irc)
            self.assertEqual(channel, self.CHANNEL)
            self.assertEqual(viewer, self.VIEWER)
            TestCallbacks.tests[func] = True

        msg = ":tmi.twitch.tv CLEARCHAT #{channel} :{viewer}\r\n".format(
            channel=self.CHANNEL, viewer=self.VIEWER)

        class TESTIRC(mIRC):
            def onClearChat(self, channel, viewer):
                callback(self, channel, viewer)

        self.setAndConnect(msg, clz=TESTIRC)

    def test_on_clear_chat_channel(self):
        func = inspect.stack()[0][3]

        def callback(irc, channel, viewer):
            self.assertIsNotNone(irc)
            self.assertEqual(channel, self.CHANNEL)
            self.assertEqual(viewer, None)
            TestCallbacks.tests[func] = True

        msg = ":tmi.twitch.tv CLEARCHAT #{channel}\r\n".format(
            channel=self.CHANNEL)

        class TESTIRC(mIRC):
            def onClearChat(self, channel, viewer):
                callback(self, channel, viewer)

        self.setAndConnect(msg, clz=TESTIRC)

    def test_on_usernotice(self):
        MSG = "Yo, NiCe StReAm BrUh!"
        func = inspect.stack()[0][3]

        def callback(irc, channel, message):
            self.assertIsNotNone(irc)
            self.assertEqual(channel, self.CHANNEL)
            self.assertEqual(message, MSG)
            TestCallbacks.tests[func] = True

        msg = ":tmi.twitch.tv USERNOTICE #{channel} :{message}\r\n".format(
            channel=self.CHANNEL, message=MSG)

        class TESTIRC(mIRC):
            def onUserNotice(self, channel, message):
                callback(self, channel, message)

        self.setAndConnect(msg, clz=TESTIRC)

    def test_on_response_override(self):
        func = inspect.stack()[0][3]
        LINE = ":{viewer}!{viewer}@{viewer}.tmi.twitch.tv PRIVMSG #{channel} :{message}\r\n" \
            .format(viewer=self.VIEWER, channel=self.CHANNEL, message="This is a message")

        def callback(irc, line):
            self.assertIsNotNone(irc)
            self.assertEqual(line, LINE.replace("\r\n", ""))
            TestCallbacks.tests[func] = True

        class TESTIRC(mIRC):
            def onResponse(self, line):
                callback(self, line)

        self.setAndConnect(LINE, clz=TESTIRC)

    def test_on_ping_override(self):
        func = inspect.stack()[0][3]
        LINE = "PING :tmi.twitch.tv\r\n"

        def callback(irc):
            self.assertIsNotNone(irc)
            TestCallbacks.tests[func] = True

        class TESTIRC(mIRC):
            def onPing(self):
                callback(self)

        self.setAndConnect(LINE, clz=TESTIRC)

    def test_on_reconnect_override(self):
        func = inspect.stack()[0][3]
        LINE = "RECONNECT :tmi.twitch.tv\r\n"

        def callback(irc):
            self.assertIsNotNone(irc)
            TestCallbacks.tests[func] = True

        class TESTIRC(mIRC):
            def onReconnect(self):
                callback(self)

        self.setAndConnect(LINE, clz=TESTIRC)

    def test_zzzzz_tests_passed(self):
        for func, passed in TestCallbacks.tests.iteritems():
            self.assertTrue(passed, "Failed Function: {}".format(func))

if __name__ == '__main__':
    unittest.main()
