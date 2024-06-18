import { Injectable } from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import { Track, Playlist } from './track-info.model';
import {Observable, catchError, throwError} from 'rxjs';
import {API_URL} from '../env';
import { ArtistTrackInfo } from './track-info/track-info.model';


@Injectable({
  providedIn: 'root'
})
export class TrackInfoService {

  constructor(private http: HttpClient) {
  }

  getTracks(): Observable<any> {
    return this.http
      .get(`${API_URL}`, { observe: 'response'});
      
  }

  compareSpotifyPlaylistWithLibrary(playlistLink: string):  Observable<any> {
    return this.http.get(`${API_URL}/test?playlistLink=${playlistLink}`, { observe: 'response'});
  }

  createSpotifyPlaylist(playlistName: string, tracks: ArtistTrackInfo[]): Observable<any> {
    const data = {
      'playlist_name': playlistName,
      'artist_track_info': tracks
    }

    return this.http.post(`${API_URL}/playlist`, data, { observe: 'response'});
  }

  createCrateInEngineDJ(crateName: string, engine_dj_track_ids: number[]): Observable<any> {
    const data = {
      'crate_name': crateName,
      'engine_dj_track_ids': engine_dj_track_ids
    }

    return this.http.post(`${API_URL}/crate`, data, { observe: 'response'});
  }
}
