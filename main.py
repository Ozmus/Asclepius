import random
from os import listdir
from os.path import isfile, join

import discord
import youtube_dl as youtube_dl
from discord import FFmpegPCMAudio
from discord.ext import commands

import modules.spotipyApi as spotify
from modules.TheMovieDatabase import *
from modules.dialogFlow import detectIntent
from modules.speechToText import stopSoundRecord
from modules.youtube import *
from modules.Twitter import *
from dynamoDB.DynamoDBService import *
from dynamoDB.GetTableEntry import *
from dynamoDB.InsertTableEntry import *

# TODO baska yere cekilecek konusulduktan sonra
commandList = {
    1: {"command": "newReleases", "description": "You can list the new releases of this week!"},
    2: {"command": "createPlaylist", "description": "Asclepius can create a playlist  on spotify for you."},
    3: {"command": "getMyPlaylists", "description": "Asclepius can get your playlist."},
    4: {"command": "recommendMe", "description": "Asclepius' recommendations for you."},
    5: {"command": "saveShow", "description": "Asclepius can save shows for you."},
    6: {"command": "saveEp", "description": "Asclepius can save episodes for you."},
    7: {"command": "getSong", "description": "Asclepius can play the song for you."},
    8: {"command": "getAlbum", "description": "Asclepius can play the album for you."},
    9: {"command": "showPlaylist", "description": "Asclepius can show the tracks in the playlist for you."},
    10: {"command": "topTracks", "description": "Asclepius knows your favorite tracks!"},
    11: {"command": "topArtists", "description": "Asclepius knows your favorite artists!"},
    12: {"command": "priTalk", "description": "Asclepius can talk with you in dm!"}
}

currentSoundDirectory = ""

load_dotenv()

ints = discord.Intents.all()
client = commands.Bot(command_prefix='>', intents=ints)

TOKEN = os.getenv('TOKEN')
clientDynamoDB, dynamoDB = connectDynamoDB()
createTables(clientDynamoDB, dynamoDB)

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

popular_podcast = []
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


@client.event
async def on_ready():
    print("I am ready")
    getPodcast()


@client.command()
async def makeJoke(ctx):
    f = open("jokeFile/jokes.json")
    data = json.load(f)
    rand = random.randint(0, 3772)
    embed = discord.Embed(description=data[rand]['body'])
    await ctx.send(embed=embed)


@client.command()
async def movie(ctx):
    film = get_film()
    await ctx.send(embed=film)


@client.command()
async def hello(ctx):
    await ctx.send("Hello, I'm Asclepius.")


@client.command()
async def getQuote(ctx):
    response = requests.get('https://api.quotable.io/random')
    r = response.json()
    embed = discord.Embed(title=r['content'], color=discord.Color.random())
    embed.set_footer(text=r['author'])
    await ctx.send(embed=embed)


@client.command()
async def recipe(ctx):
    try:
        response = requests.get('https://www.themealdb.com/api/json/v1/1/random.php')
        r = response.json()
        embed = discord.Embed(title=r['meals'][0]['strMeal'], color=discord.Color.random())
        embed.add_field(name="Category", value=r['meals'][0]['strCategory'], inline=False)
        embed.set_image(url=r['meals'][0]['strMealThumb'])
        embed.add_field(name="Youtube Link", value=r['meals'][0]['strYoutube'], inline=False)
        ingredients = [val for key, val in r['meals'][0].items() if "strIngredient" in key]
        ingredients = [x for x in ingredients if len(x) != 0 or len(x) != 1]
        measures = [val for key, val in r['meals'][0].items() if "strMeasure" in key]
        measures = [x for x in measures if len(x) != 0 or len(x) != 1]
        str = ""
        for i in range(0, len(measures)):
            str = str + measures[i] + " " + ingredients[i] + "\n"

        embed.add_field(name="Ingredients", value=str, inline=False)
        embed.add_field(name="Instructions", value="``For instructions, visit: `` " + r['meals'][0]['strSource'],
                        inline=False)
        await ctx.send(embed=embed)
    except:
        await ctx.send("Something went wrong. Please try again :(")


@client.command()
async def getPoem(ctx):
    response = requests.get('https://www.poemist.com/api/v1/randompoems')
    r = response.json()
    r = r[0]
    embed = discord.Embed(title=r['title'], description=r['content'], color=discord.Color.random())
    embed.set_author(name=r['poet']['name'], icon_url=r['poet']['photo_avatar_url'])
    await ctx.send(embed=embed)


