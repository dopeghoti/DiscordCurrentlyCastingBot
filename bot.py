#!/usr/bin/env python3
import os, re, random, discord, requests, curses
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord.ext.tasks import loop
from discord.ext.commands import Bot
from asyncio import sleep
from datetime import datetime
from channeldb import Database

load_dotenv()
TOKEN    = os.getenv( 'DISCORD_TOKEN'   )
GUILD    = os.getenv( 'DISCORD_GUILD'   )
PREFIX   = os.getenv( 'DISCORD_PREFIX'  )
CONTROL  = os.getenv( 'DISCORD_CONTROL' )
MONITOR  = os.getenv( 'DISCORD_MONITOR' )
TWITCH   = os.getenv( 'TWITCH_CLIENTID' )
TWITCH_S = os.getenv( 'TWITCH_SECRET' )
DATABASE = os.getenv( 'CHANNELS' )
WATCHLEN = int(os.getenv( 'WATCH_LENGTH' ))
DEBUG    = False
TOAUTH   = None

def log( message ):
    logfile = open( 'bot.log', 'a' )
    logfile.write( f'{datetime.now().strftime( "%Y-%m-%d %H:%M:%S" )} - {message}\n')
    logfile.close()

def err( message ):
    logfile = open( 'bot.err', 'a' )
    logfile.write( f'{datetime.now().strftime( "%Y-%m-%d %H:%M:%S" )} - {message}\n')
    logfile.close()

def handle_bad_token():
    global TOAUTH
    params = {
        'client_id': TWITCH,
        'client_secret': TWITCH_S,
        'grant_type': 'client_credentials'
    }
    url = 'https://id.twitch.tv/oauth2/token'
    log( 'Attempting to get new Twitch API OAuth token' )
    p = requests.post( url, data = params )
    log( f'API request attempt returned HTTP/{p.status_code}')
    if p.status_code == 200:
        TOAUTH = p.json()["access_token"]
        log( 'Obtained new Twitch API OAuth Token.' )
    else:
        err( f'Problem:  HTTP/{p.status_code} returned from Twitch API when fetching OAuth Token.' )

def get_online_streamers():
    if DEBUG:
        log( f'Now in get_online_streamers()' )
    channels = watchlist()
    if DEBUG:
        log( f'Fetched watchlist' )
    h = { f'Client-ID': TWITCH, 'Authorization': f'Bearer {TOAUTH}' }
    helix = 'https://api.twitch.tv/helix/streams?user_login='
    userstring="&user_login=".join( channels )
    if DEBUG:
        log( f'Prepped URL to fetch:\n{helix}{userstring}' )
        log( f'Headers:\n{h}' )
    r = requests.get( f'{helix}{userstring}', headers = h )
    if DEBUG:
        log( f'HTTP request made.  Response is HTTP/{r.status_code}.' )
    if r.status_code != 200:
        # The response code was not an expected value.
        err( f'HTTP/{r.status_code} received from API call.  Something went wrong.' )
        err( f'{r.content}' )
        if( r.status_code == 401 and 'Invalid OAuth token' in str( r.content ) ):
            err( f'Probably a bad OAuth Token.' )
            handle_bad_token()
        return []
    onlinechannels = []
    if DEBUG:
        log( f'{r.json()}' )
    for channel in r.json()['data']:
        if DEBUG:
            log( f'Found data for channel {channel}' )
        onlinechannels.append( channel['user_name'].lower() )
    if DEBUG:
        log( f'Parsed JSON response' )
    log( f'Online channels found: {onlinechannels}' )
    log( f'Twitch API pool:  {r.headers["ratelimit-remaining"]}' )
    return onlinechannels

def get_channel_status():
    if DEBUG:
        log( f'Starting get_channel_status()' )
    if DEBUG:
        log( f'Getting Watchlist' )
    channels = watchlist()
    if DEBUG:
        log( f'Got Watchlist' )
    if DEBUG:
        log( f'Calling get_onine_streamers()' )
    onlinechannels = get_online_streamers()
    if DEBUG:
        log( f'Returned from get_onine_streamers()' )
    channelstatus = {}
    if DEBUG:
        log( f'Starting to set channelstatus array' )
    for channel in channels:
        if channel.lower() in onlinechannels:
            channelstatus[channel.lower()] = True
        else:
            channelstatus[channel.lower()] = False
    if DEBUG:
        log( f'Starting get_channel_status()' )
    return channelstatus

