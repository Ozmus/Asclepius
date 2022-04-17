import requests
import discord
import os
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
SAD_PLAYLIST_ID = "PL2gObORYlf30MDdc3JbP5S6wxZmxJsrW1"
HAPPY_PLAYLIST_ID = "PL2gObORYlf32qkIQbOsqe_milOnorHpuu"

def getVideoFromYoutube(searchTerm, type):
    response = requests.get(f'https://youtube.googleapis.com/youtube/v3/search?relevanceLanguage=en&part=snippet&type={type}&maxResults=10&q={searchTerm}&key={YOUTUBE_API_KEY}').json()
    return response['items']

def getVideoDetails(videoId):
    response = requests.get(f'https://youtube.googleapis.com/youtube/v3/videos?part=contentDetails&part=statistics&id={videoId}&key={YOUTUBE_API_KEY}').json()
    return response['items'][0]

def createEmbedForYoutube(media, type):
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

def getAsclepiusPlaylist(playlistId):
    response = requests.get(f'https://youtube.googleapis.com/youtube/v3/playlists?part=snippet&type=playlist&id={playlistId}&key={YOUTUBE_API_KEY}').json()
    return response['items'][0]

async def invokeYoutubeCommand(ctx, score):
    if score <=0:
        playlist = getAsclepiusPlaylist(SAD_PLAYLIST_ID)
        mediaDescription = playlist['snippet']['description']
        mediaThumbnail = playlist['snippet']['thumbnails']['high']['url']
        embed = discord.Embed(title="Stay strong, everthing will be great",
                            url=f"https://www.youtube.com/playlist?list={SAD_PLAYLIST_ID}",
                          description=mediaDescription,
                          color=discord.Color.red())
        embed.set_image(url=mediaThumbnail)
        embed.set_author(name="Asclepius")              
        await ctx.send(embed = embed)
    else:
        playlist = getAsclepiusPlaylist(HAPPY_PLAYLIST_ID)
        mediaDescription = playlist['snippet']['description']
        mediaThumbnail = playlist['snippet']['thumbnails']['high']['url']
        embed = discord.Embed(title="It is greaaat!!",
                            url=f"https://www.youtube.com/playlist?list={HAPPY_PLAYLIST_ID}",
                          description=mediaDescription,
                          color=discord.Color.red())
        embed.set_image(url=mediaThumbnail)
        embed.set_author(name="Asclepius")              
        await ctx.send(embed = embed)
    
async def youtubeCommandInfo(ctx) :
        embed = discord.Embed(title="Info",
                          description="To get a video please use the youtube command.",
                          color=discord.Color.blue())
        embed.add_field(name="Usage", value=">youtube searchTerm", inline=True)
        embed.add_field(name="Usage for Playlists", value=">youtube -p searchTerm", inline=True)
        # embed.set_author(name="Asclepius")              
        await ctx.send(embed = embed)
