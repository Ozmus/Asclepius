import random
import time
from os import listdir
from os.path import isfile, join

import discord
import youtube_dl as youtube_dl
from discord import FFmpegPCMAudio
from discord.ext import commands
from randfacts import randfacts

import modules.spotipyApi as spotify
from modules.TheMovieDatabase import *
from modules.dialogFlow import detectIntent
from modules.speechToText import stopSoundRecord
from modules.youtube import *
from modules.Twitter import *
from dynamoDB.DynamoDBService import *
from dynamoDB.GetTableEntry import *
from dynamoDB.InsertTableEntry import *

spotifyCommandList = {
    1: {"command": "***>newReleases***", "description": "You can list the new releases of this week!"},
    2: {"command": "***>createPlaylist {theme} ***",
        "description": "Asclepius can create a playlist on spotify for you. Just give it a theme."},
    3: {"command": "***>getMyPlaylists***", "description": "Asclepius can get your playlist."},
    4: {"command": "***>recommendMe {theme} ***",
        "description": "Asclepius' recommendations for you. Just give it a theme."},
    5: {"command": "***>saveShow {show name}***", "description": "Asclepius can save shows for you."},
    6: {"command": "***>saveEp{episode name}***", "description": "Asclepius can save episodes for you."},
    7: {"command": "***>getSong{song name}***", "description": "Asclepius can play the song for you."},
    8: {"command": "***>getAlbum{album name}***", "description": "Asclepius can play the album for you."},
    9: {"command": "***>showPlaylist{playlist name}***",
        "description": "Asclepius can show the tracks in the playlist for you."},
    10: {"command": "***>topTracks***", "description": "Asclepius knows your favorite tracks!"},
    11: {"command": "***>topArtists***", "description": "Asclepius knows your favorite artists!"},
    12: {"command": ">***priTalk***", "description": "Asclepius can talk with you in dm!"},
    13: {"command": "***topArtists-Voice Of Asclepius***",
         "description": "You can call voice of asclepius and say:\n- where are my top artists?\n- top artists\n- show me my top artists\n- who are my top artists?"},
    14: {"command": "***topTracks-Voice Of Asclepius***",
         "description": "You can call voice of asclepius and say:\n- what are my top tracks?\n- top tracks\n- show me my top tracks\n- where are my top tracks?"},
    15: {"command": "***createPlaylist-Voice Of Asclepius***",
         "description": "You can call voice of asclepius and say:\n- create new playlist\n- send me new playlist\n- I want new playlist\n- I want a playlist\n- create playlist for me"},
    16: {"command": "***getPlaylist-Voice Of Asclepius***",
         "description": "You can call voice of asclepius and say: get my playlists"},
    17: {"command": "***newReleases-Voice Of Asclepius***",
         "description": "You can call voice of asclepius and say: \n- send me new releases\n- show me new releases\n- what are the new releases\n- new releases"},
    18: {"command": "***recommend-Voice Of Asclepius***",
         "description": "You can call voice of asclepius and say: \n- recommend me something happy\n- recommend me something energetic\n- recommend me something fun"},
    19: {"command": "***recommend Sad-Voice Of Asclepius***",
         "description": "You can call voice of asclepius and say: \n- dark songs\n- sad songs\n- recommendme dark songs\n- recommend me sad songs"}
}

