import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class SessionService {
  remember(user: { email: string }) {
    localStorage.setItem('user', JSON.stringify(user));
  }
}
