from flask import (
    abort,
    Flask,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
import json
import logging
import os
import requests
import secrets
import string
import spotipy
import gspread
import pandas
from urllib.parse import urlencode

from spotipy import SpotifyOAuth

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

# Client info
CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

gc = gspread.service_account(filename='asclepius-spotify-data.json')

# Spotify API endpoints
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
ME_URL = 'https://api.spotify.com/v1/me'

# Start 'er up
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/<loginout>')
def login(loginout):
    '''Login or logout user.
    Note:
        Login and logout process are essentially the same. Logout forces
        re-login to appear, even if their token hasn't expired.
    '''

    # redirect_uri can be guessed, so let's generate
    # a random `state` string to prevent csrf forgery.
    state = ''.join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16)
    )

    # Request authorization from user
    scope = 'user-read-private user-read-email'

    if loginout == 'logout':
        payload = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'state': state,
            'scope': scope,
            'show_dialog': True,
        }
    elif loginout == 'login':
        payload = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'state': state,
            'scope': scope,
        }
    else:
        abort(404)

    res = make_response(redirect(f'{AUTH_URL}/?{urlencode(payload)}'))
    res.set_cookie('spotify_auth_state', state)

    return res


@app.route('/callback')
def callback():
    error = request.args.get('error')
    code = request.args.get('code')
    state = request.args.get('state')
    stored_state = request.cookies.get('spotify_auth_state')

    # Check state
    if state is None or state != stored_state:
        app.logger.error('Error message: %s', repr(error))
        app.logger.error('State mismatch: %s != %s', stored_state, state)
        abort(400)

    # Request tokens with code we obtained
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
    }

    # `auth=(CLIENT_ID, SECRET)` basically wraps an 'Authorization'
    # header with value:
    # b'Basic ' + b64encode((CLIENT_ID + ':' + SECRET).encode())
    res = requests.post(TOKEN_URL, auth=(CLIENT_ID, CLIENT_SECRET), data=payload)
    res_data = res.json()

    if res_data.get('error') or res.status_code != 200:
        app.logger.error(
            'Failed to receive token: %s',
            res_data.get('error', 'No error information received.'),
        )
        abort(res.status_code)

    # Load tokens into session
    session['tokens'] = {
        'access_token': res_data.get('access_token'),
        'refresh_token': res_data.get('refresh_token'),
    }

    return redirect(url_for('me'))


@app.route('/refresh')
def refresh():
    '''Refresh access token.'''

    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': session.get('tokens').get('refresh_token'),
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    res = requests.post(
        TOKEN_URL, auth=(CLIENT_ID, CLIENT_SECRET), data=payload, headers=headers
    )
    res_data = res.json()

    # Load new token into session
    session['tokens']['access_token'] = res_data.get('access_token')

    return json.dumps(session['tokens'])


@app.route('/me')
def me():
    global user_data
    '''Get profile info as a API example.'''

    # Check for tokens
    if 'tokens' not in session:
        app.logger.error('No tokens in session.')
        abort(400)

    # Get profile info
    headers = {'Authorization': f"Bearer {session['tokens'].get('access_token')}"}

    res = requests.get(ME_URL, headers=headers)
    user_data = res.json()

    if res.status_code != 200:
        app.logger.error(
            'Failed to get profile info: %s',
            user_data.get('error', 'No error message returned.'),
        )
        abort(res.status_code)

    return render_template('me.html', data=user_data, tokens=session.get('tokens'))


@app.route('/user-topArtists', methods=['GET'])
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


@app.route('/topTracks', methods=['GET'])
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


@app.route('/user/recentlyPlayedTracks', methods=['GET'])
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
    return 'OK.'


@app.route('/user/relatedArtists', methods=['GET'])
def getRelatedArtists():
    spotifyInfo = getSpotifyInfo()

    artists = spotifyInfo.artist_related_artists('2RQ8NtUmg5y6tfbvCwX8jI')['artists']
    results = []

    for item in artists:
        obj = {'id': item['id'], 'name': item['name'], 'genres': ', '.join(str(genre) for genre in item['genres'])}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'genres'])
    openWorksheet('Artist Related Artists').update([df.columns.values.tolist()] + df.values.tolist())
    return 'DONE.'


