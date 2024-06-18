import { Component } from '@angular/core';
import { TrackInfoService } from '../track-info.service';
import { HTTP_INTERCEPTORS, HttpClient, HttpClientModule } from '@angular/common/http';
import { BrowserModule } from '@angular/platform-browser';
import { firstValueFrom, lastValueFrom } from 'rxjs';
import { ReactiveFormsModule } from '@angular/forms';
import { FormControl } from "@angular/forms";
import { ArtistTrackInfo, EngineDJTrackDetails } from './track-info.model';
import { CommonModule, NgFor } from '@angular/common';
import { API_URL } from '../../env';

@Component({
  selector: 'app-track-info',
  standalone: true,
  imports: [HttpClientModule, ReactiveFormsModule, CommonModule, NgFor],
  providers: [TrackInfoService],
  templateUrl: './track-info.component.html',
  styleUrl: './track-info.component.css'
})
export class TrackInfoComponent {

  constructor(private trackInfoService: TrackInfoService
  ){ }

  foundSongs: ArtistTrackInfo[] = [];
  missingSongs: ArtistTrackInfo[] = [];

  API_URL = API_URL;

  crateCreatedSuccessfully: any = null;
  createPlaylistSuccessfully: any = null;

  playlistLink = new FormControl();
  newPlaylistName = new FormControl();
  newCrateName = new FormControl();

  async ngOnInit() {
    

  }

  comparePlaylistWithLibrary(): void {
    const playlistLink = this.playlistLink.getRawValue() as string;

    const x = lastValueFrom(this.trackInfoService.compareSpotifyPlaylistWithLibrary(playlistLink));

    x.then((response) => {
      this.missingSongs = response["body"]["missing_songs"]
      this.foundSongs = response["body"]["found_songs"]
    }).catch((error) => {
      
    })
  }

  createFoundSongsCrateInEngineDJ(): void {
    const crateName = this.newCrateName.getRawValue() as string;

    const engine_dj_track_ids = this.foundSongs.map((x: ArtistTrackInfo) => 
      x.engine_dj_tracks.map((y: EngineDJTrackDetails) => 
        y.engine_dj_track_id)).flatMap((x) => x);

    const obs = lastValueFrom(this.trackInfoService.createCrateInEngineDJ(crateName, engine_dj_track_ids));
    obs.then((response) => {
      this.crateCreatedSuccessfully = true;
    })
  }

  createPlaylistInSpotify(tracks: ArtistTrackInfo[]): void {
    const newPlaylistName = this.newPlaylistName.getRawValue() as string;

    const obs = lastValueFrom(this.trackInfoService.createSpotifyPlaylist(newPlaylistName, tracks));

    obs.then((response) => {
      this.createPlaylistSuccessfully = true;
    })
  }



  test() {

  }
}
