import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-order-lines',
  templateUrl: './order-lines.html',
})
export class OrderLines {
  protected readonly lines = signal<string[]>(['']);

  protected removeLine(index: number): void {
    this.lines.update(lines => lines.filter((_, i) => i !== index));
  }
}
