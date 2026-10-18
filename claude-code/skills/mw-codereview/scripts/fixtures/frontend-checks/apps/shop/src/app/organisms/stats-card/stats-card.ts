import { Component, inject } from '@angular/core';
import { ItemsApi } from '../../data/items.api';

@Component({
  selector: 'app-stats-card',
  template: '<p>stats</p>',
})
export class StatsCard {
  private readonly api = inject(ItemsApi);
}
