import { provideZonelessChangeDetection } from '@angular/core';
import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { App } from './app/app';
import { routes } from './app/app.routes';

bootstrapApplication(App, { providers: [provideZonelessChangeDetection(), provideRouter(routes)] });
