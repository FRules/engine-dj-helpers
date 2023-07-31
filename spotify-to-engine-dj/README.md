# spotify-to-engine-dj

This script parses a given spotify playlist and fetches the relevant artist and track information.
Based on these two fields, the application tries to find the corresponding songs in the EngineDJ database.
A new playlist is created with the found songs.

## Usage

```python 
python spotify-to-engine-dj.py NEW_PLAYLIST_NAME LINK_TO_SPOTIFY_PLAYLIST LINK_TO_ENGINE_DJ_DB
```

for example

```python
python spotify-to-engine-dj.py "Test" "https://open.spotify.com/playlist/31uSi3T52m00gqt4MwuZNM" "~/Music/Engine Library/Database2/m.db"
```

