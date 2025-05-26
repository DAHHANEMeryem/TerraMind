import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { from, Observable } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { Auth, createUserWithEmailAndPassword, signInWithEmailAndPassword, sendPasswordResetEmail, signOut, GoogleAuthProvider, signInWithPopup } from '@angular/fire/auth';
import { Firestore, doc, setDoc, getDoc } from '@angular/fire/firestore';
import { inject } from '@angular/core';
import { switchMap } from 'rxjs/operators';
import { User as FirebaseUser, updatePassword } from 'firebase/auth';
import { EmailAuthProvider, reauthenticateWithCredential } from 'firebase/auth';
import { sendEmailVerification } from 'firebase/auth';
import { lastValueFrom } from 'rxjs';
import { deleteDoc } from 'firebase/firestore';
import {  updateEmail } from "firebase/auth";

import { getAuth, updateEmail as firebaseUpdateEmail } from "firebase/auth";

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private firestore: Firestore = inject(Firestore);

  constructor(private http: HttpClient, private router: Router, private auth: Auth) { }

  register(
    email: string,
    password: string,
    nom: string,
    nom_utilisateur: string,
    role: string
  ): Observable<any> {
    return from(
      (async () => {
        // Étape 1 : Vérifier si le nom d'utilisateur existe déjà
        const usernameRef = doc(this.firestore, `usernames/${nom_utilisateur}`);
        const usernameDoc = await getDoc(usernameRef);

        if (usernameDoc.exists()) {
          throw new Error("Ce nom d'utilisateur est déjà utilisé");
        }

        // Étape 2 : Créer l'utilisateur Firebase Auth
        const userCredential = await createUserWithEmailAndPassword(this.auth, email, password);
        const user = userCredential.user;

        const userRef = doc(this.firestore, `users/${user.uid}`);
        let firestoreUserCreated = false;
        let firestoreUsernameCreated = false;

        try {
          // Étape 3 : Envoyer un email de vérification
          await sendEmailVerification(user);

          // Étape 4 : Ajouter dans Firestore
          await setDoc(userRef, {
            nom: nom,
            nom_utilisateur: nom_utilisateur,
            email: email,
            role: role,
            is_blocked: false
          });
          firestoreUserCreated = true;

          await setDoc(usernameRef, {
            email: email
          });
          firestoreUsernameCreated = true;

          // Étape 5 : Appel backend
          const userData: any = {
            id: user.uid,
            nom: nom,
            nom_utilisateur: nom_utilisateur,
            email: email,
            role: role
          };

          await lastValueFrom(this.http.post(`http://localhost:5000/user/add_user`, userData));

          return { message: 'Inscription réussie' };

        } catch (error) {
          // Nettoyage en cas d'erreur
          if (firestoreUserCreated) {
            await deleteDoc(userRef);
          }
          if (firestoreUsernameCreated) {
            await deleteDoc(usernameRef);
          }

          if (user) {
            await user.delete(); // Supprime l'utilisateur Firebase Auth
          }

          throw error;
        }
      })().catch(error => {
        // Gestion des erreurs spécifiques
        if (error.code === 'auth/email-already-in-use') {
          throw new Error("Cet email est déjà utilisé");
        }
        throw error;
      })
    );
  }


