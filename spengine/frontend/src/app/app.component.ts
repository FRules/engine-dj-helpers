import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TrackInfoComponent } from './track-info/track-info.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, TrackInfoComponent],
  providers: [],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'frontend';
}
