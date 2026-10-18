import { Component, inject } from '@angular/core';
import { FeedApi } from '../../data/feed.api';
import { ItemsApi } from '../../data/items.api';

@Component({
  selector: 'app-item-board',
  templateUrl: './item-board.html',
})
export class ItemBoard {
  private readonly items = inject(ItemsApi);
  private readonly feed = inject(FeedApi);

  protected deleteItem(id: string): void {
    this.items.delete(id).subscribe();
  }
}
