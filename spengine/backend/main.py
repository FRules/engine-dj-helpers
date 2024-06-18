import requests
import urllib.parse
import re
import json
from typing import List
import os
import boto3


from datetime import datetime
from flask import Flask, redirect, request, jsonify, session, make_response, send_from_directory

from artist_track_info import ArtistTrackInfo
from spotify_client import SpotifyClient
from engine_dj_client import EngineDJClient


app = Flask(__name__, static_folder='static')


engine_dj_client = EngineDJClient(
    "/var/www/spengine/m.db",
    "/var/www/spengine/hm.db"
)

app.secret_key = '0D1EC4B0-18E9-49CA-999B-4745F921C370'

CLIENT_ID = None
CLIENT_SECRET = None
REDIRECT_URI = 'https://domi-n.dev/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

CREATE_PLAYLIST_URL = 'users/{user_id}/playlists'

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/xxx')
def xxx():
    engine_dj_client.find_unused_songs()

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email playlist-modify-private playlist-modify-public'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})

    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()
        
        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        r = make_response(redirect('https://domi-n.dev'))
        r.set_cookie('access_token', token_info['access_token'])
        return r

@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': session['refresh_token']
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()
        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/playlists')

def is_valid_session():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')

    return True

def get_spotify_headers():
    return {
        'Authorization': f"Bearer {session['access_token']}"
    }

def fetch_user_details():
    headers = get_spotify_headers()

    response = requests.get(API_BASE_URL + 'me', headers=headers)
    user_info = response.json()

    return user_info

@app.route('/crate', methods = ['POST'])
def create_crate():
    crate_name = request.json['crate_name']
    engine_dj_track_ids = request.json['engine_dj_track_ids']

    engine_dj_client.create_crate(crate_name, engine_dj_track_ids)
    return jsonify(success=True)

@app.route('/user')
def get_user_details():
    # is_valid_or_redirect = is_valid_session()
    # if is_valid_or_redirect is not True:
    #     return is_valid_or_redirect

    response = jsonify(fetch_user_details())
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response;

def chunk_array(array, chunk_size):
    return [array[i:i + chunk_size] for i in range(0, len(array), chunk_size)]

def add_songs_to_playlist(playlist_id: str, tracks: List[ArtistTrackInfo]):
    track_chunks = chunk_array(tracks, 100)
    for chunk in track_chunks:
        add_chunk_to_playlist(playlist_id, chunk)    

def add_chunk_to_playlist(playlist_id: str, tracks: List[ArtistTrackInfo]):
    headers = get_spotify_headers()
    spotify_track_uris = [track.spotify_id for track in tracks]
    req_body = {
        "uris": spotify_track_uris,
    }

    requests.post(
        f"{API_BASE_URL}playlists/{playlist_id}/tracks",
        headers=headers, json=req_body
    )

def create_playlist(name: str):
    user_details = fetch_user_details()
    user_id = user_details['id']

    headers = get_spotify_headers()
    req_body = {
        "name": name,
        "public": "false"
    }

    response = requests.post(
        API_BASE_URL + f'users/{user_id}/playlists',
        headers=headers, json=req_body
    )

    created_playlist = response.json()
    return created_playlist

@app.route('/playlist', methods=['POST'])
def create_playlist_api():
    is_valid_or_redirect = is_valid_session()
    if is_valid_or_redirect is not True:
        return is_valid_or_redirect

    playlist_name = request.json['playlist_name']
    artist_track_info = request.json['artist_track_info']

    playlist_details = spotify_client.create_playlist(playlist_name)
    spotify_client.add_songs_to_playlist(playlist_details['id'], artist_track_info)

    return jsonify(success=True)

def playlist_response_to_artist_track_info_array(playlist_response_json):    
    result = []
    separator = '-'
    
    for track in playlist_response_json['items']:
        track_name = track['track']['name']
        artist = track['track']['artists'][0]['name']
        spotify_id = f"spotify:track:{track['track']['id']}"
        
        new_name = re.sub(r"[\(\[].*?[\)\]]", "", track_name)
        new_name = new_name.split(separator, 1)[0]
        new_name = new_name.strip()
        
        
        new_artist = re.sub(r"[\(\[].*?[\)\]]", "", artist)
        new_artist = new_artist.strip()
    
        result.append(ArtistTrackInfo(new_artist, new_name, spotify_id))
    
    return result


def get_secret():
    secret_name = "prod/spotify-api-credentials"
    region_name = "eu-west-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )

    secret = json.loads(get_secret_value_response['SecretString'])
    return secret["SPOTIFY_CLIENT_ID"], secret["SPOTIFY_CLIENT_SECRET"]

if __name__ == '__main__':
    CLIENT_ID, CLIENT_SECRET = get_secret()
    spotify_client = SpotifyClient(session, CLIENT_ID, CLIENT_SECRET)
    app.run(host='0.0.0.0', port=5555, debug=True)
