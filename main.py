from os import listdir
from os.path import isfile, join

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

    videos = getVideoFromYoutube(args[0])
    topVideo = videos[0]
    embed = createEmbed(topVideo)
    await ctx.send(embed=embed)


client.run(TOKEN)
