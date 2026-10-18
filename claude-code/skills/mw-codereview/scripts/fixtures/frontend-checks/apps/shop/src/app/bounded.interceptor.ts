import { HttpInterceptorFn } from '@angular/common/http';
import { environment } from '../environments/environment';

export const boundedInterceptor: HttpInterceptorFn = (req, next) => {
  const base = environment.apiUrl.replace(/\/+$/, '');
  if (req.url !== base && !req.url.startsWith(`${base}/`)) return next(req);
  return next(req.clone({ setHeaders: { Authorization: 'Bearer x' } }));
};