updateUser(
  id: string,
  email: string,
  nom: string,
  nom_utilisateur: string,
  role: string,
  currentPassword?: string
): Observable<any> {
  return from(
    (async () => {
      const auth = getAuth();
      const currentUser = auth.currentUser;
      if (!currentUser) {
        throw new Error("Utilisateur non authentifié");
      }

      const userRef = doc(this.firestore, `users/${id}`);
      const userDoc = await getDoc(userRef);
      if (!userDoc.exists()) {
        throw new Error("Utilisateur introuvable");
      }

      const oldUserData = userDoc.data();
      const oldNomUtilisateur = oldUserData?.['nom_utilisateur'] || null;
      const oldEmail = oldUserData?.['email'] || null;

      if (nom_utilisateur !== oldNomUtilisateur) {
        const newUsernameRef = doc(this.firestore, `usernames/${nom_utilisateur}`);
        const newUsernameDoc = await getDoc(newUsernameRef);
        if (newUsernameDoc.exists()) {
          throw new Error("Ce nom d'utilisateur est déjà utilisé");
        }
      }

      if (email !== oldEmail && email !== currentUser.email) {
        if (!currentPassword) {
          throw new Error("Mot de passe requis pour changer l'adresse e-mail.");
        }
        try {
          const credential = EmailAuthProvider.credential(currentUser.email!, currentPassword);
          await reauthenticateWithCredential(currentUser, credential);

          await updateEmail(currentUser, email);

          await sendEmailVerification(currentUser);

          return { message: "Email mis à jour. Veuillez vérifier votre nouveau mail pour confirmation." };
        } catch (error: any) {
          if (error.code === 'auth/requires-recent-login') {
            throw new Error("Merci de vous reconnecter pour changer l'adresse e-mail.");
          } else {
            throw new Error("Erreur lors de la mise à jour de l'e-mail : " + error.message);
          }
        }
      }

      await setDoc(userRef, { nom, nom_utilisateur, email, role }, { merge: true });

      if (nom_utilisateur !== oldNomUtilisateur) {
        if (oldNomUtilisateur) {
          const oldUsernameRef = doc(this.firestore, `usernames/${oldNomUtilisateur}`);
          await deleteDoc(oldUsernameRef);
        }
        const newUsernameRef = doc(this.firestore, `usernames/${nom_utilisateur}`);
        await setDoc(newUsernameRef, { email, ownerUid: currentUser.uid }, { merge: true });
      } else {
        const usernameRef = doc(this.firestore, `usernames/${nom_utilisateur}`);
        await setDoc(usernameRef, { email, ownerUid: currentUser.uid }, { merge: true });
      }

      const userData = { id, nom, nom_utilisateur, email, role };
      await lastValueFrom(this.http.put(`http://localhost:5000/user/update_user/${id}`, userData));

      return { message: "Utilisateur modifié avec succès" };
    })().catch((error) => {
      throw new Error("Erreur : " + error.message);
    })
  );
}

  //login
  loginWithEmail(email: string, password: string): Observable<any> {
    return from(signInWithEmailAndPassword(this.auth, email, password)).pipe(
      switchMap((userCredential) => {
        const user = userCredential.user;
        if (user.emailVerified) {
          return of(userCredential); // Connexion réussie si l'email est vérifié
        } else {
          throw new Error('Veuillez vérifier votre email avant de vous connecter.');
        }
      })
    );
  }

  loginWithUsername(username: string, password: string): Observable<any> {
    const usernamesDoc = doc(this.firestore, `usernames/${username}`);

    return from(getDoc(usernamesDoc)).pipe(
      switchMap((docSnap) => {
        if (docSnap.exists()) {
          const email = docSnap.data()['email'];
          console.log('Email trouvé:', email);
          return this.loginWithEmail(email, password);
        } else {
          throw new Error('Nom d’utilisateur non trouvé');
        }
      })
    );
  }

  //logout
  logout(): Observable<void> {
    return from(signOut(this.auth));
  }

  logoutAndRedirect(): void {
    this.logout().subscribe({
      next: () => {
        console.log('Déconnexion réussie');
        this.router.navigate(['/login']);
      },
      error: (err) => {
        console.error('Erreur lors de la déconnexion', err);
      },
    });
  }

  resetPassword(email: string): Observable<void> {
    return from(sendPasswordResetEmail(this.auth, email)).pipe(
      catchError((error: any) => {
        console.error("Erreur lors de l'envoi de l'email de réinitialisation : ", error);
        return of();
      })
    );
  }

  reauthAndUpdatePassword(currentPassword: string, newPassword: string): Observable<void> {
    const user = this.auth.currentUser;
    if (!user || !user.email) return of();

    const credential = EmailAuthProvider.credential(user.email, currentPassword);
    return from(
      reauthenticateWithCredential(user, credential).then(() => {
        return updatePassword(user, newPassword);
      })
    );
  }

  getConnectedUserInfo(): Observable<any> {
    const user = this.auth.currentUser;
    if (!user) return of(null);

    const userRef = doc(this.firestore, `users/${user.uid}`);
    return from(getDoc(userRef)).pipe(
      switchMap((snap) => {
        if (snap.exists()) {
          return of(snap.data());
        } else {
          return of(null);
        }
      })
    );
  }



}
