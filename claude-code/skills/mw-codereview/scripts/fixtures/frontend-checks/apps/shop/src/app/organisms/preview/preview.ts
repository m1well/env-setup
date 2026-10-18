import { Component, effect, ElementRef, input, viewChild } from '@angular/core';

@Component({
  selector: 'app-preview',
  templateUrl: './preview.html',
})
export class Preview {
  readonly html = input.required<string>();
  private readonly frame = viewChild.required<ElementRef<HTMLIFrameElement>>('frame');

  private readonly write = effect(() => {
    const doc = this.frame().nativeElement.contentDocument;
    doc?.open();
    doc?.write(this.html());
    doc?.close();
  });
}
