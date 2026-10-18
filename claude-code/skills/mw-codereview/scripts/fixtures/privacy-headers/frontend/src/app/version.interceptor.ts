import { HttpInterceptorFn } from '@angular/common/http';

export const versionInterceptor: HttpInterceptorFn = (req, next) =>
  next(req.clone({ setHeaders: { 'X-Client-Version': '1.4.0', 'X-Requested-With': 'XMLHttpRequest' } }));

export const sizes = ['x-small', 'x-large'];
