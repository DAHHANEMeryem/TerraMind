import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { from, lastValueFrom } from 'rxjs';
import { inject } from '@angular/core';
import { Auth } from '@angular/fire/auth';
import { deleteDoc, doc, Firestore } from '@angular/fire/firestore';


@Injectable({
  providedIn: 'root'
})
export class UserService {
  auth = inject(Auth);
  firestore = inject(Firestore);


  private baseUrl = 'http://localhost:5000/user';

  constructor(private http: HttpClient) { }

  getUsers(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/`);
  }

  deleteUser(userId: string, username: string): Observable<any> {
    return from(
      (async () => {
        const currentUser = this.auth.currentUser;
        if (!currentUser) throw new Error("Tu n'es pas connecté");

        const token = await currentUser.getIdToken(true);

        try {
          await lastValueFrom(this.http.delete(
            `${this.baseUrl}/delete-user/${userId}/${username}`,
            { headers: { Authorization: `Bearer ${token}` } }
          ));
          return { message: 'Utilisateur supprimé' };
        } catch (err: any) {
          // Par exemple si on essaie de supprimer soi-même, le serveur renvoie 403 avec un message
          if (err.status === 403) {
            throw new Error(err.error.error || "Action interdite");
          }
          throw err;
        }
      })()
    );
  }



  blockOrUnblockUser(userId: string) {
    return this.http.put<any>(`${this.baseUrl}/toggle_block_user/${userId}`, {});
  }

  getRoles(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/roles`);
  }

    addUser(userData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/add_user`, userData);
  }

}
