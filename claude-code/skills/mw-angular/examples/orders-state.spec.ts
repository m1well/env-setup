import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ApplicationRef } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest';
import { OrdersApi } from '../data/orders-api';
import { Order, OrderDetail } from '../model/order';
import { OrdersState } from './orders-state';

const openOrder: Order = {
  id: '1',
  reference: 'ORD-1',
  status: 'OPEN',
  dueInDays: 1,
  items: [{ sku: 'SKU-1', quantity: 2, unitPrice: 10 }],
};

const shippedOrder: Order = {
  id: '2',
  reference: 'ORD-2',
  status: 'SHIPPED',
  dueInDays: 9,
  items: [],
};

const openOrderDetail: OrderDetail = {
  ...openOrder,
  customerName: 'Ada Lovelace',
  shippingAddress: 'Analytical Engine Lane 1',
  notes: '',
};

describe('OrdersState', () => {
  let findByStatus: Mock;
  let markAsShipped: Mock;
  let state: OrdersState;
  let http: HttpTestingController;

  const settle = () => TestBed.inject(ApplicationRef).whenStable();

  beforeEach(() => {
    findByStatus = vi.fn().mockReturnValue(of([openOrder, shippedOrder]));
    markAsShipped = vi.fn().mockReturnValue(of(shippedOrder));

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: OrdersApi, useValue: { findByStatus, markAsShipped } },
      ],
    });

    state = TestBed.inject(OrdersState);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('loads orders for the default filter', async () => {
    await settle();

    expect(findByStatus).toHaveBeenCalledWith('OPEN');
    expect(state.orders()).toEqual([openOrder, shippedOrder]);
  });

  it('counts only open orders', async () => {
    await settle();

    expect(state.openCount()).toBe(1);
  });

  it('reloads with the new status when the filter changes', async () => {
    await settle();

    state.applyFilter('SHIPPED');
    await settle();

    expect(findByStatus).toHaveBeenLastCalledWith('SHIPPED');
  });

  it('requests no detail while nothing is selected', async () => {
    await settle();

    expect(http.match(() => true)).toEqual([]);
  });

  it('loads the detail once an order is selected', async () => {
    await settle();

    state.selectOrder('1');
    TestBed.tick();
    http.expectOne('/api/orders/1').flush(openOrderDetail);
    await settle();

    expect(state.selectedOrder()).toEqual(openOrderDetail);
  });

  it('clears the selection when the filter changes', async () => {
    await settle();
    state.selectOrder('1');
    TestBed.tick();
    http.expectOne('/api/orders/1').flush(openOrderDetail);
    await settle();

    state.applyFilter('SHIPPED');
    await settle();

    expect(state.hasSelection()).toBe(false);
  });

  it('reloads the list after an order was shipped', async () => {
    await settle();

    state.markAsShipped('1');
    await settle();

    expect(markAsShipped).toHaveBeenCalledWith('1');
    expect(findByStatus).toHaveBeenCalledTimes(2);
  });
});
