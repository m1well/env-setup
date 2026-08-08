import { CurrencyPipe } from '@angular/common';
import { Component, computed, input, model, output } from '@angular/core';
import { Order } from '../../model/order';
import { OrderSummary } from '../../molecules/order-summary/order-summary';

/**
 * Organism: a section of the interface built from molecules and atoms.
 * Domain-aware and it owns UI-level business context - but it still injects nothing.
 */
@Component({
  selector: 'app-order-card',
  imports: [CurrencyPipe, OrderSummary],
  templateUrl: './order-card.html',
  styleUrl: './order-card.css',
  host: {
    class: 'order-card',
    '[class.order-card--expanded]': 'expanded()',
    '[attr.data-status]': 'order().status',
  },
})
export class OrderCard {
  readonly order = input.required<Order>();
  readonly currency = input('EUR');
  readonly expanded = model(false);

  readonly selected = output<string>();
  readonly shipped = output<string>();

  protected readonly canShip = computed(() => this.order().status === 'OPEN');
  protected readonly itemsId = computed(() => `items-${this.order().id}`);

  protected toggle(): void {
    this.expanded.update(expanded => !expanded);
  }
}
