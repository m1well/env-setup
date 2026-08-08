import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Order, OrderDraft, OrderStatus } from '../model/order';

/** HttpClient only - no state, no caching, no subscriptions. */
@Injectable({ providedIn: 'root' })
export class OrdersApi {
  private readonly http = inject(HttpClient);

  findByStatus(status: OrderStatus): Observable<Order[]> {
    return this.http.get<Order[]>('/api/orders', { params: { status } });
  }

  create(draft: OrderDraft): Observable<Order> {
    return this.http.post<Order>('/api/orders', draft);
  }

  markAsShipped(orderId: string): Observable<Order> {
    return this.http.post<Order>(`/api/orders/${orderId}/shipment`, {});
  }
}