@client.command()
async def playSound(ctx):
    embed = discord.Embed(color=discord.Color.random())
    embed.add_field(name=client.command_prefix + "natureSound", value="Plays nature sounds")
    embed.add_field(name=client.command_prefix + "piano", value="Plays piano sounds")
    embed.add_field(name=client.command_prefix + "chill", value="Plays chill musics")
    embed.add_field(name=client.command_prefix + "pause", value="To pause sound")
    embed.add_field(name=client.command_prefix + "resume", value="To resume sound")
    embed.add_field(name=client.command_prefix + "changeSound", value="To change sound")
    embed.add_field(name=client.command_prefix + "stop", value="To stop sound and bot leaves")
    await ctx.send(embed=embed)


def checkIntent(ctx, intent, fulfillmentText):
    if (intent == 'Twitter'):
        twitter(ctx)


@client.command()
async def stopRecord(ctx):
    detectedIntent, fullfillmentText, sentimentScore = stopSoundRecord()
    await ctx.send(fullfillmentText)


@client.command()
async def natureSound(ctx):
    voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    global currentSoundDirectory
    currentSoundDirectory = "sounds/natureSounds"
    sounds = [f for f in listdir("sounds/natureSounds") if isfile(join("sounds/natureSounds", f))]
    rand = random.randint(0, len(sounds))
    soundPath = "sounds/natureSounds/" + sounds[rand]
    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        if voice_client is not None:
            if voice_client.is_connected() == True:
                voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
                if voice.is_playing() or voice.is_paused():
                    voice.stop()
                    source = FFmpegPCMAudio(soundPath)
                    player = voice.play(source)
        else:
            voice = await channel.connect()
            source = FFmpegPCMAudio(soundPath)
            player = voice.play(source)
    else:
        await ctx.send("Please join a voice channel and try again :)")


@client.command()
async def piano(ctx):
    voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    global currentSoundDirectory
    currentSoundDirectory = "sounds/piano"
    sounds = [f for f in listdir("sounds/piano") if isfile(join("sounds/piano", f))]
    rand = random.randint(0, len(sounds))
    soundPath = "sounds/piano/" + sounds[rand]
    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        if voice_client is not None:
            if voice_client.is_connected() == True:
                voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
                if voice.is_playing() or voice.is_paused():
                    voice.stop()
                    source = FFmpegPCMAudio(soundPath)
                    player = voice.play(source)
        else:
            voice = await channel.connect()
            source = FFmpegPCMAudio(soundPath)
            player = voice.play(source)
    else:
        await ctx.send("Please join a voice channel and try again :)")


@client.command()
async def chill(ctx):
    voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    global currentSoundDirectory
    currentSoundDirectory = "sounds/chill"
    sounds = [f for f in listdir("sounds/chill") if isfile(join("sounds/chill", f))]
    rand = random.randint(0, len(sounds))
    soundPath = "sounds/chill/" + sounds[rand]
    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        if voice_client is not None:
            if voice_client.is_connected() == True:
                voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
                if voice.is_playing() or voice.is_paused():
                    voice.stop()
                    source = FFmpegPCMAudio(soundPath)
                    player = voice.play(source)
        else:
            voice = await channel.connect()
            source = FFmpegPCMAudio(soundPath)
            player = voice.play(source)
    else:
        await ctx.send("Please join a voice channel and try again :)")


@client.command()
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("There is no audio playing in the voice channel")


@client.command()
async def stop(ctx):
    voice = ctx.guild.voice_client
    voice.stop()
    await ctx.guild.voice_client.disconnect()


@client.event
async def on_voice_state_update(member, before, after):
    voice_state = member.guild.voice_client
    if voice_state is None:
        # Exiting if the bot it's not connected to a voice channel
        return

    if len(voice_state.channel.members) == 1:
        await voice_state.disconnect()


@client.command()
async def changeSound(ctx):
    sounds = [f for f in listdir(currentSoundDirectory) if isfile(join(currentSoundDirectory, f))]
    rand = random.randint(0, len(sounds))
    soundPath = currentSoundDirectory + "/" + sounds[rand]
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if ctx.author.voice:
        if voice.is_playing() or voice.is_paused():
            voice.stop()
            source = FFmpegPCMAudio(soundPath)
            player = voice.play(source)
        else:
            await ctx.send("There is no audio playing in the voice channel")
    else:
        await ctx.send("Please join a voice channel and try again :)")


@client.command()
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("There is no audio playing in the voice channel")


@client.command()
async def breathe(ctx):
    gifs = [f for f in listdir("breatheExerciseGif")]
    rand = random.randrange(0, len(gifs))
    gifPath = "breatheExerciseGif/" + gifs[rand]
    with open(gifPath, 'rb') as gif:
        exerciseGif = discord.File(gif)
        await ctx.send(file=exerciseGif)

