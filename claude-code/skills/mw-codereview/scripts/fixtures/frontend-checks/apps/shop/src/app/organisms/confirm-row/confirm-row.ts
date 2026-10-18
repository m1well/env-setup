import { Component, input, output } from '@angular/core';

@Component({
  selector: 'app-confirm-row',
  templateUrl: './confirm-row.html',
})
export class ConfirmRow {
  readonly id = input.required<string>();
  readonly deleted = output<string>();

  protected remove(): void {
    this.deleted.emit(this.id());
  }
}
