import { CurrencyPipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { UiBadge } from '@ui/atoms/ui-badge/ui-badge';
import { Order } from '../../model/order';

/**
 * Molecule: atoms composed into one unit, UI logic only.
 * It knows the Order type, so it lives inside the feature - not in ui/.
 */
@Component({
  selector: 'app-order-summary',
  imports: [CurrencyPipe, UiBadge],
  templateUrl: './order-summary.html',
  styleUrl: './order-summary.css',
})
export class OrderSummary {
  readonly order = input.required<Order>();
  readonly currency = input('EUR');

  protected readonly total = computed(() =>
    this.order().items.reduce((sum, item) => sum + item.unitPrice * item.quantity, 0),
  );

  protected readonly isUrgent = computed(
    () => this.order().status === 'OPEN' && this.order().dueInDays <= 2,
  );

  protected readonly dueLabel = computed(() => `Due in ${this.order().dueInDays} d`);
}
