import discord
import os
from dotenv import load_dotenv
import requests
import json
import csv

load_dotenv()
client = discord.Client()

#document all the parameters as variables
API_key = os.getenv('TheMovieDatabaseAPIKey')
Movie_ID = '464052'

@client.event
async def on_ready():
    print("I am ready yo!")

#write a function to compose the query using the parameters provided
def get_data(API_key, Movie_ID):
    query = 'https://api.themoviedb.org/3/movie/'+Movie_ID+'?api_key='+API_key+'&language=en-US'
    response = requests.get(query)
    if response.status_code==200:
    #status code ==200 indicates the API query was successful
        array = response.json()
        text = json.dumps(array)
        return (text)
    else:
        return ("error")

def write_file(filename, text):
    dataset = json.loads(text)
    csvFile = open(filename,'a')
    csvwriter = csv.writer(csvFile)
    #unpack the result to access the "collection name" element
    try:
        collection_name = dataset['belongs_to_collection']['name']
    except:
        #for movies that don't belong to a collection, assign null
        collection_name = None
    result = [dataset['original_title'],collection_name]
    # write data
    csvwriter.writerow(result)
    print (result)
    csvFile.close()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello I am Asclepius.')
    if message.content.startswith('$movie'):
        write_file('filmList', get_data(API_key, Movie_ID))
        #await message.channel.send(get_data(API_key, Movie_ID))

client.run(os.getenv('TOKEN'))

