import { Routes } from '@angular/router';
import { authGuard } from './auth.guard';

export const routes: Routes = [
  { path: 'orders', canActivate: [authGuard], loadComponent: () => import('./pages/item-list/item-list').then(m => m.ItemList) },
  { path: 'account', loadComponent: () => import('./pages/item-board/item-board').then(m => m.ItemBoard) },
];
