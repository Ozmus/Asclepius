import discord
import os
from discord import Status
from discord.ext import commands
from dotenv import load_dotenv

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


@client.event
async def on_message(message):
    if message.content.startswith('$i'):
        await message.channel.send("Sahibim geldi :)")

    if message.content.startswith('$y'):
        await message.channel.send("Sahibimin kankisi geldi :) <3")

    if message.content.startswith('$hello'):
        await message.channel.send('Привет I am Asclepius.')



#@client.event
#async def on_private_channel_update(before, after):

client.run(os.getenv('TOKEN'))

