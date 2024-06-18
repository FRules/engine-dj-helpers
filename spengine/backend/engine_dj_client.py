import sqlite3
import datetime
from typing import List
from artist_track_info import ArtistTrackInfo, EngineDJTrack

class EngineDJClient:
    def __init__(self, database_link, history_database_link = None):
        self.database_link = database_link
        self.history_database_link = history_database_link


    def find_unused_songs(self):
        if self.history_database_link is None:
            return
        
        conn1 = sqlite3.connect(self.database_link)
        cursor1 = conn1.cursor()

        conn2 = sqlite3.connect(self.history_database_link)
        cursor2 = conn2.cursor()

        used_tracks = "SELECT originTrackId FROM track"
        cursor2.execute(used_tracks)
        track_ids = cursor2.fetchall()
        track_ids = [str(track_id[0]) for track_id in track_ids]
        
        placeholders = ", ".join(['?'] * len(track_ids))
        unused_tracks_sql = f"SELECT id FROM Track WHERE id NOT IN ({placeholders})"

        cursor1.execute(unused_tracks_sql, track_ids)
        unused_tracks = cursor1.fetchall()
        unused_track_ids = [str(track_id[0]) for track_id in unused_tracks]

        new_playlist_name_unused_songs = datetime.datetime.today().strftime('%Y-%m-%d') + '-unused'

        self.create_crate(new_playlist_name_unused_songs, unused_track_ids)
        #print(new_playlist_name_unused_songs)


    def find_songs(self, artist_track_array: List[ArtistTrackInfo], verbose: bool = False):
        with sqlite3.connect(self.database_link) as connection:
            cursor = connection.cursor()
            
            found_ids = []
            
            found_songs = []
            missing_songs = []

            for spotify_song in artist_track_array:
                name = "%" + spotify_song.track + "%"
                artist = "%" + spotify_song.artist + "%"

                sql = "SELECT id, artist, title FROM track "
                sql += "WHERE title like ? "
                sql += "AND artist like ?"

                found = False
                for row in cursor.execute(sql, (name, artist)):
                    found = True
                    found_ids.append(row[0])
                    spotify_song['engine_dj_tracks'].append(
                        EngineDJTrack(row[0], row[1], row[2]).serialize()
                    )

                if found is False:
                    missing_songs.append(spotify_song)
                else:
                    found_songs.append(spotify_song)
                    
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

    def create_crate(self, crate_name, engine_track_ids):
        with sqlite3.connect(self.database_link) as connection:
            next_playlist_id = self.__get_next_playlist_id(connection)
            next_playlist_entity_id = self.__get_next_playlist_entity_id(connection)
            db_uuid = self.__get_db_uuid(connection)
            
            self.__create_playlist(connection, next_playlist_id, crate_name)
            self.__add_songs_to_playlist(connection, engine_track_ids, next_playlist_id, next_playlist_entity_id, db_uuid)

    def __get_next_playlist_id(self, connection):
        cursor = connection.cursor()
        
        x = cursor.execute("SELECT id FROM playlist ORDER BY id DESC")
        result = x.fetchone()
        return result[0] + 1

    def __get_next_playlist_entity_id(self, connection):
        cursor = connection.cursor()
        
        x = cursor.execute("SELECT id FROM PlaylistEntity ORDER BY id DESC")
        result = x.fetchone()
        return result[0] + 1

    def __create_playlist(self, connection, playlist_id: str, playlist_name: str):
        current_date_time = datetime.datetime.now()
        
        cursor = connection.cursor()
        
        insert_sql = "INSERT INTO playlist "
        insert_sql += "(id, title, parentListId, isPersisted, nextListId, lastEditTime, isExplicitlyExported) "
        insert_sql += "VALUES (?, ?, 0, ?, 0, ?, ?)"
        cursor.execute(insert_sql, (playlist_id, playlist_name, True, current_date_time, True))
        connection.commit()

    def __get_db_uuid(self, connection):
        cursor = connection.cursor()
        
        sql = "SELECT uuid FROM information;"
        x = cursor.execute(sql)
        result = x.fetchone()
        return result[0]

    def __add_songs_to_playlist(self, connection, engine_dj_song_ids, playlist_id, next_playlist_entity_id, db_uuid):
        sql = "INSERT INTO PlaylistEntity (id, listId, trackId, databaseUuid, nextEntityId, membershipReference) "
        sql += "values(?, ?, ?, ?, ?, 0)"
        
        current_id = next_playlist_entity_id
        
        cursor = connection.cursor()
        
        for song_id in engine_dj_song_ids:
            try:
                print(current_id, playlist_id, song_id, db_uuid, current_id + 1)
                cursor.execute(sql, (current_id, playlist_id, song_id, db_uuid, current_id + 1))
                current_id += 1
            except sqlite3.IntegrityError:
                continue

        connection.commit()
        
        sql = "UPDATE PlaylistEntity SET nextEntityId = 0 WHERE id = ?"
        cursor.execute(sql, (current_id - 1,))
        connection.commit()