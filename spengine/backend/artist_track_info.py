class EngineDJTrack:
    def __init__(self, track_id, artist, name):
        self.track_id = track_id
        self.artist = artist
        self.name = name

    def __str__(self):
        return "Artist: " + self.artist + "; Track: " + self.name + "; EngineDJId: " + self.track_id
    
    def __repr__(self):
        return str({"Artist": self.artist, "Track": self.name  + "; EngineDJId: " + self.track_id})

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def serialize(self):
        return {
            "artist": self.artist,
            "track": self.name,
            "engine_dj_track_id": self.track_id
        }

class ArtistTrackInfo:
    def __init__(self, artist, track, spotify_id):
        self.artist = artist
        self.track = track
        self.spotify_id = spotify_id
        self.engine_dj_tracks = []
        
    def __str__(self):
        return "Artist: " + self.artist + "; Track: " + self.track + "; SpotfyId: " + self.spotify_id
    
    def __repr__(self):
        return str({"Artist": self.artist, "Track": self.track  + "; SpotfyId: " + self.spotify_id})

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def serialize(self):
        return {
            "artist": self.artist,
            "track": self.track,
            "spotify_id": self.spotify_id,
            "engine_dj_tracks": self.engine_dj_tracks
        }