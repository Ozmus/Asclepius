#for guild in client.guilds:
 #   print(guild)
  #  if guild.name == "iremtos":
   #     for member in guild.members:
    #        if member.status == discord.Status.online and member != client.user:
     #           print(member, member.status)
      #      await member.create_dm()
       #     await member.dm_channel.send(f'Merhaba bebegim {member.name} imparatorluğuma hoşgeldin.')

import json
import os
import spotipy
import gspread
import pandas
from spotipy import SpotifyOAuth

CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

gc = gspread.service_account(filename='asclepius-spotify-data.json')


def getRelatedArtists():
    SCOPE = 'user-read-playback-position'
    spotifyInfo = spotipy.Spotify(
        auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI,
                                  scope=SCOPE))
    episode = spotifyInfo.episode('77o6BIVlYM3msb4MMIL1jH')
    results = []

    obj = {'id': episode['id'], 'name': episode['name'],
           'external_urls': episode['external_urls']['spotify']}
    results.append(obj)
    df = pandas.DataFrame(results, columns=['id', 'name', 'external_urls'])
    print(df)
    return 'DONE.'

getRelatedArtists()
