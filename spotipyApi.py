''' Example of Spotify authorization code flow (refreshable user auth).
Displays profile information of authenticated user and access token
information that can be refreshed by clicking a button.
Basic flow:
    -> '/'
    -> Spotify login page
    -> '/callback'
    -> get tokens
    -> use tokens to access API
Required environment variables:
    FLASK_APP, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SECRET_KEY
More info:
    https://developer.spotify.com/documentation/general/guides/authorization-guide/#authorization-code-flow
'''

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
    spotifyInfo = spotipy.Spotify(
        auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI,
                                  scope=SCOPE))
    artists = spotifyInfo.current_user_top_artists(limit=10, offset=0, time_range='short_term')['items']
    results = []

    for item in artists:
        obj = {'id': item['id'], 'name': item['name'], 'genres': ', '.join(str(genre) for genre in item['genres']),
               'href': item['href'],
               'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'genres', 'href', 'external_urls'])
    sheets = gc.open('Asclepius')
    worksheet = sheets.add_worksheet(title='User Top Artists', rows='10', cols='5')
    print([df.columns.values.tolist()] + df.values.tolist())
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    return 'DONE.'


@app.route('/topTracks', methods=['GET'])
def getUserTopTracks():
    SCOPE = 'user-top-read'
    spotifyInfo = spotipy.Spotify(
        auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI,
                                  scope=SCOPE))
    artists = spotifyInfo.current_user_top_tracks(limit=10, offset=0, time_range='short_term')
    results = []

    for item in artists['items']:
        obj = {'id': item['id'], 'name': item['name'],
               'artist': ' '.join(n['name'] for n in item['album']['artists']),
               'href': item['href'], 'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'href', 'external_urls'])
    sheets = gc.open('Asclepius')
    worksheet = sheets.add_worksheet(title='User Top Tracks', rows='10', cols='5')
    print([df.columns.values.tolist()] + df.values.tolist())
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    return 'OK.'


@app.route('/user/recentlyPlayedTracks', methods=['GET'])
def getRecentlyPlayedTracks():
    SCOPE = 'user-read-recently-played'
    spotifyInfo = spotipy.Spotify(
        auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI,
                                  scope=SCOPE))
    artists = spotifyInfo.current_user_recently_played(limit=10, after=None, before=None)['items']
    results = []

    for item in artists['items']:
        obj = {'id': item['id'], 'name': item['name'],
               'artist': ' '.join(n['name'] for n in item['album']['artists']),
               'href': item['href'], 'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'href', 'external_urls'])
    sheets = gc.open('Asclepius')
    worksheet = sheets.add_worksheet(title='User Recently Played Tracks', rows='10', cols='5')
    print([df.columns.values.tolist()] + df.values.tolist())
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    return 'OK.'


@app.route('/user/relatedArtists', methods=['GET'])
def getRelatedArtists():
    spotifyInfo = spotipy.Spotify(
        auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI))
    artists = spotifyInfo.artist_related_artists('2RQ8NtUmg5y6tfbvCwX8jI')['artists']
    results = []

    for item in artists:
        obj = {'id': item['id'], 'name': item['name'], 'genres': ', '.join(str(genre) for genre in item['genres'])}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'genres'])
    sheets = gc.open('Asclepius')
    worksheet = sheets.add_worksheet(title='Artist Related Artists', rows=len(artists), cols='3')
    print([df.columns.values.tolist()] + df.values.tolist())
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    return 'DONE.'


