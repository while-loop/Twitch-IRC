class Message:
    def __init__(self, channel, user, message):
        self.channel = channel  # channel to send message to
        self.user = user  # user that bot is responding to
        self.message = message  # message to be sent

    def __str__(self):
        return 'PRIVMSG #{channel} :{msg}'.format(channel=self.channel, msg=self.message)
