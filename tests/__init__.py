import re

reg = r"^:(\w+)!\1@\1\.tmi\.twitch\.tv\s+PRIVMSG\s+#(\w+)\s+:(.*)$"
line = ":testviewer!testviewer@testviewer.tmi.twitch.tv PRIVMSG #testchannel :testmessage"

regex = re.compile(reg)
match = regex.search(line)

if match:
    print match