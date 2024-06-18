import { Injectable } from '@angular/core';
import {HttpClient, HttpErrorResponse, HttpResponse} from '@angular/common/http';
import { Track, Playlist } from './track-info.model';
import {Observable, catchError, tap, throwError} from 'rxjs';
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

    //return this.http.post(`${API_URL}/crate`, data, { observe: 'response'});

    return this.http.post(`${API_URL}/crate`, data, { responseType: 'blob', observe: 'response' }).pipe(
      tap((response: HttpResponse<Blob>) => {
        if (response.body) {
          const blob = new Blob([response.body], { type: 'application/octet-stream' });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'm.db';  // Ersetze 'filename.ext' durch den gewünschten Dateinamen und die entsprechende Erweiterung
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        } else {
          console.error('Response body is null');
        }
      })
    );
  }
}
