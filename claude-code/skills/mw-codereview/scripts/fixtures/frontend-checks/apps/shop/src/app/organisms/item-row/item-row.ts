import { Component, input, output } from '@angular/core';

@Component({
  selector: 'app-item-row',
  templateUrl: './item-row.html',
})
export class ItemRow {
  readonly id = input.required<string>();
  readonly removed = output<string>();
}