@app.route('/user/artists', methods=['GET'])
def getSeveralArtists():
    spotifyInfo = getSpotifyInfo()

    artistList = ['2RQ8NtUmg5y6tfbvCwX8jI', '6S2OmqARrzebs0tKUEyXyp', '3ABivHBm6ULD624ig1lgOg']
    artists = spotifyInfo.artists(artistList)['artists']
    results = []

    for item in artists:
        obj = {'id': item['id'], 'name': item['name'], 'genres': ', '.join(str(genre) for genre in item['genres']),
               'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'genres', 'external_urls'])
    openWorksheet('Artists').update([df.columns.values.tolist()] + df.values.tolist())
    return 'DONE.'


@app.route('/user/newReleases', methods=['GET'])
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


@app.route('/tracks', methods=['GET'])
def getTracks():
    spotifyInfo = getSpotifyInfo()

    trackList = ['7ouMYWpwJ422jRcDASZB7P', '4VqPOruhp5EdPBeR92t6lQ', '2takcwOaAZWiXQijPHIx7B']
    tracks = spotifyInfo.tracks(trackList, market=None)['tracks']
    results = []

    for item in tracks:
        obj = {'id': item['id'], 'name': item['name'],
               'artist': ' '.join(n['name'] for n in item['artists']),
               'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'external_urls'])
    openWorksheet('Tracks').update([df.columns.values.tolist()] + df.values.tolist())
    return 'OK.'


@app.route('/tracks', methods=['GET'])
def getTrack(id):
    spotifyInfo = getSpotifyInfo(None)

    track = spotifyInfo.track(id)
    results = []

    obj = {'id': track['id'], 'name': track['name'], 'artist': ' '.join(n['name'] for n in track['artists']),
           'external_urls': track['external_urls']['spotify']}
    results.append(obj)
    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'external_urls'])
    return df


