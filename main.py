import os
import random
from os import listdir
from os.path import isfile, join

import discord
import speech_recognition as sr
import soundfile

from discord.ext import commands
from dotenv import load_dotenv
import requests
import json
import random

load_dotenv()
client = discord.Client()

#document all the parameters as variables
Movie_db_API_key = os.getenv('TheMovieDatabaseAPIKey')
Movie_ID = '634649'
client = commands.Bot(command_prefix=">")


@client.event
async def on_ready():
    print("I am ready")


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



client.run(os.getenv('TOKEN'))
