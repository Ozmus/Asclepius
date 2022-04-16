#document all the parameters as variables
import json
import os

import discord
import requests
from numpy import random

Movie_db_API_key = os.getenv('TheMovieDatabaseAPIKey')

#loads genre list using get request from themoviedb
def load_genre_dictionary():
    genreDict = {}
    Movie_db_API_key = os.getenv('TheMovieDatabaseAPIKey')
    text = json.dumps(requests.get("https://api.themoviedb.org/3/genre/movie/list?api_key=" + Movie_db_API_key + "&language=en-US").json())
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
    Movie_db_API_key = os.getenv('TheMovieDatabaseAPIKey')
    filmList = []
    for pageNum in range(1 , 6):
        query = "https://api.themoviedb.org/3/movie/popular?api_key=" + Movie_db_API_key + "&language=en-US&page=" + str(pageNum)
        text = json.dumps(requests.get(query).json())
        dataset = json.loads(text)
        datasetResults = dataset['results']
        for i in range(len(datasetResults)):
            filmList.append({"id": datasetResults[i]['id']
                        , "original_title": datasetResults[i]['original_title']
                        , "genre_ids": datasetResults[i]['genre_ids']
                        , "vote_average": datasetResults[i]['vote_average']
                        , "overview": datasetResults[i]['overview']
                        , "poster_path": datasetResults[i]['poster_path']
                        , "popularity": datasetResults[i]['popularity']
                        , "release_date": datasetResults[i]['release_date']
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

def embed_film(film):
    embed = discord.Embed(title=film['original_title'],
                          description=film['overview'],
                          color=discord.Color.blue())
    embed.set_thumbnail(url='https://image.tmdb.org/t/p/original/' + film['poster_path'])
    embed.add_field(name="Release Date", value=film['release_date'], inline=True)
    embed.add_field(name="Vote Average", value=film['vote_average'], inline=True)
    return embed

def get_film(sentimentScore = 0):
    load_popular_film_list()
    filmList = read_popular_film_list()
    film = filmList[random.randint(0, len(filmList))]
    if(sentimentScore > 0):
        positiveFilmList=[]
        for film in filmList:
            if(80 in film['genre_ids']):
                positiveFilmList.append(film)
        film = positiveFilmList[random.randint(0, len(positiveFilmList))]
    elif(sentimentScore < 0):
        negativeFilmList = []
        for film in filmList:
            if (10751 in film['genre_ids']):
                negativeFilmList.append(film)
        film = negativeFilmList[random.randint(0, len(negativeFilmList))]
    else:
        film = filmList[random.randint(0, len(filmList))]
    embed = embed_film(film)
    return embed