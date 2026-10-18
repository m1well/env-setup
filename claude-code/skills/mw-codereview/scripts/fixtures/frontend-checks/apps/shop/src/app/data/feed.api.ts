import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class FeedApi {
  private readonly http = inject(HttpClient);

  page(pageToken: string) {
    return this.http.get(`${environment.apiUrl}/feed?pageToken=${pageToken}`);
  }
}