# -p playlist, default video
@client.command()
async def youtube(ctx, *args):
    if (len(args) == 0):
        await ctx.send("Please give an argument")
        return

    global embedListForYoutube
    global youtubeEmbedListIndex
    if (len(args) == 1):
        youtubeEmbedListIndex = 0
        embedListForYoutube = createEmbedListForYoutube(args[0], "video")
        msg = await ctx.send(embed=embedListForYoutube[youtubeEmbedListIndex])
    elif (len(args) == 2 and args[0] == "-p"):
        youtubeEmbedListIndex = 0
        embedListForYoutube = createEmbedListForYoutube(args[1], "playlist")
        msg = await ctx.send(embed=embedListForYoutube[youtubeEmbedListIndex])
    await msg.add_reaction("⬅️")
    await msg.add_reaction("➡️")


@client.event
async def on_reaction_add(reaction, user):
    global embedListForYoutube
    global youtubeEmbedListIndex
    if user != client.user:
        if str(reaction.emoji) == "➡️":
            if youtubeEmbedListIndex < len(embedListForYoutube) - 1:
                youtubeEmbedListIndex = youtubeEmbedListIndex + 1
                await reaction.message.edit(embed=embedListForYoutube[youtubeEmbedListIndex])
            for reaction in reaction.message.reactions:
                await reaction.remove(user)
        if str(reaction.emoji) == "⬅️":
            if youtubeEmbedListIndex > 0:
                youtubeEmbedListIndex = youtubeEmbedListIndex - 1
                await reaction.message.edit(embed=embedListForYoutube[youtubeEmbedListIndex])
            for reaction in reaction.message.reactions:
                await reaction.remove(user)


@client.command()
async def commands(ctx):
    embed = discord.Embed(title="Commands",
                          description="Here's all the things Asclepius can do for you...",
                          color=discord.Color.blue())

    for id, command in commandList.items():
        embed.add_field(name=command["command"], value=command["description"], inline=False)
    await ctx.send(embed=embed)


@client.command(name="newReleases")
async def newReleases(ctx):
    embed = discord.Embed(title="New Releases",
                          description="Here's all the new releases",
                          color=discord.Color.blue())

    for release in spotify.getNewReleases().values.tolist():
        embed.add_field(name=(release[2] + " : " + release[1]), value=release[3], inline=False)

    await ctx.send(embed=embed)


@client.command(name="recommendMe")
async def recommendation(ctx, arg1):
    embed = discord.Embed(title="New Releases",
                          description="Recommendations from ASCLEPIUS ( ͡~ ͜ʖ ͡°)",
                          color=discord.Color.dark_gold())

    for rec in spotify.getRecommendationsForUser(arg1).values.tolist():
        embed.add_field(name=(rec[2] + " : " + rec[1]), value=rec[3], inline=False)

    await ctx.send(embed=embed)


@client.event
async def on_member_join(member):
    print(member)
    await member.create_dm()
    await member.dm_channel.send(f'Hi {member.name} welcome!.')


@client.event
async def on_message(msg):
    if msg.author == client.user:
        return
    if isinstance(msg.channel, discord.channel.DMChannel):
        _, fullfillmentText, _ = detectIntent(msg.content)
        await msg.channel.send(fullfillmentText)

    await client.process_commands(msg)


@client.command(name="priTalk")
async def on_message(msg):
    member = msg.guild.get_member(msg.author.id)
    await member.create_dm()
    await member.dm_channel.send(f'Lets talk {member.name}. ')


@client.command(name="createPlaylist")
async def createPlaylist(ctx, arg1):
    embed = discord.Embed(title="NEW PLAYLIST",
                          description="ENJOY! -> " + spotify.createPlaylistForUser(arg1),
                          color=discord.Color.dark_gold())

    await ctx.send(embed=embed)


@client.command(name="showPlaylist")
async def getPlaylist(ctx, arg1):
    embed = discord.Embed(title="Current Tracks in Playlist",
                          color=discord.Color.dark_green())

    for rec in spotify.getPlaylistItems(arg1).values.tolist():
        embed.add_field(name=rec[1], value=rec[2], inline=False)

    await ctx.send(embed=embed)


@client.command(name="getAlbum")
async def getAlbumTracks(ctx, arg1):
    embed = discord.Embed(title="Current Tracks in Album",
                          color=discord.Color.dark_magenta())

    for rec in spotify.getAlbums(arg1).values.tolist():
        embed.add_field(name=(rec[2] + " : " + rec[1]), value=rec[3], inline=False)

    await ctx.send(embed=embed)


@client.command(name="getMyPlaylists")
async def getPlaylist(ctx):
    embed = discord.Embed(title="Your Current Playlists",
                          color=discord.Color.dark_orange())

    for rec in spotify.getUserPlaylists().values.tolist():
        embed.add_field(name=rec[1], value=rec[2], inline=False)

    await ctx.send(embed=embed)