# TODO baska yere cekilecek konusulduktan sonra
commandList = {
    1: {"command": "***>spotifyCommands***", "description": "Asclepius can list the spotify commands."},
    2: {"command": "***>youtube searchTerm***",
        "description": "Asclepius can suggest a video from youtube about searchTerm."},
    3: {"command": "***>youtube -p searchTerm***",
        "description": "Asclepius can suggest a playlist from youtube about searchTerm."},
    4: {"command": "***>twitter***",
        "description": "Asclepius can look up your tweets to make a perfect movie and video suggestion for you."},
    5: {"command": "***>movie***", "description": "Asclepius can suggest a movie for you."},
    6: {"command": "***>getPoem***", "description": "Asclepius can read a poem for you."},
    7: {"command": "***>makeJoke***", "description": "Asclepius can make a funny joke for you."},
    8: {"command": "***>getQuote***", "description": "Asclepius can read a quote for you."},
    9: {"command": "***>recipe***", "description": "Asclepius can show a delicious recipe for you."},
    10: {"command": "***>playSound***", "description": "Asclepius can play a relaxing sound."},
    11: {"command": "***>record***", "description": "Asclepius starts listening your voice (works in Server)."},
    12: {"command": "***>stopRecord***", "description": "Asclepius finishes listening your voice (works in Server)."},
    13: {"command": "***>mindfulness***", "description": "Asclepius can show you a mindfulness exercise."},
    14: {"command": "***>breathe***", "description": "Asclepius shows you a breathe exercise with a gif"},
    15: {"command": ">***randomFact***", "description": "Asclepius gives a random fact"},
    16: {"command": ">***imbored***", "description": "Asclepius give a suggestion if you are bored"},
    17: {"command": ">***randomAdvice***", "description": "Asclepius can give an advice"},
    18: {"command": ">***trivia***", "description": "Asclepius can ask a question with hidden answer!"},
    19: {"command": "***>playPod***", "description": "Asclepius can play one of the popular podcasts."},
    20: {"command": "***>playThePod {searchTerm}***", "description": "Asclepius can play given podcast."},
    21: {"command": "***>playWithUrl***", "description": "Asclepius can play video with the given url"},
    22: {"command": "***>play {searchTerm}***", "description": "Asclepius can search and play given search term"},
}

currentSoundDirectory = ""

load_dotenv()

ints = discord.Intents.all()
client = commands.Bot(command_prefix='>', intents=ints)
client.remove_command("help")

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
async def mindfulness(ctx):
    f = open("mindfulness/jsonformatter.json")
    data = json.load(f)
    rand = random.randint(0, len(data))
    embed = discord.Embed(title="***" + data[rand]['title'] + "***", description="`" + data[rand]['instr'] + "`")
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
    embed.add_field(name=client.command_prefix + "stop", value="To stop sound and bot leaves")
    await ctx.send(embed=embed)


