import discord
import os
from dotenv import load_dotenv
import requests
import json
import random

load_dotenv()
client = discord.Client()

#document all the parameters as variables
Movie_db_API_key = os.getenv('TheMovieDatabaseAPIKey')
Movie_ID = '634649'

@client.event
async def on_ready():
    print("I am ready yo!")

#loads genre list using get request from themoviedb
def load_genre_dictionary():
    genreDict = {}
    text = json.dumps(requests.get("https://api.themoviedb.org/3/genre/movie/list?api_key=", Movie_db_API_key, "&language=en-US").json())
    dataset = json.loads(text)
    for i in range(len(dataset['genres'])):
        genreDict[dataset['genres'][i]['id']] = dataset['genres'][i]['name']

    with open('genreDictionary', 'w') as genre_dict_file:
        genre_dict_file.write(json.dumps(genreDict))

def read_genre_dictionary():
    # reading the data from the file
    with open('genreDictionary') as genre_dict_file:
        genres = genre_dict_file.read()
    genreDict = json.loads(genres)
    return genreDict

def get_genre(genre_ID):
    genreDict = read_genre_dictionary()
    return genreDict[genre_ID]

#write a function to compose the query using the parameters provided
def get_data(Movie_db_API_key, Movie_ID):
    query = 'https://api.themoviedb.org/3/movie/' + Movie_ID + '?api_key=' + Movie_db_API_key + '&language=en-US'
    response = requests.get(query)
    if response.status_code==200:
    #status code ==200 indicates the API query was successful
        array = response.json()
        text = json.dumps(array)
        return array['original_title']
    else:
        return ("error")

def load_popular_film_list():
    filename = 'filmList'
    query = "https://api.themoviedb.org/3/movie/popular?api_key=" + Movie_db_API_key + "&language=en-US&page=1"
    text = json.dumps(requests.get(query).json())
    dataset = json.loads(text)
    datasetResults = dataset['results']
    filmList = []
    for i in range(len(datasetResults)):
        filmList.append({"id": datasetResults[i]['id']
                    , "original_title": datasetResults[i]['original_title']
                    , "genre_ids": datasetResults[i]['genre_ids']
                    , "vote_average": datasetResults[i]['vote_average']
                    , "overview": datasetResults[i]['overview']
                    , "poster_path": datasetResults[i]['poster_path']
                    , "popularity": datasetResults[i]['popularity']
                })

    with open(filename, 'w') as film_list_file:
        film_list_file.write(json.dumps(filmList))

def read_popular_film_list():
    filename = 'filmList'
    # reading the data from the file
    with open(filename) as film_list_file:
        films = film_list_file.read()
    filmList = json.loads(films)
    return filmList

def get_film():
    filmList = read_popular_film_list()
    return filmList[random.randint(0,19)]

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello I am Asclepius.')
    if message.content.startswith('$movie'):
        film = get_film()
        await message.channel.send(film['original_title'])

client.run(os.getenv('TOKEN'))