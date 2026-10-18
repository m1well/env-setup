import { createInterceptorCondition, IncludeBearerTokenCondition } from 'keycloak-angular';

export const loose = createInterceptorCondition<IncludeBearerTokenCondition>({
  urlPattern: /^https:\/\/api\.example\.com/i,
});

export const strict = createInterceptorCondition<IncludeBearerTokenCondition>({
  urlPattern: /^(https:\/\/api\.example\.com)(\/.*)?$/i,
});
