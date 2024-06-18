import { TestBed } from '@angular/core/testing';

import { TrackInfoService } from './track-info.service';

describe('TrackInfoService', () => {
  let service: TrackInfoService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(TrackInfoService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
