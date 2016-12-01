Twitch-IRC Callbacks
====================

- [IRC Chat Functions](#irc-chat-functions)
- [IRC Connection Functions](#irc-connection-functions)

IRC Chat Functions
------------------
Chat callbacks can be added by `overriding` the desired functions

**Note:** Overriding the `onResponse` function can nullify all other IRC Chat functions.

| function       | description                                                                         | parameters                                                            | example                                                                                     | notes                                                                                                                            |
| -------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------  | -------------------------------------------------------------------------------------------------------------------------------- |
| `onResponse`   | receive twitch commands or messages directly from the IRC socket (no prepossessing) | (string `line`)                                                       | ```:viewer!viewer@viewer.tmi.twitch.tv PRIVMSG #channel :message here```                    | if this function is overridden, all functions mentioned below will not be handled by the IRC                                           |
| `onMessage`    | receive a user message from a channel                                               | (string `channel`, string `viewer`, string `message`)                 | ```:viewer!viewer@viewer.tmi.twitch.tv PRIVMSG #channel :message here```                    |                                                                                                                                  |
| `onCommand`    | receive a bot command by a user from a channel                                      | (string `channel`, string `viewer`, string `command`, string `value`) | ```:viewer!viewer@viewer.tmi.twitch.tv PRIVMSG #channel :!away I'll be back 8-D```          | a custom shebang can be given to the IRC constructor with `cmdShebang=`. The `value` variable may be `None` type                 |
| `onJoinPart`   | get notified when a viewer enters/leaves a channel irc                              | (string `channel`, string `viewer`, string `state`)                   | ```:viewer!viewer@viewer.tmi.twitch.tv JOIN #channel```                                     | the state variable can be accessed by `IRC.JOIN` or `IRC.PART`                                                                   |
| `onMode`       | get notified when a viewer gets opped/deopped (moderator status) in a channel irc   | (string `channel`, string `viewer`, string `state`)                   | ```:jtv MODE #channel +o viewer```                                                          | the state variable can be accessed by `IRC.OP` or `IRC.DEOP`                                                                     |
| `onNotice`     | general notices from the server (state change, feeback, etc)                        | (string `channel`, string `msgID`, string `message`)                  | ```@msg-id=slow_off :tmi.twitch.tv NOTICE #channel :This room is no longer in slow mode.``` | A list of channel notices can be found in the official IRC [documentation][msgid-docs]. MessageIDs can be accessed by `IRC.ID_*` |
| `onHostTarget` | notification when a channel starts/stops hosting another channel                    | (string `hostingChannel`, string `targetChannel`, int `amount`)       | ```:tmi.twitch.tv HOSTTARGET #hostingChannel :targetChannel 9001```                         | `targetChannel` may be `None` type if the command is a host stop command                                                         |
| `onClearChat`  | notification when a channel's/viewer's chat has been cleared                        | (string `channel`, string `viewer`)                                   | ```:tmi.twitch.tv CLEARCHAT #channel :viewer```                                             | `viewer` may be `None` type if the channel chat has been cleared                                                                 |
| `onUserNotice` | notice from a user currently only used for re-subscription messages                 | (string `channel`, string `message`)                                  | ```:tmi.twitch.tv USERNOTICE #channel :message```                                           |                                                                                                                                  |

IRC Connection Functions
------------------------
Connection callbacks can be added via the constructor for `IRC` using the parameters `onPing=` and `onReconnect`.

| function      | description                                                | parameters      | comments |
| ------------- | ---------------------------------------------------------- | --------------- | -------- |
| `onPing`      | receive callback when the IRC issues a `PING` request      | (string `line`) |          |
| `onReconnect` | receive callback when the IRC issues a `RECONNECT` request | (string `line`) |          |

[msgid-docs]: https://github.com/justintv/Twitch-API/blob/master/IRC.md#notice
