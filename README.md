- What is this project?

CurrentlyCastingBot is a Discord bot written in Python for the purposes of maintaining
a channel in a Discord server (or "guild" to use its parlance) which will post a "call
to action" message when a monitored channel goes live on Twitch.tv. It will also watch
for any monitored channels to go _off_ the air and remove that message.  The end result
of this is a nice, clean channel containing only working links to live channels, and
no links to channels which are no longer live.  Any links to live thannels which are
not affirmatively monitored will also be removed.  This is a much cleaner look than a
`#self_promotion` channel containing pages and pages of links to the same short list
of channels, many or most of which may not even be on the air at the time a person is
perusing the channel.

- Main features

  - Fully automated posting and cleanup of "now live" messages
  - Variantly permuted flavor text to keep things from being too "samey"
  - Easy-to-update list of channels to monitor though messages within Discord
  - Easy to self-host with low overhead

- Installation Overview (full procedure in `INSTALL.md`)

  - Prepare a Discord and Twitch developer account and prepare API keys
  - Install required Python libraries
  - Set up configuration file
  - Create Discord bot
    - Set Discord bot permissions
    - Invite the bot
  - Run the bot
  - Add channels to The List

- Using the Bot

Once the bot has been configured and running, you should have two channels set up for
the bot:  One (which for instance we will call `#now_live`) for public consumption to 
which ideally only the bot will be able to post, but anyone on the Discord server can
read; and one (which for instance we will call `#bot_control`) which is used to issue
commands to the bot.  Commands for the bot will start with a prefix defined in the
configuration file (the example prefix given is `!`).  There are four commands which
the bot will respond to:

  - `!hello` - Causes the bot to respond with a brief message.  Can be used to verify
    the bot is up and running.
  - `!list` - Causes the bot to respond with a message consisting of an alphebetized
    list of all monitored Twitch channels.
  - `!watch dopeghoti` - Adds the Twtich channel which can be found at the URL
    https://twitch.tv/dopeghoti to The List.  This channel does not have to have any
    association with anyone on the Discord server.  The bot will respond indicating
    whether or not the addition was successful.
  - `!unwatch dopeghoti` - Removes the Twitch channel which can be found at the URL
    https://twitch.tv/dopeghoti from The List if it is present. The bot will respond
    with a message indicating whether or not the removal was successful.

- Planned Features

  - Configurable command verbs
  - Configurable procedural text in the "go-live" messages
  - Similar monitoring for YouTube channels

- Featureѕ Under Consideration

  - Role-based adding to or removing from The List for Discord profiles with linked
    Twitch accounts
  - Channel-specific callouts
  - Announcing of (and possibly updating up) the Category of a live channel
  - Per-channel callouts or "go-live" verbage
