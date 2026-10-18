import { inject, Injectable, signal } from '@angular/core';
import { ItemsApi } from '../data/items.api';

@Injectable({ providedIn: 'root' })
export class ItemsState {
  private readonly api = inject(ItemsApi);
  readonly items = signal<string[]>([]);

  remove(id: string): void {
    this.api.delete(id).subscribe(() => this.items.update(list => list.filter(i => i !== id)));
  }

  hide(id: string): void {
    this.items.update(list => list.filter(i => i !== id));
  }
}