@app.route('/user/artists', methods=['GET'])
def getSeveralArtists():
    spotifyInfo = spotipy.Spotify(
        auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI))
    artists = spotifyInfo.artists('2RQ8NtUmg5y6tfbvCwX8jI,6S2OmqARrzebs0tKUEyXyp,3ABivHBm6ULD624ig1lgOg')['artists']
    results = []

    for item in artists:
        obj = {'id': item['id'], 'name': item['name'], 'genres': ', '.join(str(genre) for genre in item['genres']),
               'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'genres', 'external_urls'])
    sheets = gc.open('Asclepius')
    worksheet = sheets.add_worksheet(title='Artists', rows=3, cols='4')
    print([df.columns.values.tolist()] + df.values.tolist())
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    return 'DONE.'


@app.route('/user/newReleases', methods=['GET'])
def getNewReleases():
    spotifyInfo = spotipy.Spotify(
        auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI))

    tracks = spotifyInfo.new_releases(country='TR', limit=20, offset=0,)['albums']['items']
    results = []

    for item in tracks:
        obj = {'id': item['id'], 'name': item['name'],
               'artist': ' '.join(n['name'] for n in item['album']['artists']),
               'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'external_urls'])
    sheets = gc.open('Asclepius')
    worksheet = sheets.add_worksheet(title='New Releases', rows='10', cols='4')
    print([df.columns.values.tolist()] + df.values.tolist())
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    return 'OK.'


@app.route('/tracks', methods=['GET'])
def getTracks():
    spotifyInfo = spotipy.Spotify(
        auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI))

    tracks = spotifyInfo.tracks('7ouMYWpwJ422jRcDASZB7P,4VqPOruhp5EdPBeR92t6lQ,2takcwOaAZWiXQijPHIx7B', market=None)['tracks']
    results = []

    for item in tracks:
        obj = {'id': item['id'], 'name': item['name'],
               'artist': ' '.join(n['name'] for n in item['artists']['name']),
               'href': item['href'], 'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'external_urls'])
    sheets = gc.open('Asclepius')
    worksheet = sheets.add_worksheet(title='Tracks', rows='3', cols='4')
    print([df.columns.values.tolist()] + df.values.tolist())
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    return 'OK.'

@app.route('/albumTracks', methods=['GET'])
def getAlbums():
    spotifyInfo = spotipy.Spotify(
        auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI))

    tracks = spotifyInfo.album_tracks('',limit=30, offset=0, market=None)['items']
    results = []

    for item in tracks:
        obj = {'id': item['id'], 'name': item['name'],
               'artist': ' '.join(n['name'] for n in item['album']['artists']), 'external_urls': item['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'external_urls'])
    sheets = gc.open('Asclepius')
    worksheet = sheets.add_worksheet(title='Album Tracks', rows='10', cols='4')
    print([df.columns.values.tolist()] + df.values.tolist())
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    return 'OK.'


@app.route('/audioFeature', methods = ['GET'])
def getAudioFeature():
    spotifyInfo = spotipy.Spotify(
        auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI))


    track = spotifyInfo.audio_features('7ouMYWpwJ422jRcDASZB7P')['audio_features']
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
    sheets = gc.open('Asclepius')
    worksheet = sheets.add_worksheet(title='Tracks Audio Feature', rows='3', cols='11')
    print([df.columns.values.tolist()] + df.values.tolist())
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    return 'OK.'

@app.route('/audioAnalysis', methods = ['GET'])
def getAudioAnalysis():
    spotifyInfo = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI))

    track = spotifyInfo.audio_analysis('7ouMYWpwJ422jRcDASZB7P')

    obj = {'loudness': track['track']['loudness'], 'tempo': track['track']['tempo'] ,'tempo_confidence': track['track']['tempo_confidence'],
           'time_signature': track['track']['time_signature'], 'time_signature_confidence': track['track']['time_signature_confidence'],
           'key': track['track']['key'], 'key_confidence': track['track']['key_confidence'],'mode': track['track']['mode'],
           'mode_confidence': track['track']['mode_confidence'], 'loudness': track['track']['loudness'], 'tempo': track['sections']['tempo'],
           'tempo_confidence': track['sections']['tempo_confidence'], 'key': track['sections']['key'], 'key_confidence': track['sections']['key_confidence'],
           'mode': track['sections']['mode'], 'mode_confidence': track['sections']['mode_confidence'], 'time_signature': track['sections']['time_signature'],
           'time_signature_confidence': track['sections']['time_signature_confidence'], 'start': track['segments']['start'], 'duration': track['segments']['duration'],
           'confidence': track['segments']['confidence'], 'loudness_start': track['segments']['loudness_start'], 'loudness_max': track['segments']['loudness_max'],
           'loudness_max_time': track['segments']['loudness_max_time'], 'loudness_end': track['segments']['loudness_end']}

    df = pandas.DataFrame(track, columns=['loudness', 'tempo' ,'tempo_confidence', 'time_signature', 'time_signature_confidence','key', 'key_confidence','mode',
           'mode_confidence', 'loudness', 'tempo', 'tempo_confidence', 'key', 'key_confidence', 'mode', 'mode_confidence', 'time_signature',
           'time_signature_confidence', 'start', 'duration', 'confidence', 'loudness_start', 'loudness_max', 'loudness_max_time', 'loudness_end'])


    sheets = gc.open('Asclepius')
    worksheet = sheets.add_worksheet(title='Tracks Audio Analysis', rows='3', cols='25')
    print([df.columns.values.tolist()] + df.values.tolist())
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    return 'OK.'


