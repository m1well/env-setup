import { Component, inject } from '@angular/core';
import { ItemsApi } from '../../data/items.api';
import { ConfirmRow } from '../../organisms/confirm-row/confirm-row';
import { ItemRow } from '../../organisms/item-row/item-row';
import { OrderLines } from '../../organisms/order-lines/order-lines';
import { ItemsState } from '../../state/items.state';

@Component({
  selector: 'app-item-list',
  imports: [ItemRow, ConfirmRow, OrderLines],
  templateUrl: './item-list.html',
})
export class ItemList {
  protected readonly state = inject(ItemsState);
  protected readonly api = inject(ItemsApi);
}
