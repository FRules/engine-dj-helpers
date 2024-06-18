import requests
import urllib.parse
import re
import json

from typing import List
from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session
from artist_track_info import ArtistTrackInfo

class SpotifyClient:
    REDIRECT_URI = 'http://localhost:5555/callback'

    AUTH_URL = 'https://accounts.spotify.com/authorize'
    TOKEN_URL = 'https://accounts.spotify.com/api/token'
    API_BASE_URL = 'https://api.spotify.com/v1/'

    def __init__(self, session, client_id, client_secret):
        self.session = session
        self.CLIENT_ID = client_id
        self.CLIENT_SECRET = client_secret
        self.scope = 'user-read-private user-read-email playlist-modify-private playlist-modify-public'

    def get_playlist_id_by_link(self, playlist_link: str):
        spotify_playlist_id = playlist_link.rsplit('/', 1)[-1]
        if "?" in playlist_link:
            spotify_playlist_id = spotify_playlist_id.split("?", 1)[0]

        return spotify_playlist_id

    def get_spotify_headers(self):
        return {
            'Authorization': f"Bearer {self.session['access_token']}"
        }

    def fetch_user_details(self):
        headers = self.get_spotify_headers()

        response = requests.get(self.API_BASE_URL + 'me', headers=headers)
        user_info = response.json()

        return user_info
    
    def chunk_array(self, array, chunk_size):
        return [array[i:i + chunk_size] for i in range(0, len(array), chunk_size)]

    def add_songs_to_playlist(self, playlist_id: str, tracks: List[ArtistTrackInfo]):
        track_chunks = self.chunk_array(tracks, 100)
        for chunk in track_chunks:
            self.add_chunk_to_playlist(playlist_id, chunk)    

    def add_chunk_to_playlist(self, playlist_id: str, tracks: List[ArtistTrackInfo]):
        headers = self.get_spotify_headers()
        spotify_track_uris = [track["spotify_id"] for track in tracks]
        req_body = {
            "uris": spotify_track_uris,
        }

        requests.post(
            f"{self.API_BASE_URL}playlists/{playlist_id}/tracks",
            headers=headers, json=req_body
        )

    def create_playlist(self, name: str):
        user_details = self.fetch_user_details()
        user_id = user_details['id']

        headers = self.get_spotify_headers()
        req_body = {
            "name": name,
            "public": "false"
        }

        response = requests.post(
            self.API_BASE_URL + f'users/{user_id}/playlists',
            headers=headers, json=req_body
        )

        created_playlist = response.json()
        return created_playlist


    def playlist_response_to_artist_track_info_array(self, playlist_response_json):    
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

    def query_reference_playlist(self, playlist_link: str):
        playlist_id = self.get_playlist_id_by_link(playlist_link)
        offset = 0
        artistTrackInfo = []
        playlist_response = self.query_reference_playlist_offset(playlist_id, offset)
        print(playlist_response)
        while (len(playlist_response['items']) > 0):
            playlist_response = self.query_reference_playlist_offset(playlist_id, offset)
            parsed = self.playlist_response_to_artist_track_info_array(playlist_response)
            artistTrackInfo += parsed
            offset += 1

        return artistTrackInfo

    def query_reference_playlist_offset(self, playlist_id, offset):
        headers = self.get_spotify_headers()
        limit = 100
        url = 'https://api.spotify.com/v1/playlists/' + playlist_id + "/tracks?" 
        url += "fields=items(track(id,name,artists))&limit=" + str(limit) + "&offset=" + str(offset * limit)
        
        tracks_response = requests.get(url, headers = headers)
        return tracks_response.json()