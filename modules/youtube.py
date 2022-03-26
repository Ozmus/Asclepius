import requests
import discord
import os
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

def getVideoFromYoutube(searchTerm):
    response = requests.get(f'https://youtube.googleapis.com/youtube/v3/search?part=snippet&maxResults=10&q={searchTerm}&key={YOUTUBE_API_KEY}').json()
    # print(response)
    return response['items']

def getVideoDetails(videoId):
    response = requests.get(f'https://youtube.googleapis.com/youtube/v3/videos?part=contentDetails&part=statistics&id={videoId}&key={YOUTUBE_API_KEY}').json()
    # print(response)
    return response['items'][0]

def createEmbedForYoutube(video):
    videoTitle = video['snippet']['title']
    videoAuthor = video['snippet']['channelTitle']
    videoId = video['id']['videoId']
    videoDescription = video['snippet']['description']
    videoThumbnail = video['snippet']['thumbnails']['high']['url']
    videoDetails = getVideoDetails(videoId) # 0 content, 1 statistics
    videoViewCount = videoDetails['statistics']['viewCount']
    showComment = True
    try:
        videoCommentCount = videoDetails['statistics']['commentCount']
    except Exception:
        showComment = False

    videoCaption = videoDetails['contentDetails']['caption']

    embed=discord.Embed(title=videoTitle, url=f"https://www.youtube.com/watch?v={videoId}", description=videoDescription, color=discord.Color.red())
    embed.set_thumbnail(url=videoThumbnail)
    embed.set_author(name=videoAuthor)
    embed.add_field(name="Views", value=videoViewCount, inline=True)
    if showComment: embed.add_field(name="Comments", value=videoCommentCount, inline=True)
    embed.add_field(name="Caption", value= u'\u2713' if videoCaption == "true" else u'\u2717', inline=True)
    return embed

def createEmbedListForYoutube(searchTerm):
    videos = getVideoFromYoutube(searchTerm)
    embedList = []
    for video in videos:
        embedList.append(createEmbedForYoutube(video))

    return embedList


    