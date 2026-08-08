import { ComponentFixture, TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Order } from '../../model/order';
import { OrderCard } from './order-card';

const order: Order = {
  id: '1',
  reference: 'ORD-1',
  status: 'OPEN',
  dueInDays: 5,
  items: [
    { sku: 'SKU-1', quantity: 2, unitPrice: 10 },
    { sku: 'SKU-2', quantity: 1, unitPrice: 23.5 },
  ],
};

/**
 * No shallow rendering: the molecule and its atom render for real,
 * so composition across the layers is covered by the organism's own spec.
 */
describe('OrderCard', () => {
  let fixture: ComponentFixture<OrderCard>;
  let component: OrderCard;

  const query = <T extends HTMLElement>(selector: string): T | null =>
    fixture.nativeElement.querySelector(selector);

  const queryAll = (selector: string): NodeListOf<HTMLElement> =>
    fixture.nativeElement.querySelectorAll(selector);

  const setOrder = async (patch: Partial<Order> = {}): Promise<void> => {
    fixture.componentRef.setInput('order', { ...order, ...patch });
    await fixture.whenStable();
  };

  beforeEach(async () => {
    TestBed.configureTestingModule({ imports: [OrderCard] });
    fixture = TestBed.createComponent(OrderCard);
    component = fixture.componentInstance;
    await setOrder();
  });

  it('renders the summed item total', () => {
    expect(query('.order-summary__total')?.textContent).toContain('43.50');
  });

  it('exposes the status on the host element', () => {
    expect(fixture.nativeElement.dataset.status).toBe('OPEN');
  });

  it('shows an urgency badge for open orders due within two days', async () => {
    expect(query('.ui-badge')).toBeNull();

    await setOrder({ dueInDays: 2 });

    expect(query('.ui-badge')?.textContent).toContain('Due in 2 d');
  });

  it('shows no urgency badge for a shipped order', async () => {
    await setOrder({ status: 'SHIPPED', dueInDays: 0 });

    expect(query('.ui-badge')).toBeNull();
  });

  it('hides the items until expanded', async () => {
    expect(query('.order-card__items')).toBeNull();

    fixture.componentRef.setInput('expanded', true);
    await fixture.whenStable();

    expect(queryAll('.order-card__items li')).toHaveLength(2);
  });

  it('emits expandedChange when the header is toggled', async () => {
    const expandedChange = vi.fn();
    component.expanded.subscribe(expandedChange);

    query<HTMLButtonElement>('.order-card__toggle')?.click();
    await fixture.whenStable();

    expect(expandedChange).toHaveBeenCalledWith(true);
  });

  it('emits the order id when details are requested', async () => {
    const selected = vi.fn();
    component.selected.subscribe(selected);

    query<HTMLButtonElement>('.order-card__actions button')?.click();
    await fixture.whenStable();

    expect(selected).toHaveBeenCalledWith('1');
  });

  it('offers shipping only for open orders', async () => {
    expect(queryAll('.order-card__actions button')).toHaveLength(2);

    await setOrder({ status: 'SHIPPED' });

    const actions = queryAll('.order-card__actions button');
    expect(actions).toHaveLength(1);
    expect(actions[0].textContent).toContain('Details');
  });
});