@app.route('/albumTracks', methods=['GET'])
def getAlbums():
    spotifyInfo = getSpotifyInfo(None)

    tracks = spotifyInfo.album_tracks('0HcHPBu9aaF1MxOiZmUQTl', limit=30, offset=0, market=None)['items']
    results = []

    for item in tracks:
        obj = {'id': item['id'], 'name': item['name'],
               'artist': ' '.join(n['name'] for n in item['artists']),
               'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'external_urls'])
    openWorksheet('Album Tracks').update([df.columns.values.tolist()] + df.values.tolist())
    return df


@app.route('/audioFeature', methods=['GET'])
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
    return 'OK.'


@app.route('/user/followedArtists', methods=['GET'])
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
    return 'OK.'


@app.route('/user/Playlist', methods=['GET'])
def getUserPlaylists():
    SCOPE = 'playlist-read-private playlist-read-collaborative'
    spotifyInfo = getSpotifyInfo(SCOPE)

    playlists = spotifyInfo.user_playlists('nonolala99', limit=5, offset=0)['items']
    results = []

    for item in playlists:
        obj = {'id': item['id'], 'name': item['name'], 'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'external_urls'])
    openWorksheet('User Playlist').update([df.columns.values.tolist()] + df.values.tolist())
    return df


@app.route('/user/playlistItems', methods=['GET'])
def getPlaylistItems():
    SCOPE = 'playlist-read-private'
    spotifyInfo = getSpotifyInfo(SCOPE)

    playlistItems = spotifyInfo.playlist_items('1bWn2njrDAK1q8hrk48Jaf', limit=15, offset=0)['items']
    results = []

    for item in playlistItems:
        obj = {'id': item['track']['id'], 'name': item['track']['name'],
               'external_urls': item['track']['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'external_urls'])
    openWorksheet('Playlist Items').update([df.columns.values.tolist()] + df.values.tolist())
    return df


@app.route('/user/playlistForUser', methods=['POST'])
def createPlaylistForUser():
    SCOPE = 'playlist-modify-public playlist-modify-private'
    spotifyInfo = getSpotifyInfo(SCOPE)

    tracks = ['6mPJvjjx7pcfZuI57Dh95o', '2takcwOaAZWiXQijPHIx7B', '6lCvK2AR2uOKkVFCVlAzzm', '0y6kdSRCVQhSsHSpWvTUm7',
              '2NmsngXHeC1GQ9wWrzhOMf']
    response = spotifyInfo.user_playlist_create('nonolala99', 'just for you... from ASCLEPIUS')
    spotifyInfo.playlist_add_items(response['id'], tracks)
    return response['external_urls']['spotify']


@app.route('/categoryPlaylists', methods=['GET'])
def getCategoryPlaylists():
    spotifyInfo = getSpotifyInfo()

    playlists = spotifyInfo.category_playlists('punk', 'US', limit=10, offset=5)['playlists']
    results = []
    for item in playlists['items']:
        obj = {'id': item['id'], 'name': item['name'], 'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'external_urls'])
    openWorksheet('Category Playlists').update([df.columns.values.tolist()] + df.values.tolist())
    return 'OK.'


@app.route('/user/genreSeeds', methods=['GET'])
def getAvailableGenreSeeds():
    spotifyInfo = getSpotifyInfo()

    genres = spotifyInfo.recommendation_genre_seeds()['genres']
    df = pandas.DataFrame(genres, columns=['genres'])
    openWorksheet('Available Genres').update([df.columns.values.tolist()] + df.values.tolist())
    return 'OK.'


@app.route('/user/recommendations', methods=['GET'])
def getRecommendationsForUser():
    spotifyInfo = getSpotifyInfo(None)

    artists = ['01crEa9G3pNpXZ5m7wuHOk']
    genres = ['pop', 'rock', 'punk']
    tracks = ['4RVwu0g32PAqgUiJoXsdF8']

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


@app.route('/user/savedEpisodes', methods=['GET'])
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
    return 'OK.'


@app.route('/user/savedEpisodes', methods=['GET'])
def getEpisodes(id):
    SCOPE = 'user-read-playback-position'
    spotifyInfo = getSpotifyInfo(SCOPE)

    episodes = spotifyInfo.show_episodes(id, limit=5, offset=0)['items']
    results = []

    for item in episodes:
        obj = {'id': item['id'], 'name': item['name'],
               'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'external_urls'])
    openWorksheet('Show Episodes').update([df.columns.values.tolist()] + df.values.tolist())
    return df


@app.route('/user/saveEpisode', methods=['POST'])
def saveEpisodesForUser():
    SCOPE = 'user-library-modify'
    spotifyInfo = getSpotifyInfo(SCOPE)

    episodeList = ['77o6BIVlYM3msb4MMIL1jH', '0Q86acNRm6V9GYx55SXKwf']
    spotifyInfo.current_user_saved_episodes_add(episodeList)
    return getEpisode(episodeList[0])


@app.route('/user/savedShows', methods=['GET'])
def getUserSavedShows():
    SCOPE = 'user-library-read'
    spotifyInfo = getSpotifyInfo(SCOPE)

    shows = spotifyInfo.current_user_saved_shows(limit=5, offset=0, market='US')['items']
    results = []

    for item in shows:
        obj = {'id': item['show']['id'], 'name': item['show']['name'],
               'external_urls': item['show']['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'external_urls'])
    openWorksheet('User Saved Shows').update([df.columns.values.tolist()] + df.values.tolist())
    return 'OK.'


@app.route('/user/saveShows', methods=['POST'])
def saveShowsForUser():
    SCOPE = 'user-library-modify'
    spotifyInfo = getSpotifyInfo(SCOPE)

    showList = ['5CfCWKI5pZ28U0uOzXkDHe', '5as3aKmN2k11yfDDDSrvaZ']
    spotifyInfo.current_user_saved_shows_add(showList)
    return getEpisodes('5CfCWKI5pZ28U0uOzXkDHe')


@app.route('/user/savedEpisodes', methods=['GET'])
def getEpisode(id):
    SCOPE = 'user-read-playback-position'
    spotifyInfo = getSpotifyInfo(SCOPE)

    episode = spotifyInfo.episode(id)
    results = []

    obj = {'id': episode['id'], 'name': episode['name'],
           'external_urls': episode['external_urls']['spotify']}
    results.append(obj)
    df = pandas.DataFrame(results, columns=['id', 'name', 'external_urls'])
    return df


@app.route('/audioAnalysis', methods=['GET'])
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


def openWorksheet(sheetName):
    sheets = gc.open('Asclepius')
    return sheets.worksheet(title=sheetName)


def getSpotifyInfo(SCOPE):
    if SCOPE is None:
        return spotipy.Spotify(
            auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI))

    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI,
                                  scope=SCOPE))
