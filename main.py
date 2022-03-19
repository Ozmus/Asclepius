import os
import random
from os import listdir
from os.path import isfile, join

import discord
import speech_recognition as sr
import soundfile
import requests

from discord.ext import commands
from dotenv import load_dotenv
import requests
import json
import random
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
async def movie(ctx):
  film = get_film()
  await ctx.send(film['original_title'])
  
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
    gifPath = "breatheExerciseGif/"+gifs[rand]
    with open(gifPath, 'rb') as gif:
        exerciseGif = discord.File(gif)
        await ctx.send(file=exerciseGif)

@client.command()
async def youtube(ctx, *args):
    if(len(args) == 0):
        await ctx.send("Please give an argument")
        return

    videos = getVideoFromYoutube(args[0])
    topVideo = videos[0]
    embed = createEmbed(topVideo)
    await ctx.send(embed=embed)


client.run(TOKEN)
