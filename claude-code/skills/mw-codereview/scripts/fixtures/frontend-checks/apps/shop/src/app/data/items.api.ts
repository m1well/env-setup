import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ItemsApi {
  private readonly http = inject(HttpClient);

  delete(id: string) {
    return this.http.delete(`${environment.apiUrl}/items/${id}`);
  }

  byLink(token: string) {
    return this.http.get(`${environment.apiUrl}/links/${token}`);
  }
}
