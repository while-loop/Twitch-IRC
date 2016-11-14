import unittest

from twitchirc.irc import IRC


class TestIRC(unittest.TestCase):
    def setUp(self):
        self.oauthToken = "oauthToken"
        self.oauthError = "Invalid Oauth token"
        self.username = "username"
        self.usernameError = "Invalid username"

    def test_unicode_oauth_token_passes(self):
        chat = IRC(unicode(self.oauthToken), self.username)
        self.assertIsNotNone(chat, "IRC returned None object")

    def test_string_oauth_token_passes(self):
        chat = IRC(str(self.oauthToken), self.username)
        self.assertIsNotNone(chat, "IRC returned None object")

    def test_none_oauth_token_passes(self):
        self._run_oauth_or_id_exception_test(None, self.oauthError)

    def test_list_oauth_token_raises_IRCError(self):
        self._run_oauth_or_id_exception_test(['list'], self.oauthError)

    def test_number_oauth_token_passes(self):
        self._run_oauth_or_id_exception_test(8675309, self.oauthError)

    def _run_oauth_or_id_exception_test(self, value, errorMsg):
        exceptionRaised = False
        try:
            IRC(value, self.username)
        except TypeError, e:
            exceptionRaised = True
            self.assertEqual(e.message, errorMsg, "IRC {} Exception message not matched".format(type(value)))
        self.assertTrue(exceptionRaised, "{} Exception was not raised".format(type(value)))


if __name__ == '__main__':
    unittest.main()
