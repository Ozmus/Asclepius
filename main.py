import random
from os import listdir
from os.path import isfile, join

from discord import FFmpegPCMAudio
from discord.ext import commands

import modules.spotipyApi as spotify
from modules.TheMovieDatabase import *
from modules.speechToText import stopSoundRecord
from modules.youtube import *

#TODO baska yere cekilecek konusulduktan sonra
commandList = {
    1: {"command": "newReleases", "description": "You can list the new releases of this week!"},
    2: {"command": "createPlaylist", "description": "Asclepius can create a playlist  on spotify for you."},
    3: {"command": "getMyPlaylist", "description": "Asclepius can get your playlist."},
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

load_dotenv()
GUILD = os.getenv('DISCORD_GUILD')
GENEL = os.getenv('DISCORD_GENEL')
ints = discord.Intents.all()
client = commands.Bot(command_prefix='>', intents=ints)

# client = discord.Client(intents=intents)
TOKEN = os.getenv('TOKEN')


@client.event
async def on_ready():
    print("I am ready")


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
async def getPoem(ctx):
    response = requests.get('https://www.poemist.com/api/v1/randompoems')
    r = response.json()
    r = r[0]
    embed = discord.Embed(title=r['title'], description=r['content'], color=discord.Color.random())
    embed.set_author(name=r['poet']['name'], icon_url=r['poet']['photo_avatar_url'])
    await ctx.send(embed=embed)


@client.command()
async def stopRecord(ctx):
    detectedIntent, fullfillmentText, sentimentScore = stopSoundRecord()
    await ctx.send(fullfillmentText)


@client.command()
async def playNatureSound(ctx):
    sounds = [f for f in listdir("natureSounds") if isfile(join("natureSounds", f))]
    rand = random.randint(0, len(sounds))
    soundPath = "natureSounds/" + sounds[rand]
    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        voice = await channel.connect()
        source = FFmpegPCMAudio(soundPath)
        player = voice.play(source)
    else:
        await ctx.send("Please join a voice channel and try again :)")


@client.command()
async def pauseNatureSound(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("There is no audio playing in the voice channel")


@client.command()
async def stopNatureSound(ctx):
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
async def changeNatureSound(ctx):
    sounds = [f for f in listdir("natureSounds") if isfile(join("natureSounds", f))]
    rand = random.randint(0, len(sounds))
    soundPath = "natureSounds/" + sounds[rand]
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
async def resumeNatureSound(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("There is no audio playing in the voice channel")


@client.command()
async def breathe(ctx):
    gifs = [f for f in listdir("breatheExerciseGif") if isfile(join("breatheExerciseGif", f))]
    rand = random.randrange(0, len(gifs))
    gifPath = "breatheExerciseGif/" + gifs[rand]
    with open(gifPath, 'rb') as gif:
        exerciseGif = discord.File(gif)
        await ctx.send(file=exerciseGif)


@client.command()
async def youtube(ctx, *args):
    if (len(args) == 0):
        await ctx.send("Please give an argument")
        return

    global embedListForYoutube
    global youtubeEmbedListIndex
    youtubeEmbedListIndex = 0
    embedListForYoutube = createEmbedListForYoutube(args[0])
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
async def asc(ctx):
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
    await member.dm_channel.send(f'Merhaba {member.name} hoşgeldin.')


@client.event
async def on_message(msg):
    if msg.author == client.user:
        return
    if isinstance(msg.channel, discord.channel.DMChannel):
        await msg.channel.send(str(msg.content + " - from Asclepius"))

    await client.process_commands(msg)


@client.command(name="priTalk")
async def on_message(msg):
    member = msg.guild.get_member(msg.author.id)
    await member.create_dm()
    await member.dm_channel.send(f'Hadi konuşalım {member.name}. ')


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


@client.command(name="getMyPlaylist")
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


# client.run(os.getenv('TOKEN'))
client.run(TOKEN)
