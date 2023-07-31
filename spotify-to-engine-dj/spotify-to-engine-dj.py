import requests
import os
import sqlite3
import re
import datetime
import argparse

class ArtistTrackInfo:
    def __init__(self, artist, track):
        self.artist = artist
        self.track = track
        
    def __str__(self):
        print("Artist: " + self.artist + "; Track: " + self.track)
    
    def __repr__(self):
        return str({"Artist": self.artist, "Track": self.track})

def get_oauth_token():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if client_id is None or client_secret is None:
        print("Please provide SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")
        return None
    
    url = "https://accounts.spotify.com/api/token"
    
    data = {'grant_type': 'client_credentials', 'client_id': client_id, 'client_secret': client_secret}
    
    response = requests.post(url, data=data)
    
    return response.json()['access_token']
    
    
def get_playlist_id_by_link(playlist_link: str):
    return playlist_link.rsplit('/', 1)[-1]
    
def query_playlist(playlist_id, offset, token):
    limit = 100
    url = 'https://api.spotify.com/v1/playlists/' + playlist_id + "/tracks?" 
    url += "fields=items(track(name,artists))&limit=" + str(limit) + "&offset=" + str(offset * limit)
    headers = {'Authorization': 'Bearer ' + token}
    
    x = requests.get(url, headers = headers)
    return x.json()

def playlist_response_to_artist_track_info_array(playlist_response_json):    
    result = []
    separator = '-'
    
    for track in playlist_response_json['items']:
        track_name = track['track']['name']
        artist = track['track']['artists'][0]['name']
        
        new_name = re.sub("[\(\[].*?[\)\]]", "", track_name)
        new_name = new_name.split(separator, 1)[0]
        new_name = new_name.strip()
        
        
        new_artist = re.sub("[\(\[].*?[\)\]]", "", artist)
        new_artist = new_artist.strip()
    
        
        result.append(ArtistTrackInfo(new_artist, new_name))
    
    return result

def merge_artist_track_info_arrays(array):
    response = []
    for a in array:
        response += a
        
    return response

# SEARCH
def find_songs_in_engine_dj(connection, artistTrackInfoArray, verbose = False):
    cursor = connection.cursor()
    
    found_ids = []
    
    found_songs = []
    missing_songs = []

    for spotify_song in artistTrackInfoArray:
        name = "%" + spotify_song.track + "%"
        artist = "%" + spotify_song.artist + "%"

        sql = "SELECT id, artist, title FROM track "
        sql += "WHERE title like ? "
        sql += "AND artist like ?"

        found = False
        for row in cursor.execute(sql, (name, artist)):
            found = True
            found_ids.append(row[0])
            found_songs.append({'spotify_song': spotify_song, 'engine_dj_song': row[1] + ' - ' + row[2]})

        if found is False:
            missing_songs.append(spotify_song)
            
    found_ids = list(dict.fromkeys(found_ids))
    
    if verbose is True:
        print("Found songs:")
        for song in found_songs:
            print(song)
            
        print()
        print("Missing songs:")
        for song in missing_songs:
            print(song.artist + " - " + song.track)
    
    return found_ids, found_songs, missing_songs

def get_next_playlist_id(connection):
    cursor = connection.cursor()
    
    x = cursor.execute("SELECT id FROM playlist ORDER BY id DESC")
    result = x.fetchone()
    return result[0] + 1

def get_next_playlist_entity_id(connection):
    cursor = connection.cursor()
    
    x = cursor.execute("SELECT id FROM PlaylistEntity ORDER BY id DESC")
    result = x.fetchone()
    return result[0] + 1
        
    
def create_playlist(connection, playlist_id, playlist_name):
    currentDateTime = datetime.datetime.now()
    
    cursor = connection.cursor()
    
    insert_sql = "INSERT INTO playlist "
    insert_sql += "(id, title, parentListId, isPersisted, nextListId, lastEditTime, isExplicitlyExported) "
    insert_sql += "VALUES (?, ?, 0, ?, 0, ?, ?)"
    x = cursor.execute(insert_sql, (playlist_id, playlist_name, True, currentDateTime, True))
    connection.commit()
    
def get_db_uuid(connection):
    cursor = connection.cursor()
    
    sql = "SELECT uuid FROM information;"
    x = cursor.execute(sql)
    result = x.fetchone()
    return result[0]

def add_songs_to_playlist(connection, engine_dj_song_ids, playlist_id, next_playlist_entity_id, db_uuid):
    sql = "INSERT INTO PlaylistEntity (id, listId, trackId, databaseUuid, nextEntityId, membershipReference) "
    sql += "values(?, ?, ?, ?, ?, 0)"
    
    current_id = next_playlist_entity_id
    
    cursor = connection.cursor()
    
    for song_id in engine_dj_song_ids:
        cursor.execute(sql, (current_id, playlist_id, song_id, db_uuid, current_id + 1))
        current_id += 1
        
    connection.commit()
    
    sql = "UPDATE PlaylistEntity SET nextEntityId = 0 WHERE id = ?"
    cursor.execute(sql, (current_id - 1,))
    connection.commit()


def main(playlist_link, engine_db_path, name_of_new_playlist, verbose=False):
    playlist_id = get_playlist_id_by_link(playlist_link)
    token = get_oauth_token()
    
    offset = 0
    artistTrackInfo = []
    playlist_response = query_playlist(playlist_id, offset, token)
    while (len(playlist_response['items']) > 0):
        playlist_response = query_playlist(playlist_id, offset, token)
        parsed = playlist_response_to_artist_track_info_array(playlist_response)
        artistTrackInfo += parsed
        offset += 1
    
    connection = sqlite3.connect(engine_db_path)
    
    found_song_ids, found_songs, missing_songs = find_songs_in_engine_dj(connection, artistTrackInfo, verbose=verbose)
    
    next_playlist_id = get_next_playlist_id(connection)
    next_playlist_entity_id = get_next_playlist_entity_id(connection)
    db_uuid = get_db_uuid(connection)
    
    create_playlist(connection, next_playlist_id, name_of_new_playlist)
    add_songs_to_playlist(connection, found_song_ids, next_playlist_id, next_playlist_entity_id, db_uuid)
    
    connection.close()


if __name__ == '__main__':
    description = 'This application takes a spotify playlist, parses it and searches for the corresponding songs in your EngineDJ Library. '
    description += 'The found songs are added to a new playlist.'
    parser = argparse.ArgumentParser(
                    prog='Spotify Playlist to Engine DJ Playlist',
                    description=description,
                    epilog='Text at the bottom of help')

    parser.add_argument('name')
    parser.add_argument('playlist')
    parser.add_argument('db')
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()
    main(args.playlist, args.db, args.name, args.verbose)