import os
import random
from os import listdir
from os.path import isfile, join

import discord
import soundfile
import speech_recognition as sr
from discord.ext import commands
from dotenv import load_dotenv

import spotipyApi as spotiApi

commandList = {
    1: {"command": "newReleases", "description": "You can list the new releases of this week!"},
    2: {"command": "createPlaylist", "description": "Asclepius can create a playlist  on spotify for you."},
    3: {"command": "getPlaylist", "description": "Asclepius can get your playlist."},
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


@client.event
async def on_ready():
    await client.wait_until_ready()
    await client.get_channel(GENEL).send(f'Ben geldim. 👑')
    print("I am ready")


@client.command()
async def hello(ctx):
    await ctx.send("Hello, I'm Asclepius.")


def speechRecognition():
    filename = "voiceOfAsclepius/records/newOut.wav"
    r = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data)
        print(text)


@client.command()
async def stopRecord(ctx):
    path = "voiceOfAsclepius/records"
    absolutePath = os.path.abspath(path)
    outFile = absolutePath + "/out.wav"
    command = f"ffmpeg -f s16le -ar 48000 -ac 2 -i " + path + "/merge.pcm" + " " + outFile
    os.system(command)
    os.remove(path + "/merge.pcm")
    data, samplerate = soundfile.read(outFile)
    soundfile.write(path + '/newOut.wav', data, samplerate, subtype="PCM_16")
    os.remove(outFile)
    speechRecognition()


@client.command()
async def breathe(ctx):
    gifs = [f for f in listdir("breatheExerciseGif") if isfile(join("breatheExerciseGif", f))]
    rand = random.randrange(0, len(gifs))
    gifPath = "breatheExerciseGif/" + gifs[rand]
    with open(gifPath, 'rb') as gif:
        exerciseGif = discord.File(gif)
        await ctx.send(file=exerciseGif)


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

    for release in spotiApi.getNewReleases().values.tolist():
        embed.add_field(name=(release[2] + " : " + release[1]), value=release[3], inline=False)

    await ctx.send(embed=embed)


@client.command(name="recommendMe")
async def recommendation(ctx):
    embed = discord.Embed(title="New Releases",
                          description="Recommendations from ASCLEPIUS ( ͡~ ͜ʖ ͡°)",
                          color=discord.Color.dark_gold())

    for rec in spotiApi.getRecommendationsForUser().values.tolist():
        embed.add_field(name=(rec[2] + " : " + rec[1]), value=rec[3], inline=False)

    await ctx.send(embed=embed)


@client.event
async def on_member_join(member):
    print("---------------")
    print(member)
    await member.create_dm()
    await member.dm_channel.send(f'Merhaba {member.name} hoşgeldin.')


@client.event
async def on_message(msg):
    if msg.author == client.user:
        return
    print(str(msg.content))
    if isinstance(msg.channel, discord.channel.DMChannel):
        await msg.channel.send(str(msg.content + " - from Asclepius"))

    await client.process_commands(msg)


@client.command(name="priTalk")
async def on_message(msg):
    member = msg.guild.get_member(msg.author.id)
    await member.create_dm()
    await member.dm_channel.send(f'Hadi konuşalım {member.name}. ')


@client.command(name="createPlaylist")
async def createPlaylist(ctx):
    embed = discord.Embed(title="NEW PLAYLIST",
                          description="ENJOY! -> " + spotiApi.createPlaylistForUser(),
                          color=discord.Color.dark_gold())

    await ctx.send(embed=embed)


@client.command(name="showPlaylist")
async def getPlaylist(ctx):
    embed = discord.Embed(title="Current Tracks in Playlist",
                          color=discord.Color.dark_green())

    for rec in spotiApi.getPlaylistItems().values.tolist():
        embed.add_field(name=rec[1], value=rec[2], inline=False)

    await ctx.send(embed=embed)


@client.command(name="getAlbum")
async def getAlbumTracks(ctx):
    embed = discord.Embed(title="Current Tracks in Album",
                          color=discord.Color.dark_magenta())

    for rec in spotiApi.getAlbums().values.tolist():
        embed.add_field(name=(rec[2] + " : " + rec[1]), value=rec[3], inline=False)

    await ctx.send(embed=embed)


@client.command(name="getPlaylist")
async def getPlaylist(ctx):
    embed = discord.Embed(title="Your Current Playlists",
                          color=discord.Color.dark_orange())

    for rec in spotiApi.getUserPlaylists().values.tolist():
        embed.add_field(name=rec[1], value=rec[2], inline=False)

    await ctx.send(embed=embed)


@client.command(name="topArtists")
async def getTopArtists(ctx):
    embed = discord.Embed(title="Your Favorite Artists",
                          color=discord.Color.dark_orange())

    for rec in spotiApi.getUserTopArtist().values.tolist():
        embed.add_field(name=rec[1], value="Genre: " + rec[2] + " " + rec[4], inline=False)

    await ctx.send(embed=embed)


@client.command(name="topTracks")
async def getTopTracks(ctx):
    embed = discord.Embed(title="Your Favorite Tracks",
                          color=discord.Color.blurple())

    for rec in spotiApi.getUserTopTracks().values.tolist():
        embed.add_field(name=(rec[2] + " : " + rec[1]), value=rec[3], inline=False)

    await ctx.send(embed=embed)


@client.command(name="saveShow")
async def saveShow(ctx):
    embed = discord.Embed(title="Asclepius saved the show for you.", description="Here's the available episodes.",
                          color=discord.Color.dark_teal())

    for rec in spotiApi.saveShowsForUser().values.tolist():
        embed.add_field(name=rec[1], value=rec[2], inline=False)

    await ctx.send(embed=embed)


@client.command(name="saveEp")
async def saveEpisode(ctx):
    ep = spotiApi.saveEpisodesForUser()
    print(ep)
    embed = discord.Embed(title="Asclepius saved the episode for you.",
                          description=ep.iat[0, 1] + " (>‿◠)✌" + ep.iat[0, 2],
                          color=discord.Color.blurple())

    await ctx.send(embed=embed)


@client.command(name="getSong")
async def getTrack(ctx):
    ep = spotiApi.getTrack('7ouMYWpwJ422jRcDASZB7P')
    print(ep)
    embed = discord.Embed(title="Here's the song!",
                          color=discord.Color.blurple())

    embed.add_field(name=ep.iat[0, 1], value=ep.iat[0, 2] + ": " + ep.iat[0, 3], inline=False)
    await ctx.send(embed=embed)


client.run(os.getenv('TOKEN'))