@client.event
async def on_guild_join(guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed()
            embed.set_image(
                url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Aesculap_147-.png/170px-Aesculap_147-.png")
            embed.add_field(name=">twitter",
                            value="`I'm Asclepius. I'm here to help you.` \n To list commands, you can write >help \n "
                                  "Also, we have voice bot to record your voice, if you don't want to write. This is the invite link: \n "
                                  "|| https://discord.com/api/oauth2/authorize?client_id=964912868036329543&permissions=120325187904&scope=bot ||")
            await channel.send(embed=embed)
            ctx = await client.get_context(guild)
            await help(ctx)
        break


@client.command()
async def stopRecord(ctx):
    await ctx.send("Please wait..")
    detectedIntent, fullfillmentText, sentimentScore = stopSoundRecord()
    await checkIntent(ctx, detectedIntent.display_name, fullfillmentText)


@client.command()
async def randomFact(ctx):
    x = randfacts.get_fact()
    await ctx.send(x)


@client.command()
async def randomAdvice(ctx):
    response = requests.get('https://api.adviceslip.com/advice')
    r = response.json()
    embed = discord.Embed(title=":sweat_smile: :thinking: :smile:", description="***" + r['slip']['advice'] + "***",
                          color=discord.Color.random())
    await ctx.send(embed=embed)


@client.command()
async def imbored(ctx):
    response = requests.get('https://www.boredapi.com/api/activity/')
    r = response.json()
    embed = discord.Embed(title="Are you BORED?! :zany_face:", description="```" + r['activity'] + "```",
                          color=discord.Color.random())
    await ctx.send(embed=embed)


@client.command()
async def trivia(ctx):
    response = requests.get('https://opentdb.com/api.php?amount=1')
    r = response.json()
    embed = discord.Embed(title=" :thinking_face: ***" + r['results'][0]['question'] + "***",
                          description=" *** The answer is ||" + r['results'][0]['correct_answer'] + "|| ***",
                          color=discord.Color.random())
    await ctx.send(embed=embed)


async def checkIntent(ctx, intent, fullfillmentText):
    if intent != "Youtube":  await ctx.send(fullfillmentText)
    if intent == 'createPlaylist':
        await createPlaylist(ctx)
    elif intent == 'newReleases':
        await newReleases(ctx)
    elif intent == 'recommend':
        await recommendation(ctx, "happy")
    elif intent == 'recommend Sad':
        await recommendation(ctx, "sad")
    elif intent == 'topArtists':
        await getTopArtists(ctx)
    elif intent == 'topTracks':
        await getTopTracks(ctx)
    elif intent == 'getPlaylist':
        await getTopTracks(ctx)
    elif intent == 'Twitter':
        await twitter(ctx)
    elif intent == 'Youtube':
        await youtubeCommandInfo(ctx)
    elif intent == 'Bad Feelings':
        await ctx.send('You can use these command to feel better.')
        await help(ctx)
    elif intent == 'Movie':
        film = get_film()
        await ctx.send(embed=film)


@client.command()
async def natureSound(ctx):
    voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    global currentSoundDirectory
    currentSoundDirectory = "sounds/natureSounds"
    sounds = [f for f in listdir("sounds/natureSounds")]
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
    sounds = [f for f in listdir("sounds/piano")]
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
    sounds = [f for f in listdir("sounds/chill")]
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
    print("Music is paused")
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
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    print("Music is resumed")
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("There is no audio playing in the voice channel")


@client.command()
async def breathe(ctx):
    gifs = [f for f in listdir("breatheExerciseGif")]
    rand = random.randint(0, len(gifs))
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
async def help(ctx):
    embed = discord.Embed(title="Commands",
                          description="Here's all the things Asclepius can do for you...",
                          color=discord.Color.blue())

    for id, command in commandList.items():
        embed.add_field(name=command["command"], value=command["description"], inline=True)
    await ctx.send(embed=embed)


@client.command()
async def spotifyCommands(ctx):
    embed = discord.Embed(title="Spotify Commands",
                          description="Here's all the things Asclepius can do for you...",
                          color=discord.Color.blue())

    for id, command in spotifyCommandList.items():
        embed.add_field(name=command["command"], value=command["description"], inline=True)
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
async def recommendation(ctx, *, arg1):
    embed = discord.Embed(title="New Releases",
                          description="Recommendations from ASCLEPIUS ( ͡~ ͜ʖ ͡°)",
                          color=discord.Color.dark_gold())

    for rec in spotify.getRecommendationsForUser(arg1).values.tolist():
        embed.add_field(name=(rec[2] + " : " + rec[1]), value=rec[3], inline=False)

    await ctx.send(embed=embed)


@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(f'Hi {member.name} welcome!.')


@client.event
async def on_message(msg):
    ctx = await client.get_context(msg)
    if msg.author == client.user:
        return
    if isinstance(msg.channel, discord.channel.DMChannel):
        detectedIntent, fullfillmentText, _ = detectIntent(msg.content)
        await checkIntent(ctx, detectedIntent.display_name, fullfillmentText)

    await client.process_commands(msg)


@client.command(name="priTalk")
async def on_message(msg):
    member = msg.guild.get_member(msg.author.id)
    await member.create_dm()
    await member.dm_channel.send(f'Lets talk {member.name}. ')


@client.command(name="createPlaylist")
async def createPlaylist(ctx, *, arg1="happy"):
    embed = discord.Embed(title="NEW PLAYLIST",
                          description="ENJOY! -> " + spotify.createPlaylistForUser(arg1),
                          color=discord.Color.dark_gold())

    await ctx.send(embed=embed)


@client.command(name="showPlaylist")
async def getPlaylist(ctx, *, arg1):
    embed = discord.Embed(title="Current Tracks in Playlist",
                          color=discord.Color.dark_green())

    for rec in spotify.getPlaylistItems(arg1).values.tolist():
        embed.add_field(name=rec[1], value=rec[2], inline=False)

    await ctx.send(embed=embed)


@client.command(name="getAlbum")
async def getAlbumTracks(ctx, *, arg1):
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
async def saveShow(ctx, *, arg1):
    embed = discord.Embed(title="Asclepius saved the show for you.", description="Here's the available episodes.",
                          color=discord.Color.dark_teal())

    for rec in spotify.saveShowsForUser(arg1).values.tolist():
        embed.add_field(name=rec[1], value=rec[2], inline=False)

    await ctx.send(embed=embed)


@client.command(name="saveEp")
async def saveEpisode(ctx, *, arg1):
    ep = spotify.saveEpisodesForUser(arg1)
    embed = discord.Embed(title="Asclepius saved the episode for you.",
                          description=ep.iat[0, 1] + " (>‿◠)✌" + ep.iat[0, 2],
                          color=discord.Color.blurple())

    await ctx.send(embed=embed)


@client.command(name="getSong")
async def getTrack(ctx, *, arg1):
    embed = discord.Embed(title="Here's the song!",
                          color=discord.Color.blurple())

    for rec in spotify.getTracks(arg1).values.tolist():
        embed.add_field(name=rec[1], value=rec[2] + ": " + rec[3], inline=False)
    await ctx.send(embed=embed)


@client.command(name='playWithUrl')
async def playWithUrl(ctx, url):
    await join(ctx)
    try:
        server = ctx.message.guild
        voice_channel = server.voice_client
        song_info = ytdl.extract_info(url, download=False)
        time.sleep(1)
        voice_channel.play(discord.FFmpegPCMAudio(song_info["formats"][0]["url"]))
        voice_channel.source = discord.PCMVolumeTransformer(voice_channel.source)
        voice_channel.source.volume = 1

    except:
        await ctx.send("The bot is not connected to a voice channel.")

@client.command(name='play')
async def play(ctx, *, searchTerm):
    await join(ctx)
    videos = getVideoFromYoutube(searchTerm,"video")
    videoId = videos[0]['id']['videoId']
    url = f"https://www.youtube.com/watch?v={videoId}"
    try:
        server = ctx.message.guild
        voice_channel = server.voice_client
        song_info = ytdl.extract_info(url, download=False)
        time.sleep(1)
        voice_channel.play(discord.FFmpegPCMAudio(song_info["formats"][0]["url"]))
        voice_channel.source = discord.PCMVolumeTransformer(voice_channel.source)
        voice_channel.source.volume = 1
    except:
        await ctx.send("The bot is not connected to a voice channel.")



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


@client.command(name='playThePod')
async def playPodcastSpecified(ctx, *, arg):
    await join(ctx)
    try:
        server = ctx.message.guild
        voice_channel = server.voice_client

        async with ctx.typing():
            source = getPodcastSpecified(arg)
            voice_channel.play(
                discord.FFmpegPCMAudio(source=source))
        await ctx.send('**Now playing:** {}'.format(source))
    except:
        await ctx.send("The bot is not connected to a voice channel.")


async def join(ctx):
    voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    if not ctx.message.author.voice:
        if voice_client is None:
            await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
            return
    else:
        channel = ctx.message.author.voice.channel
        if voice_client is None:
            await channel.connect()
        else:
            voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
            voice.stop()
            print("is voice playing", voice.is_playing())


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


def getPodcastSpecified(pod):
    response = requests.get("https://api.audioboom.com/audio_clips?find[query]=*" + str(pod) + "*")
    current_podcast = ""

    for audios in json.loads(response.text)['body']['audio_clips']:
        current_podcast = (audios['urls']['high_mp3'])
        print(current_podcast)

    return current_podcast


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
            await ctx.send("I'm glad you're happy :smile:")
        else:
            await ctx.send("Dont worry, everything's gonna be alright :hugging:")
        await ctx.send("Here is my movie and video suggestion for you :sunny:")
        film = get_film(sentiment_score)
        await ctx.send(embed=film)
        await invokeYoutubeCommand(ctx, sentiment_score)
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
                await ctx.send("I'm glad you're happy :smile:")
            else:
                await ctx.send("Dont worry, everything's gonna be alright :hugging:")
            await ctx.send("Here is my movie and video suggestion for you :sunny:")
            film = get_film(sentiment_score)
            await ctx.send(embed=film)
            await invokeYoutubeCommand(ctx, sentiment_score)


client.run(TOKEN)