@client.command(name="topArtists")
async def getTopArtists(ctx):
    embed = discord.Embed(title="Your Favorite Artists",
                          color=discord.Color.dark_orange())

    for rec in spotify.getUserTopArtist().values.tolist():
        embed.add_field(name=rec[1], value="Genre: " + rec[2] + " " + rec[4], inline=False)

    await ctx.send(embed=embed)


@client.command(name="topTracks")
async def getTopTracks(ctx):
    embed = discord.Embed(title="Your Favorite Tracks",
                          color=discord.Color.blurple())

    for rec in spotify.getUserTopTracks().values.tolist():
        embed.add_field(name=(rec[2] + " : " + rec[1]), value=rec[3], inline=False)

    await ctx.send(embed=embed)


@client.command(name="saveShow")
async def saveShow(ctx, arg1):
    embed = discord.Embed(title="Asclepius saved the show for you.", description="Here's the available episodes.",
                          color=discord.Color.dark_teal())

    for rec in spotify.saveShowsForUser(arg1).values.tolist():
        embed.add_field(name=rec[1], value=rec[2], inline=False)

    await ctx.send(embed=embed)


@client.command(name="saveEp")
async def saveEpisode(ctx, arg1):
    ep = spotify.saveEpisodesForUser(arg1)
    embed = discord.Embed(title="Asclepius saved the episode for you.",
                          description=ep.iat[0, 1] + " (>‿◠)✌" + ep.iat[0, 2],
                          color=discord.Color.blurple())

    await ctx.send(embed=embed)


@client.command(name="getSong")
async def getTrack(ctx, arg1):
    embed = discord.Embed(title="Here's the song!",
                          color=discord.Color.blurple())

    for rec in spotify.getTracks(arg1).values.tolist():
        embed.add_field(name=rec[1], value=rec[2] + ": " + rec[3], inline=False)
    await ctx.send(embed=embed)


@client.command(name='playSong')
async def play(ctx, url):
    await join(ctx)
    try:
        server = ctx.message.guild
        voice_channel = server.voice_client
        song_info = ytdl.extract_info(url, download=False)
        voice_channel.play(discord.FFmpegPCMAudio(song_info["formats"][0]["url"]))
        voice_channel.source = discord.PCMVolumeTransformer(voice_channel.source)
        voice_channel.source.volume = 1

    except:
        await ctx.send("The bot is not connected to a voice channel.")


@client.event
async def on_guild_join(guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send('Hey there! this is the message i send when i join a server')
        break


@client.command(name='playPod')
async def playPodcast(ctx):
    await join(ctx)
    try:
        server = ctx.message.guild
        voice_channel = server.voice_client

        async with ctx.typing():
            source = popular_podcast[random.randint(0, len(popular_podcast) - 1)]
            voice_channel.play(
                discord.FFmpegPCMAudio(source=source))
        await ctx.send('**Now playing:** {}'.format(source))
    except:
        await ctx.send("The bot is not connected to a voice channel.")


async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()


@client.command(name='leave')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


def getPodcast():
    response = requests.get("https://api.audioboom.com/audio_clips/popular")
    for audios in json.loads(response.text)['body']['audio_clips']:
        popular_podcast.append(audios['urls']['high_mp3'])


@client.command()
async def twitter(ctx):
    isAuthorizedUser = True
    discord_id = str(ctx.author.id)
    try:
        twitter_credentials = get_twitter_credentials(dynamo_db=dynamoDB, discord_id=discord_id)
        tweets = getTweetsKnownAccessToken(twitter_credentials['access_token'],
                                           twitter_credentials['access_token_secret'],
                                           twitter_credentials['username'])
        sentiment_score = getSentimentResult(tweets)
        if sentiment_score > 0:
            await ctx.send("Happy for you :)")
        else:
            await ctx.send("Sorry for you :(")
    except:
        isAuthorizedUser = False

        if not isAuthorizedUser:
            authToken, authTokenSecret, authorizationURL = authorizationTwitter()
            await ctx.send(f"Click the following URL and paste the PIN to authorize your Twitter account. "
                           f"\n → {authorizationURL}")

            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel

            msg = await client.wait_for("message", check=check)
            authorizationPin = msg.content
            access_token, access_token_secret, user_id, screen_name = get_user_access_tokens(authToken,
                                                                                             authTokenSecret,
                                                                                             authorizationPin)
            add_twitter_credentials(dynamo_db=dynamoDB, discord_id=discord_id, username=screen_name, user_id=user_id,
                                    access_token=access_token, access_token_secret=access_token_secret)
            tweets = getTweets(access_token, access_token_secret, screen_name)
            sentiment_score = getSentimentResult(tweets)
            if sentiment_score > 0:
                await ctx.send("Happy for you :)")
            else:
                await ctx.send("Sorry for you :(")


client.run(TOKEN)
