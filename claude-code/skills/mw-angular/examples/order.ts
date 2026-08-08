export type OrderStatus = 'OPEN' | 'SHIPPED' | 'CANCELLED';

export interface OrderItem {
  readonly sku: string;
  readonly quantity: number;
  readonly unitPrice: number;
}

export interface Order {
  readonly id: string;
  readonly reference: string;
  readonly status: OrderStatus;
  readonly dueInDays: number;
  readonly items: readonly OrderItem[];
}

export interface OrderDetail extends Order {
  readonly customerName: string;
  readonly shippingAddress: string;
  readonly notes: string;
}

export interface OrderDraft {
  readonly reference: string;
  readonly items: readonly OrderItem[];
}
