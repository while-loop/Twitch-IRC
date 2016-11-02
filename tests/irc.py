import unittest
from twitchirc.irc import IRC

from twitchirc.exception import IRCError


class TestIRC(unittest.TestCase):
    def setUp(self):
        self.clientID = "clientID"
        self.oauthToken = "oauthToken"
        self.oauthError = "Invalid Oauth token"
        self.clientIDError = "Invalid Client ID"

    def test_unicode_oauth_token_passes(self):
        chat = IRC(unicode(self.oauthToken), self.clientID)
        self.assertIsNotNone(chat)

    def test_string_oauth_token_passes(self):
        chat = IRC(str(self.oauthToken), self.clientID)
        self.assertIsNotNone(chat)

    def test_none_oauth_token_passes(self):
        self._run_oauth_or_id_exception_test(self.oauthToken, None, self.oauthError)

    def test_list_oauth_token_raises_IRCError(self):
        self._run_oauth_or_id_exception_test(self.oauthToken, ['list'], self.oauthError)

    def test_number_oauth_token_passes(self):
        self._run_oauth_or_id_exception_test(self.oauthToken, 8675309, self.oauthError)

    def _run_oauth_or_id_exception_test(self, type, value, errorMsg):
        exceptionRaised = False
        try:
            if type == self.oauthToken:
                IRC(value, self.clientID)
            else:
                IRC(self.oauthToken, value)
        except IRCError, e:
            exceptionRaised = True
            self.assertEqual(e.message, errorMsg, "IRC {} Exception message not matched".format(type))
        self.assertFalse(exceptionRaised, "{} Exception was not raised".format(type))


if __name__ == '__main__':
    unittest.main()
