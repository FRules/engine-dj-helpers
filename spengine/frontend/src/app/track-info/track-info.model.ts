export class EngineDJTrackDetails {
    constructor(
        public artist: string,
        public track: string,
        public engine_dj_track_id: number
    ) {}
}

export class ArtistTrackInfo {
    constructor(
        public artist: string,
        public track: string,
        public spotify_id: string,
        public engine_dj_tracks: EngineDJTrackDetails[]
    ) {}
}