def watch( user ):
    """Add a user to the database"""
    if user:
        if db.addToList( user ):
            log( f'User added: {user}' )
            return True
        else:
            log( f'Failed to add user: {user}' )
            return False
    else:
        log( 'watch() called without specifying user' )
        return False

def unwatch( user ):
    """Remove a user from the database"""
    if user:
        if db.removeFromList( user ):
            log( f'User removed: {user}' )
            return True
        else:
            log( f'Failed to remove user: {user}' )
            return False
    else:
        log( 'unwatch() called without specifying user' )
        return False

def is_watched( user ):
    """See whether a user is in the database"""
    return db.checkStreamerList( user )

def watchlist():
    """Return a List of every user in the database"""
    return db.getStreamerList()

bot = Bot( PREFIX )
#bot = Bot( command_prefix = PREFIX, help_command = 'info' )
db = Database()

@bot.event
async def on_ready():
    # all_channels = bot.get_all_channels()
    global MyServer, MonitorChannel, ControlChannel
    MyServer = bot.guilds[0]
    MonitorChannel = discord.utils.get( MyServer.text_channels, name = MONITOR )
    ControlChannel = discord.utils.get( MyServer.text_channels, name = CONTROL )
    log( f'{bot.user.name} has connected to the {MyServer.name} Discord.' )
    log( f'Monitoring channel #{MonitorChannel.name} (id: {MonitorChannel.id})' )
    log( f'Control channel    #{ControlChannel.name} (id: {ControlChannel.id})' )
    log( 'Initial startup complete' )

@bot.command( name='hello', help='Test routine responds with a random answer' )
async def hello_world( ctx ):
    MyServer = bot.guilds[0]
    MonitorChannel = discord.utils.get( MyServer.text_channels, name = MONITOR )
    ControlChannel = discord.utils.get( MyServer.text_channels, name = CONTROL )
    if ctx.channel.id != ControlChannel.id:
        return
    hello_answers = [
            'Hello, world',
            'Please state the nature of the Discord emergency.',
            'Roger roger',
            'By your command'
            ]
    response = random.choice( hello_answers )
    await ControlChannel.send( response )
    log( 'Hello, world' )

@bot.command( name='watch', help='Add a channel to the watch list' )
async def watch_channel( ctx, target ):
    MyServer = bot.guilds[0]
    ControlChannel = discord.utils.get( MyServer.text_channels, name = CONTROL )
    if ctx.channel.id != ControlChannel.id:
        return
    await ctx.channel.delete_messages( [ ctx.message ] )
    if watch( target ):
        await ControlChannel.send( f'{target.title()} added to The List.' )
    else:
        await ControlChannel.send( f'Unable to add {target.title()} to The List.' )

@bot.command( name='unwatch', help='Remove a channel from the watch list' )
async def unwatch_channel( ctx, target ):
    MyServer = bot.guilds[0]
    ControlChannel = discord.utils.get( MyServer.text_channels, name = CONTROL )
    if ctx.channel.id != ControlChannel.id:
        return
    await ctx.channel.delete_messages( [ ctx.message ] )
    if unwatch( target ):
        await ControlChannel.send( f'{target.title()} removed from The List.' )
    else:
        await ControlChannel.send( f'Unable to remove {target.title()} from The List.' )

@bot.command( name='purge', help='Clear messages in the monitor channel' )
async def purge( ctx, number ):
    MyServer = bot.guilds[0]
    MonitorChannel = discord.utils.get( MyServer.text_channels, name = MONITOR )
    ControlChannel = discord.utils.get( MyServer.text_channels, name = CONTROL )
    if ctx.channel.id != ControlChannel.id:
        return
    msgs = []
    number = int( number )
    msgs = await MonitorChannel.history( limit = number ).flatten()
    await MonitorChannel.delete_messages( msgs )

@bot.command( name='refresh', help='Manually refresh the Monitor Channel' )
async def refresh_channel( ctx ):
    pass

@bot.command( name='list', help='Report a list of everyone in the Database' )
async def report_list( ctx ):
    MyServer = bot.guilds[0]
    ControlChannel = discord.utils.get( MyServer.text_channels, name = CONTROL )
    if ctx.channel.id != ControlChannel.id:
        return
    streamers = watchlist()
    await ControlChannel.send( f'The current streamer list consists of {", ".join( streamers )}.' )

