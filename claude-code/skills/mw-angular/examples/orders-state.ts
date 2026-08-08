import { httpResource } from '@angular/common/http';
import { computed, DestroyRef, inject, Injectable, linkedSignal, signal } from '@angular/core';
import { rxResource, takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Order, OrderDetail, OrderStatus } from '../model/order';
import { OrdersApi } from '../data/orders-api';

/**
 * Feature state. Provide it in the feature route (`providers: [OrdersState]`)
 * unless the state really is app-wide.
 */
@Injectable({ providedIn: 'root' })
export class OrdersState {
  private readonly api = inject(OrdersApi);
  private readonly destroyRef = inject(DestroyRef);

  private readonly filter = signal<OrderStatus>('OPEN');

  /** Resets itself whenever the filter changes - a computed can't, a plain signal would go stale. */
  private readonly selectedId = linkedSignal<OrderStatus, string | null>({
    source: this.filter,
    computation: () => null,
  });

  private readonly ordersResource = rxResource({
    params: () => this.filter(),
    stream: ({ params: status }) => this.api.findByStatus(status),
    defaultValue: [] as Order[],
  });

  /** Returning undefined means "no request" - the detail stays idle until something is selected. */
  private readonly detailResource = httpResource<OrderDetail>(() => {
    const orderId = this.selectedId();
    return orderId ? `/api/orders/${orderId}` : undefined;
  });

  readonly orders = this.ordersResource.value.asReadonly();
  readonly isLoading = this.ordersResource.isLoading;
  readonly error = this.ordersResource.error;

  readonly activeFilter = this.filter.asReadonly();
  readonly selectedOrder = this.detailResource.value.asReadonly();
  readonly isDetailLoading = this.detailResource.isLoading;

  readonly openCount = computed(() => this.orders().filter(order => order.status === 'OPEN').length);
  readonly hasSelection = computed(() => this.selectedId() !== null);

  applyFilter(status: OrderStatus): void {
    this.filter.set(status);
  }

  selectOrder(orderId: string): void {
    this.selectedId.set(orderId);
  }

  clearSelection(): void {
    this.selectedId.set(null);
  }

  /** Writes stay imperative - a POST is not a resource. Reload afterwards. */
  markAsShipped(orderId: string): void {
    this.api
      .markAsShipped(orderId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.ordersResource.reload());
  }

  refresh(): void {
    this.ordersResource.reload();
  }
}
