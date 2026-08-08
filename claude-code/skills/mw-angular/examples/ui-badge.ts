import { Component, input } from '@angular/core';

/**
 * Atom: domain-free, injects nothing, imports nothing.
 * Lives in ui/atoms/ and may be used by any feature.
 */
@Component({
  selector: 'app-ui-badge',
  templateUrl: './ui-badge.html',
  styleUrl: './ui-badge.css',
  host: {
    class: 'ui-badge',
    '[class.ui-badge--warning]': 'tone() === "warning"',
  },
})
export class UiBadge {
  readonly label = input.required<string>();
  readonly tone = input<'neutral' | 'warning'>('neutral');
}
