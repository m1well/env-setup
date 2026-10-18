import { Component, input } from '@angular/core';

@Component({
  selector: 'app-print-frame',
  template: '<button type="button" (click)="print()">Print</button>',
})
export class PrintFrame {
  readonly receipt = input.required<string>();

  print(): void {
    const frame = document.createElement('iframe');
    frame.srcdoc = this.receipt();
    document.body.appendChild(frame);
  }
}
