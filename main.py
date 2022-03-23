from os import listdir
from os.path import isfile, join

from discord import FFmpegPCMAudio
from discord.ext import commands

import random

from modules.speechToText import stopSoundRecord
from modules.youtube import *
from modules.TheMovieDatabase import *

load_dotenv()
TOKEN = os.getenv('TOKEN')

client = discord.Client()

client = commands.Bot(command_prefix=">")


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
    rand = random.randint(0, len(gifs))
    gifPath = "breatheExerciseGif/" + gifs[rand]
    with open(gifPath, 'rb') as gif:
        exerciseGif = discord.File(gif)
        await ctx.send(file=exerciseGif)


@client.command()
async def youtube(ctx, *args):
    if (len(args) == 0):
        await ctx.send("Please give an argument")
        return

    videos = getVideoFromYoutube(args[0])
    topVideo = videos[0]
    embed = createEmbed(topVideo)
    await ctx.send(embed=embed)


client.run(TOKEN)
