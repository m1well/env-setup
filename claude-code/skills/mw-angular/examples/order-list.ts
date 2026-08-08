import { Component, ElementRef, inject, signal, viewChild } from '@angular/core';
import { UiListLayout } from '@ui/templates/ui-list-layout/ui-list-layout';
import { OrderStatus } from '../../model/order';
import { OrderCard } from '../../organisms/order-card/order-card';
import { OrdersState } from '../../state/orders-state';

/** Page: the only layer that injects. It wires the template and organisms to the state. */
@Component({
  selector: 'app-order-list',
  imports: [UiListLayout, OrderCard],
  templateUrl: './order-list.html',
  styleUrl: './order-list.css',
})
export class OrderList {
  protected readonly state = inject(OrdersState);
  protected readonly statuses: readonly OrderStatus[] = ['OPEN', 'SHIPPED', 'CANCELLED'];

  /** Pure view state: dies with the view, so it never reaches the state service. */
  private readonly expandedId = signal<string | null>(null);

  private readonly detailDialog = viewChild.required<ElementRef<HTMLDialogElement>>('detailDialog');

  protected isExpanded(orderId: string): boolean {
    return this.expandedId() === orderId;
  }

  protected setExpanded(orderId: string, expanded: boolean): void {
    this.expandedId.set(expanded ? orderId : null);
  }

  protected showDetail(orderId: string): void {
    this.state.selectOrder(orderId);
    this.detailDialog().nativeElement.showModal();
  }

  protected closeDetail(): void {
    this.detailDialog().nativeElement.close();
  }
}
