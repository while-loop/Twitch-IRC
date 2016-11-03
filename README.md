Twitch-IRC
=====
Python Twitch.tv IRC library.

Features
--------
- Callbacks for many behind the scene functions
- Transparent Ping-Pong messaging
- Transparent Server reconnection
- Complies with Twitch IRC Command & Message [rate limits](https://help.twitch.tv/customer/portal/articles/1302780-twitch-irc)
    - 50 JOINs per 15 seconds
    - 20 commands or messages per 30 seconds 

Installation
------------
    pip install -e git+git://github.com/while-loop/Twitch-IRC.git#egg=twitchirc
Or

    pip install twitchirc
Or

    python setup.py install

Basic Usage
-----------


Future Updates / TODO
--------------
- Send messages to channels modded in using a different time interval
- Async I/O
- Handle Reconnection
- Verbose error handling
- Well tested and documented
- Optional Mod only bot
    - Mod only bots get an increase rate of 100 commands per 30 secs
    - Need to enforce that the bot is a mod before sending message


License
-------
Twitch-IRC is licensed under the MIT license. See [LICENSE](LICENSE) for details.
