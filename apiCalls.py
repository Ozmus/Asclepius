import json
import os

import gspread
import pandas

CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')


def getUserTopArtist():
    with open('a.txt', 'r') as file:
        data = json.load(file)

    results = []

    for item in data['items']:
        obj = {'id': item['album']['id'], 'name': item['album']['name'], 'artist': ' '.join(n['name']for n in item['album']['artists']),
               'href': item['album']['href'], 'external_urls': item['album']['external_urls']['spotify']}
        results.append(obj)

    df = pandas.DataFrame(results, columns=['id', 'name', 'artist', 'href', 'external_urls'])

    print(df)
        gc = gspread.service_account(filename='asclepius-spotify-data.json')
        sheets = gc.open('Asclepius')
        worksheet = sheets.add_worksheet(title='User Top Tracks', rows='5', cols='5')
        print([df.columns.values.tolist()] + df.values.tolist())
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())

    print("--------------------------")
    return ("Done. Go to api/products")


getUserTopArtist()
