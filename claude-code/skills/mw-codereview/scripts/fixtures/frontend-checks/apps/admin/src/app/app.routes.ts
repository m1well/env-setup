import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: 'settings', loadComponent: () => import('./settings').then(m => m.Settings) },
  { path: 'confirm/:token', loadComponent: () => import('./settings').then(m => m.Settings) },
];
