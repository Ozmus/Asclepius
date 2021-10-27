import discord
import os
from dotenv import load_dotenv

client = discord.Client()
load_dotenv()
@client.event
async def on_ready():
    print("I am ready yo!")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello I am Asclepius.')

client.run(os.getenv('TOKEN'))

