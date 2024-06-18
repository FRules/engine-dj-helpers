export class Track {
    constructor(
        public artist: string,
        public title: string,
        public spotifyId: string
    ) {}
}

export class Playlist {
    constructor(
        public name: string,
        public tracks: Track[]
    ) {}
}