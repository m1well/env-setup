import { debounce } from 'lodash-es';

export const later = debounce(() => undefined, 100);
