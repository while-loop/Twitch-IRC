Twitch-IRC Callbacks
====================

- [IRC Chat Callbacks](#irc-chat-callbacks)
- [IRC Connection Callbacks](#irc-connection-callbacks)

IRC Chat Callbacks
------------------
Chat callbacks can be added via the method `addCallbacks()`. 
**Note:** previous callbacks will be removed if not added again.

The `onResponse` callback can be added via the constructor for `IRC`.

| callback       | description                                                                         | parameters                                                                       | example                                                                                     | notes                                                                                                                            |
| -------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------  | -------------------------------------------------------------------------------------------------------------------------------- |
| `onResponse`   | receive twitch commands or messages directly from the IRC socket (no prepossessing) | (IRC `irc`, string `line`)                                                       | ```:viewer!viewer@viewer.tmi.twitch.tv PRIVMSG #channel :message here```                    | if this callback is used, all callbacks mentioned below will not be handled by the IRC                                           |
| `onMessage`    | receive a user message from a channel                                               | (IRC `irc`, string `channel`, string `viewer`, string `message`)                 | ```:viewer!viewer@viewer.tmi.twitch.tv PRIVMSG #channel :message here```                    |                                                                                                                                  |
| `onCommand`    | receive a bot command by a user from a channel                                      | (IRC `irc`, string `channel`, string `viewer`, string `command`, string `value`) | ```:viewer!viewer@viewer.tmi.twitch.tv PRIVMSG #channel :!away I'll be back 8-D```          | a custom shebang can be given to the IRC constructor with `cmdShebang=`. The `value` variable may be `None` type                 |
| `onJoinPart`   | get notified when a viewer enters/leaves a channel irc                              | (IRC `irc`, string `channel`, string `viewer`, string `state`)                   | ```:viewer!viewer@viewer.tmi.twitch.tv JOIN #channel```                                     | the state variable can be accessed by `IRC.JOIN` or `IRC.PART`                                                                   |
| `onMode`       | get notified when a viewer gets opped/deopped (moderator status) in a channel irc   | (IRC `irc`, string `channel`, string `viewer`, string `state`)                   | ```:jtv MODE #channel +o viewer```                                                          | the state variable can be accessed by `IRC.OP` or `IRC.DEOP`                                                                     |
| `onNotice`     | general notices from the server (state change, feeback, etc)                        | (IRC `irc`, string `channel`, string `msgID`, string `message`)                  | ```@msg-id=slow_off :tmi.twitch.tv NOTICE #channel :This room is no longer in slow mode.``` | A list of channel notices can be found in the official IRC [documentation][msgid-docs]. MessageIDs can be accessed by `IRC.ID_*` |
| `onHostTarget` | notification when a channel starts/stops hosting another channel                    | (IRC `irc`, string `hostingChannel`, string `targetChannel`, int `amount`)       | ```:tmi.twitch.tv HOSTTARGET #hostingChannel :targetChannel 9001```                         | `targetChannel` may be `None` type if the command is a host stop command                                                         |
| `onClearChat`  | notification when a channel's/viewer's chat has been cleared                        | (IRC `irc`, string `channel`, string `viewer`)                                   | ```:tmi.twitch.tv CLEARCHAT #channel :viewer```                                             | `viewer` may be `None` type if the channel chat has been cleared                                                                 |
| `onUserNotice` | notice from a user currently only used for re-subscription messages                 | (IRC `irc`, string `channel`, string `message`)                                  | ```:tmi.twitch.tv USERNOTICE #channel :message```                                           |                                                                                                                                  |

IRC Connection Callbacks
------------------------
Connection callbacks can be added via the constructor for `IRC` using the parameters `onPing=` and `onReconnect`.

| callback      | description                                                | parameters                 | comments |
| ------------- | ---------------------------------------------------------- | -------------------------- | -------- |
| `onPing`      | receive callback when the IRC issues a `PING` request      | (IRC `irc`, string `line`) |          |
| `onReconnect` | receive callback when the IRC issues a `RECONNECT` request | (IRC `irc`, string `line`) |          |

[msgid-docs]: https://github.com/justintv/Twitch-API/blob/master/IRC.md#notice
