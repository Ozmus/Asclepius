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

client = commands.Bot(command_prefix=">")
load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
TOKEN = os.getenv('TOKEN')
@client.event
async def on_ready():
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

def getVideoFromYoutube(searchTerm):
    response = requests.get(f'https://youtube.googleapis.com/youtube/v3/search?part=snippet&maxResults=3&q={searchTerm}&key={YOUTUBE_API_KEY}').json()
    # print(response)
    return response['items']

def getVideoDetails(videoId):
    response = requests.get(f'https://youtube.googleapis.com/youtube/v3/videos?part=contentDetails&part=statistics&id={videoId}&key={YOUTUBE_API_KEY}').json()
    # print(response)
    return response['items'][0]

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
    videoTitle = topVideo['snippet']['title']
    videoAuthor = topVideo['snippet']['channelTitle']
    videoId = topVideo['id']['videoId']
    videoDescription = topVideo['snippet']['description']
    videoThumbnail = topVideo['snippet']['thumbnails']['high']['url']
    videoDetails = getVideoDetails(videoId) # 0 content, 1 statistics
    videoViewCount = videoDetails['statistics']['viewCount']
    showComment = True
    try:
        videoCommentCount = videoDetails['statistics']['commentCount']
    except Exception:
        showComment = False

    videoCaption = videoDetails['contentDetails']['caption']

    embed=discord.Embed(title=videoTitle, url=f"https://www.youtube.com/watch?v={videoId}", description=videoDescription, color=discord.Color.blue())
    embed.set_thumbnail(url=videoThumbnail)
    embed.set_author(name=videoAuthor)
    embed.add_field(name="Views", value=videoViewCount, inline=True)
    if showComment: embed.add_field(name="Comments", value=videoCommentCount, inline=True)
    embed.add_field(name="Caption", value= u'\u2713' if videoCaption == "true" else u'\u2717', inline=True)
    await ctx.send(embed=embed)


client.run(TOKEN)