@bot.command( name='numbers', help='Call for Numbers', pass_context=True )
async def numbers_call( ctx, topic ):
    MyServer = bot.guilds[0]
    msg = await ctx.send( f'A call for Numbers has been made.   What are your feelings on {topic}?' )
    for n in ('one', 'two', 'three', 'four', 'five'):
        await bot.add_reaction( msg, n )

@bot.command( name='numbers?', help='Explain Numbers' )
async def numbers_call( ctx ):
    await ctx.send( 'TODO: Explain Numbers.' )

@loop( seconds = 90 )
async def find_messages():
    log( 'Tick start.' )
    MyServer = bot.guilds[0]
    MonitorChannel = discord.utils.get( MyServer.text_channels, name = MONITOR )
    # Find list of message with apparent Twitch URLs
    pattern = re.compile( r'twitch\.tv/([^-=?&/\s]+)')
    msgs = await MonitorChannel.history().flatten()
    log( 'Fetched Discord channel messages' )
    needles = {} # from the haystack of messages
    reportedchannels = []
    channelstatus = get_channel_status()
    log( f'Fetched Twitch channel status for {len(channelstatus)} channels.' )
    for twitcher in watchlist():
        # Collect list of channels which are a> online and b> on the List
        if channelstatus[ twitcher.lower() ]:
            reportedchannels.append( twitcher.lower() )
        else:
            pass
    log( 'Updated list of online watched channels' )
    for message in msgs:
        match = pattern.search( message.content )
        if match:
            needles[message] = match.groups()[0]
    # Purge messages which should not be present
    log( 'Starting message purge' )
    for message in needles.keys():
        if needles[message] in reportedchannels:
            pass
        else:
            # It's either a link to a stale channel or one that's not on the list
            log( f'{needles[message]} is not both live and listed.  Purging.' )
            # if needles[message] in watchlist():
                # update_watch( streamer = needles[message], online = False )
            await MonitorChannel.delete_messages( [ message ] )
    # Add messages which should be present
    log( 'Starting message posting' )
    for watchedchannel in watchlist():
        if ( watchedchannel in reportedchannels ) and ( watchedchannel not in needles.values() ):
            log( f'Posting a plug for {watchedchannel.title()}' )
            prefixes = [
                    'Guess what?',
                    'Look what I found!',
                    'What if I told you that',
                    'Breaking news:',
                    'Let me tell you a story.',
                    'No heckin'' way!',
                    'Want to hear a secret?',
                    'Is this thing on?',
                    'Major Tom to Ground Control:',
                    'O frabjous day!' ]
            actions = [
                    'is now broadcasting',
                    'has gone on the air',
                    'just went live',
                    'remembered to hit "Go Live"',
                    'has blessed us with eir presence',
                    'is presenting to the masses'
                    ]
            calls = [
                    'Check em out at',
                    'You can watch at',
                    'See eir slick moves at',
                    'Show some love- click',
                    'To watch, you can go to',
                    'Say hello at',
                    'Enjoy eir show at'
                    ]
            suffixes = [
                    'if you like.',
                    'at your convenience.',
                    '- don''t forget to like and subscribe!',
                    'and report back when they are finished.',
                    '- and remember your Twitch Prime sub!',
                    'should you feel so inclined',
                    'and let em know if eir mic has been muted this whole time.',
                    'to join the fun.'
                    ]
            response = f'{random.choice(prefixes)}\n`{watchedchannel.title()}` {random.choice(actions)}!\n{random.choice(calls)} https://twitch.tv/{watchedchannel} {random.choice(suffixes)}'
            await MonitorChannel.send( response )
        else:
            pass
    log( 'Tick end.' )
find_messages.before_loop( bot.wait_until_ready )
find_messages.start()

@bot.event
async def on_command_error( ctx, error ):
    MyServer = bot.guilds[0]
    MonitorChannel = discord.utils.get( MyServer.text_channels, name = MONITOR )
    ControlChannel = discord.utils.get( MyServer.text_channels, name = CONTROL )
    if ctx.channel.id not in ( ControlChannel.id, MonitorChannel.id ):
        return
    if isinstance( error, commands.CommandNotFound ):
        return
    raise error

try:
    bot.run(TOKEN)
except:
    raise

# db.close()
print( f"\nAaaand we're.. done?" )
log( 'Bot shutdown.' )
