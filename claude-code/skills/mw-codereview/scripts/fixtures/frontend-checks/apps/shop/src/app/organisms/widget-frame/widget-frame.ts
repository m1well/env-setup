import { Component, ElementRef, input, viewChild } from '@angular/core';

@Component({
  selector: 'app-widget-frame',
  templateUrl: './widget-frame.html',
})
export class WidgetFrame {
  readonly markup = input.required<string>();
  private readonly frame = viewChild.required<ElementRef<HTMLIFrameElement>>('frame');

  render(): void {
    this.frame().nativeElement.contentWindow?.document.write(this.markup());
  }
}
