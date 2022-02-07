import os

from discord.ext import commands
from dotenv import load_dotenv

client = commands.Bot(command_prefix=">")
load_dotenv()


@client.event
async def on_ready():
    print("I am ready yo!")


@client.command()
async def hello(ctx):
    await ctx.send("Hello, I'm Asclepius.")


@client.command()
async def stopRecord(ctx):
    path = "voiceOfAsclepius/records"
    absolutePath = os.path.abspath(path)
    pcmFile = absolutePath + "/merge.pcm "
    outFile = absolutePath + "/out.mp3"
    command = f"ffmpeg -f s16le -ar 48000 -ac 2 -i " + path+"/merge.pcm" + " " + outFile
    os.system(command)
    os.remove(path+"/merge.pcm")


client.run(os.getenv('TOKEN'))
