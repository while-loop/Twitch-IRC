Twitch-IRC
==========

# !!!LIBRARY IS IN DEVELOPMENT!!!

[![GitHub version](https://badge.fury.io/gh/while-loop%2FTwitch-IRC.svg)](https://badge.fury.io/gh/while-loop%2FTwitch-IRC) [![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/mit-license.php)   

Python Twitch.tv IRC library.

Features
--------
- Callbacks for many behind the scene functions
- Transparent Ping-Pong messaging
  - Includes optional onPing callback
- Verbose error messages
- Complies with Twitch IRC Command & Message [rate limits](https://help.twitch.tv/customer/portal/articles/1302780-twitch-irc)
    - 50 JOINs per 15 seconds
    - 20 commands/messages per 30 seconds
    - Optional Moderator only bot
        - Mod only bots get an increase rate of 100 commands per 30 secs

Installation
------------
    pip install -e git+git://github.com/while-loop/Twitch-IRC.git#egg=twitchirc
Or

    pip install twitchirc
Or

    python setup.py install

Basic Usage
-----------
Example of simple chat bot [here](docs/echo.py).

Example of complex chat bot [here](docs/example2.py).

#### Note
    For better efficiency, try to distribute channel loads to multiple bot instances on different IPs and connections

    Ex: 2 servers running 8 instances of Twitch-IRC each.
    208 channels in use. Each bot would manage 13 channels.

    Each bot would be able to send 20messages/30secs (100/30 for Mod bots) totaling 320messages/30secs (1600/30)
    across all bots.

[source1](https://discuss.dev.twitch.tv/t/max-messages-per-user-channel-ip/6321/3)
[source2](https://discuss.dev.twitch.tv/t/twitch-chat-limitations-for-mod-bots/986/13)

Future Updates / TODO
---------------------
- Transparent Server reconnection (Needs testing)
- Well [tested](tests/) and [documented](docs/)
- SSL/TLS
- Twitch IRC Tags
- Receive and parse Tags from twitch channel

Changelog
---------

The format is based on [Keep a Changelog](http://keepachangelog.com/) 
and this project adheres to [Semantic Versioning](http://semver.org/).

[CHANGELOG.md](CHANGELOG.md)

License
-------
Twitch-IRC is licensed under the MIT license. See [LICENSE](LICENSE) for details.
