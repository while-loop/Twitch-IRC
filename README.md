Twitch-IRC
==========

# LIBRARY IS IN DEVELOPMENT

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
---------------------
- Transparent Server reconnection (Needs testing)
- Well [tested](tests/) and [documented](docs/)
- Optional Moderator only bot
    - Mod only bots get an increase rate of 100 commands per 30 secs
    - Need to enforce that the bot is a mod before sending message
- Custom Command & Message rate limits

Changelog
---------

The format is based on [Keep a Changelog](http://keepachangelog.com/) 
and this project adheres to [Semantic Versioning](http://semver.org/).

[CHANGELOG.md](CHANGELOG.md)

License
-------
Twitch-IRC is licensed under the MIT license. See [LICENSE](LICENSE) for details.
