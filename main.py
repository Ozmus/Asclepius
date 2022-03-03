import discord
import os
from discord import Status
from discord.ext import commands
import random
from os import listdir
from os.path import isfile, join

import discord
import speech_recognition as sr
import soundfile

from discord.ext import commands
from dotenv import load_dotenv

client = commands.Bot(command_prefix=">")
load_dotenv()
GUILD = os.getenv('DISCORD_GUILD')
GENEL = os.getenv('DISCORD_GENEL')
intents = discord.Intents.all()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    await client.wait_until_ready()
    await client.get_channel(GENEL).send(f'Sahibiniz geldi 👑')

    for guild in client.guilds:
        if guild.name == "TOBB ETU SEVDALILARI":
            for member in guild.members:
                if member.status == discord.Status.online and member != client.user:
                    print(member, member.status)
                    await member.create_dm()
                    await member.dm_channel.send(f'Merhaba bebegim {member.name} imparatorluğuma hoşgeldin.')

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


@client.event
async def on_message(message):
    if message.content.startswith('$i'):
        await message.channel.send("Sahibim geldi :)")

    if message.content.startswith('$y'):
        await message.channel.send("Sahibimin kankisi geldi :) <3")
@client.command()
async def breathe(ctx):
    gifs = [f for f in listdir("breatheExerciseGif") if isfile(join("breatheExerciseGif", f))]
    rand = random.randrange(0, len(gifs))
    gifPath = "breatheExerciseGif/"+gifs[rand]
    with open(gifPath, 'rb') as gif:
        exerciseGif = discord.File(gif)
        await ctx.send(file=exerciseGif)

    if message.content.startswith('$hello'):
        await message.channel.send('Привет I am Asclepius.')



#@client.event
#async def on_private_channel_update(before, after):

client.run(os.getenv('TOKEN'))

