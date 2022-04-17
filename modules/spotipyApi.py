import os

import gspread
import pandas
import spotipy
from dotenv import load_dotenv
from spotipy import SpotifyOAuth

load_dotenv()
CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

gc = gspread.service_account(filename='asclepius-spotify-data.json')


def getUserTopArtist():
    SCOPE = 'user-top-read'
    spotifyInfo = getSpotifyInfo(SCOPE)

    artists = spotifyInfo.current_user_top_artists(limit=10, offset=0, time_range='short_term')['items']
    results = []

    for item in artists:
        obj = {'id': item['id'], 'name': item['name'], 'genres': ', '.join(str(genre) for genre in item['genres']),
               'href': item['href'],
               'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'genres', 'href', 'external_urls'])
    openWorksheet('User Top Artists').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def getUserTopTracks():
    SCOPE = 'user-top-read'
    spotifyInfo = getSpotifyInfo(SCOPE)
    artists = spotifyInfo.current_user_top_tracks(limit=10, offset=0, time_range='short_term')

    results = []

    for item in artists['items']:
        obj = {'id': item['id'], 'name': item['name'],
               'artist': ' '.join(n['name'] for n in item['album']['artists']),
               'href': item['href'], 'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'href', 'external_urls'])
    openWorksheet('User Top Tracks').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def getRecentlyPlayedTracks():
    SCOPE = 'user-read-recently-played'
    spotifyInfo = getSpotifyInfo(SCOPE)

    artists = spotifyInfo.current_user_recently_played(limit=10, after=None, before=None)['items']
    results = []

    for item in artists['items']:
        obj = {'id': item['id'], 'name': item['name'],
               'artist': ' '.join(n['name'] for n in item['album']['artists']),
               'href': item['href'], 'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'href', 'external_urls'])
    openWorksheet('User Recently Played Tracks').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def getRelatedArtists():
    spotifyInfo = getSpotifyInfo(None)
    artists = spotifyInfo.artist_related_artists(getUserTopArtist()['id'][0])['artists']
    results = []

    for item in artists:
        obj = {'id': item['id'], 'name': item['name'], 'genres': ', '.join(str(genre) for genre in item['genres'])}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'genres'])
    openWorksheet('Artist Related Artists').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def getSeveralArtists():
    spotifyInfo = getSpotifyInfo(None)

    artistList = ', '.join(artist['id'] for artist in getRelatedArtists())
    artists = spotifyInfo.artists(artistList)['artists']
    results = []

    for item in artists:
        obj = {'id': item['id'], 'name': item['name'], 'genres': ', '.join(str(genre) for genre in item['genres']),
               'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'genres', 'external_urls'])
    openWorksheet('Artists').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def getNewReleases():
    spotifyInfo = getSpotifyInfo(None)

    tracks = spotifyInfo.new_releases(country='TR', limit=20, offset=0, )['albums']['items']
    results = []

    for item in tracks:
        obj = {'id': item['id'], 'name': item['name'],
               'artist': ' '.join(n['name'] for n in item['artists']),
               'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'external_urls'])
    openWorksheet('New Releases').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def getTracks(trackName):
    tracks = search(trackName, "track")['tracks']['items']
    results = []

    for item in tracks:
        obj = {'id': item['album']['id'], 'name': item['album']['name'],
               'artist': ' '.join(n['name'] for n in item['album']['artists']),
               'external_urls': item['album']['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'external_urls'])
    return df


def getAlbums(albumName):
    df = storeAlbumData(search(albumName, "album")['albums']['items'])
    return df


def storeAlbumData(tracks):
    results = []
    for item in tracks:
        obj = {'id': item['id'], 'name': item['name'],
               'artist': ' '.join(n['name'] for n in item['artists']),
               'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'external_urls'])
    openWorksheet('Album Tracks').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def getAudioFeatures():
    spotifyInfo = getSpotifyInfo()

    trackList = ['7ouMYWpwJ422jRcDASZB7P', '2nTgdpxwpXTk5x1c9yaO3W']
    track = spotifyInfo.audio_features(trackList)
    results = []

    for item in track:
        obj = {'id': item['id'], 'acousticnes': item['acousticness'], 'danceability': item['danceability'],
               'duration_ms': item['duration_ms'], 'energy': item['energy'],
               'instrumentalness': item['instrumentalness'],
               'key': item['key'], 'loudness': item['loudness'], 'mode': item['mode'], 'tempo': item['tempo'],
               'valence': item['valence']}
        results.append(obj)

    df = pandas.DataFrame(results,
                          columns=['id', 'acousticnes', 'danceability', 'duration_ms', 'energy', 'instrumentalness',
                                   'key',
                                   'loudness', 'mode', 'tempo', 'valence'])
    openWorksheet('Tracks Audio Feature').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def getUserFollowedArtists():
    SCOPE = 'user-follow-read'
    spotifyInfo = getSpotifyInfo(SCOPE)

    followedArtists = spotifyInfo.current_user_followed_artists(limit=10)['artists']['items']
    results = []

    for item in followedArtists:
        obj = {'id': item['id'], 'name': item['name'], 'genres': ', '.join(str(genre) for genre in item['genres']),
               'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'genres', 'external_urls'])
    openWorksheet('User\'s Followed Artists').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def getUserPlaylists():
    SCOPE = 'playlist-read-private playlist-read-collaborative'
    spotifyInfo = getSpotifyInfo(SCOPE)

    playlists = spotifyInfo.current_user_playlists(limit=5, offset=0)['items']
    results = []

    for item in playlists:
        obj = {'id': item['id'], 'name': item['name'], 'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'external_urls'])
    openWorksheet('User Playlist').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def getPlaylistItems(playlistName):
    SCOPE = 'playlist-read-private'
    spotifyInfo = getSpotifyInfo(SCOPE)
    playlist = search(playlistName, "playlist")['playlists']['items'][0]['id']
    playlistItems = spotifyInfo.playlist_items(playlist, limit=15, offset=0)['items']
    df = storePlaylistData(playlistItems)
    return df


def storePlaylistData(playlistItems):
    results = []

    for item in playlistItems:
        obj = {'id': item['track']['id'], 'name': item['track']['name'],
               'external_urls': item['track']['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'external_urls'])
    openWorksheet('Playlist Items').update([df.columns.values.tolist()] + df.values.tolist())
    return df


# TODO id
def createPlaylistForUser(trackName):
    SCOPE = 'playlist-modify-public playlist-modify-private'
    spotifyInfo = getSpotifyInfo(SCOPE)
    trackList = []
    tracks = getRecommendationsForUser(trackName).values.tolist()
    for track in tracks:
        trackList.append(str(track[0]))

    response = spotifyInfo.user_playlist_create('nonolala99','just for you... from ASCLEPIUS')
    spotifyInfo.playlist_add_items(response['id'], trackList)
    return response['external_urls']['spotify']


def getCategoryPlaylists(category):
    spotifyInfo = getSpotifyInfo(None)

    playlists = spotifyInfo.category_playlists(category, limit=10, offset=5)['playlists']
    results = []
    for item in playlists['items']:
        obj = {'id': item['id'], 'name': item['name'], 'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'external_urls'])
    openWorksheet('Category Playlists').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def getAvailableGenreSeeds():
    spotifyInfo = getSpotifyInfo(None)

    genres = spotifyInfo.recommendation_genre_seeds()['genres']
    df = pandas.DataFrame(genres, columns=['genres'])
    openWorksheet('Available Genres').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def getRecommendationsForUser(trackName):
    spotifyInfo = getSpotifyInfo(None)
    artists = []
    tracks = []
    genres = []

    value = getRelatedArtists().values[0]
    artists.append(str(value[0]))
    genresList = getAvailableGenreSeeds().values
    genres.append(str(genresList[0][0]))
    tracks.append(str(search(trackName, "track")['tracks']['items'][0]['album']['id']))

    rec = spotifyInfo.recommendations(seed_artists=artists, seed_genres=genres, seed_tracks=tracks, limit=15)['tracks']
    results = []

    for item in rec:
        obj = {'id': item['id'], 'name': item['name'],
               'artist': ' '.join(n['name'] for n in item['artists']),
               'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'external_urls'])
    openWorksheet('Recommended Tracks').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def getUserSavedEpisodes():
    SCOPE = 'user-library-read'
    spotifyInfo = getSpotifyInfo(SCOPE)

    episodes = spotifyInfo.current_user_saved_episodes(limit=5, offset=0, market='US')['items']
    results = []

    for item in episodes:
        obj = {'id': item['episode']['id'], 'name': item['episode']['name'],
               'external_urls': item['episode']['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'external_urls'])
    openWorksheet('User Saved Episodes').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def getEpisodes(id):
    SCOPE = 'user-read-playback-position'
    spotifyInfo = getSpotifyInfo(SCOPE)

    episodes = spotifyInfo.show_episodes(id, limit=5, offset=0)['items']
    df = storeEpisodes(episodes)
    return df


def storeEpisodes(episodes):
    results = []

    for item in episodes:
        obj = {'id': item['id'], 'name': item['name'],
               'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'external_urls'])
    openWorksheet('Show Episodes').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def saveEpisodesForUser(episodeName):
    SCOPE = 'user-library-modify'
    spotifyInfo = getSpotifyInfo(SCOPE)
    episodeList = []
    episode = search(episodeName, "episode")['episodes']['items'][0]['id']
    episodeList.append(episode)
    spotifyInfo.current_user_saved_episodes_add(episodeList)
    return getEpisode(episodeList[0])


def getUserSavedShows():
    SCOPE = 'user-library-read'
    spotifyInfo = getSpotifyInfo(SCOPE)

    shows = spotifyInfo.current_user_saved_shows(limit=5, offset=0)['items']
    results = []

    for item in shows:
        obj = {'id': item['show']['id'], 'name': item['show']['name'],
               'external_urls': item['show']['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'external_urls'])
    openWorksheet('User Saved Shows').update([df.columns.values.tolist()] + df.values.tolist())
    return df


def saveShowsForUser(showName):
    SCOPE = 'user-library-modify'
    spotifyInfo = getSpotifyInfo(SCOPE)
    showList = []
    showId = search(showName, 'show')['shows']['items'][0]['id']
    showList.append(showId)
    spotifyInfo.current_user_saved_shows_add(showList)
    return getEpisodes(showId)


def getEpisode(id):
    SCOPE = 'user-read-playback-position'
    spotifyInfo = getSpotifyInfo(SCOPE)

    episode = spotifyInfo.episode(id)
    df = storeEpisodeData(episode)
    return df


def storeEpisodeData(episode):
    results = []

    obj = {'id': episode['id'], 'name': episode['name'],
           'external_urls': episode['external_urls']['spotify']}
    results.append(obj)
    df = pandas.DataFrame(results, columns=['id', 'name', 'external_urls'])
    return df


def getAudioAnalysis():
    spotifyInfo = getSpotifyInfo()

    track = spotifyInfo.audio_analysis('7ouMYWpwJ422jRcDASZB7P')

    obj = {'loudness': track['track']['loudness'], 'tempo': track['track']['tempo'],
           'tempo_confidence': track['track']['tempo_confidence'],
           'time_signature': track['track']['time_signature'],
           'time_signature_confidence': track['track']['time_signature_confidence'],
           'key': track['track']['key'], 'key_confidence': track['track']['key_confidence'],
           'mode': track['track']['mode'],
           'mode_confidence': track['track']['mode_confidence'], 'loudness': track['track']['loudness'],
           'tempo': track['sections']['tempo'],
           'tempo_confidence': track['sections']['tempo_confidence'], 'key': track['sections']['key'],
           'key_confidence': track['sections']['key_confidence'],
           'mode': track['sections']['mode'], 'mode_confidence': track['sections']['mode_confidence'],
           'time_signature': track['sections']['time_signature'],
           'time_signature_confidence': track['sections']['time_signature_confidence'],
           'start': track['segments']['start'], 'duration': track['segments']['duration'],
           'confidence': track['segments']['confidence'], 'loudness_start': track['segments']['loudness_start'],
           'loudness_max': track['segments']['loudness_max'],
           'loudness_max_time': track['segments']['loudness_max_time'],
           'loudness_end': track['segments']['loudness_end']}

    df = pandas.DataFrame(track, columns=['loudness', 'tempo', 'tempo_confidence', 'time_signature',
                                          'time_signature_confidence', 'key', 'key_confidence', 'mode',
                                          'mode_confidence', 'loudness', 'tempo', 'tempo_confidence', 'key',
                                          'key_confidence', 'mode', 'mode_confidence', 'time_signature',
                                          'time_signature_confidence', 'start', 'duration', 'confidence',
                                          'loudness_start', 'loudness_max', 'loudness_max_time', 'loudness_end'])
    return ""


def search(searchValue, searchType):
    spotifyInfo = getSpotifyInfo(None)
    results = spotifyInfo.search(searchValue, type=searchType)
    return results


def openWorksheet(sheetName):
    sheets = gc.open('Asclepius')
    return sheets.worksheet(title=sheetName)


def getSpotifyInfo(SCOPE):
    if SCOPE is None:
        return spotipy.Spotify(
            auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri="http://127.0.0.1:5000/"))

    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri="http://127.0.0.1:5000/",
                                  scope=SCOPE))
