import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Auth } from '@angular/fire/auth';
import { from, Observable, of } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {

  constructor(private auth: Auth) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return from(this.auth.currentUser ? this.auth.currentUser.getIdToken() : Promise.resolve('')).pipe(
      switchMap(token => {
        console.log("🔥 TOKEN UTILISÉ POUR LA REQUÊTE:", token);
        if (!token) {
          return next.handle(req); 
        }
  
        const authReq = req.clone({
          setHeaders: {
            Authorization: `Bearer ${token}`
          }
        });
  
        return next.handle(authReq);
      }),
      catchError(error => {
        console.error('Erreur d\'interception', error);
        return next.handle(req);
      })
    );
  }
  
}
