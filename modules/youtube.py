import requests
import discord
import os
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

def getVideoFromYoutube(searchTerm, type):
    response = requests.get(f'https://youtube.googleapis.com/youtube/v3/search?part=snippet&type={type}&maxResults=10&q={searchTerm}&key={YOUTUBE_API_KEY}').json()
    # print(response)
    return response['items']

def getVideoDetails(videoId):
    response = requests.get(f'https://youtube.googleapis.com/youtube/v3/videos?part=contentDetails&part=statistics&id={videoId}&key={YOUTUBE_API_KEY}').json()
    # print(response)
    return response['items'][0]

def createEmbedForYoutube(media, type):
    print(media)
    mediaTitle = media['snippet']['title']
    mediaAuthor = media['snippet']['channelTitle']
    mediaDescription = media['snippet']['description']
    mediaThumbnail = media['snippet']['thumbnails']['high']['url']

    if (type == "video"):
        videoId = media['id']['videoId']
        videoDetails = getVideoDetails(videoId) # 0 content, 1 statistics
        videoViewCount = videoDetails['statistics']['viewCount']
        showComment = True
        try:
            videoCommentCount = videoDetails['statistics']['commentCount']
        except Exception:
            showComment = False

        videoCaption = videoDetails['contentDetails']['caption']

        embed=discord.Embed(title=mediaTitle, url=f"https://www.youtube.com/watch?v={videoId}", description=mediaDescription, color=discord.Color.red())
        embed.set_thumbnail(url=mediaThumbnail)
        embed.set_author(name=mediaAuthor)
        embed.add_field(name="Views", value=videoViewCount, inline=True)
        if showComment: embed.add_field(name="Comments", value=videoCommentCount, inline=True)
        embed.add_field(name="Caption", value= u'\u2713' if videoCaption == "true" else u'\u2717', inline=True)
        return embed
    else:
        playlistId = media['id']['playlistId']
        embed=discord.Embed(title=mediaTitle, url=f"https://www.youtube.com/playlist?list={playlistId}", description=mediaDescription, color=discord.Color.red())
        embed.set_thumbnail(url=mediaThumbnail)
        embed.set_author(name=mediaAuthor)
        return embed

def createEmbedListForYoutube(searchTerm, type):
    videos = getVideoFromYoutube(searchTerm,  type)
    embedList = []
    for video in videos:
        embedList.append(createEmbedForYoutube(video, type))
    return embedList


    