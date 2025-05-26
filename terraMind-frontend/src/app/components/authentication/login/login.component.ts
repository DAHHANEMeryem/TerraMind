import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AuthService } from '../../../services/auth/auth.service';
import { Router } from '@angular/router';
import { Auth, signInWithPopup, GoogleAuthProvider } from '@angular/fire/auth';
import { ToastrService } from 'ngx-toastr';
import { switchMap } from 'rxjs/operators';
import { from } from 'rxjs';
import { Firestore, doc, getDoc,setDoc } from '@angular/fire/firestore';
import { UserService } from 'src/app/services/user/user.service';
import { lastValueFrom } from 'rxjs';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  loginError: string | null = null;
  successMessage: string | null = null;
  showPassword: boolean = false;

  loginForm: FormGroup = this.fb.group({
    identifiant: ['', [Validators.required]], // Email ou nom d'utilisateur
    mot_de_passe: ['', [Validators.required]]
  });

  constructor(private fb: FormBuilder, private authService: AuthService, private router: Router,
    private auth: Auth, private toastr: ToastrService, private firestore: Firestore,
  private userService : UserService) { }

  login(): void {
    const { identifiant, mot_de_passe } = this.loginForm.value;

    const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(identifiant);

    const loginObservable = isEmail
      ? this.authService.loginWithEmail(identifiant, mot_de_passe)
      : this.authService.loginWithUsername(identifiant, mot_de_passe);

    loginObservable.pipe(
      switchMap(userCredential => {
        const uid = userCredential.user.uid;
        const userDocRef = doc(this.firestore, `users/${uid}`);
        return from(getDoc(userDocRef));
      })
    ).subscribe({
      next: (userDocSnap) => {
        if (userDocSnap.exists()) {
          const userData = userDocSnap.data();

          // Vérification du champ is_blocked
          if (userData['is_blocked'] === true) {
            this.loginError = "Compte bloqué, accès refusé.";
            this.successMessage = "";
            return; // Stop la suite
          }

          const role = userData['role'];
          console.log('Role récupéré :', role);

          this.loginError = "";
          this.successMessage = "Login réussie !";

          setTimeout(() => {
            const roleNormalized = role.toLowerCase().trim();

            console.log('Role normalisé pour redirection:', roleNormalized);

            if (roleNormalized === 'admin') {
              this.router.navigate(['/admin']);
            } else if (roleNormalized === 'user') {
              this.router.navigate(['/chat']);
            } else {
              this.router.navigate(['/']);
            }
          }, 1000);

        } else {
          this.loginError = "Utilisateur introuvable.";
        }
      },
      error: (err) => {
        console.error("Erreur de login", err);
        if (err.message === 'Veuillez vérifier votre email avant de vous connecter.') {
          this.loginError = err.message;
        } else {
          this.loginError = "Identifiant ou mot de passe incorrect.";
        }
      }
    });
  }



handleGoogleLogin() {
  const provider = new GoogleAuthProvider();
  signInWithPopup(this.auth, provider)
    .then(async (result) => {
      const user = result.user;

      const userData = {
        id: user.uid,
        nom: user.displayName,
        nom_utilisateur: user.displayName, // ou une transformation si besoin
        email: user.email,
        role: 'User'
      };

      const userRef = doc(this.firestore, `users/${user.uid}`);
      const usernameRef = doc(this.firestore, `usernames/${user.displayName}`);

      const userDoc = await getDoc(userRef);

      if (!userDoc.exists()) {
        // Si l'utilisateur n'existe pas encore dans Firestore
        await setDoc(userRef, {
          nom: user.displayName,
          nom_utilisateur: user.displayName,
          email: user.email,
          role: 'User',
          is_blocked: false
        });

        await setDoc(usernameRef, {
          email: user.email
        });

        // Envoi au backend Flask
        try {
          await lastValueFrom(this.userService.addUser(userData));
          console.log('Utilisateur enregistré sur le backend');
        } catch (error) {
          console.error('Erreur backend:', error);
        }
      }

      this.successMessage = `Bienvenue ${user.displayName}`;
      this.loginError = null;
      this.router.navigate(['/chat']);
    })
    .catch((error) => {
      console.error(error);
      this.loginError = "Échec de la connexion avec Google.";
      this.successMessage = null;
    });
}


  onForgotPassword() {
    const email = this.loginForm.get('identifiant')?.value;
    console.log("Email saisi :", email);

    const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    if (!email || !isEmail) {
      this.toastr.error("Veuillez entrer une adresse email valide.");
      this.loginError = "Veuillez entrer une adresse email valide.";
      return;
    }

    this.authService.resetPassword(email).subscribe({
      next: () => {
        this.toastr.success("Un email de réinitialisation a été envoyé. Vérifiez votre boîte de réception.");
        this.successMessage = "Le lien de réinitialisation a été envoyé à votre adresse email.";
      },
      error: (err) => {
        console.error("Erreur lors de la réinitialisation :", err);
        this.toastr.error("Erreur lors de l'envoi de l'email : " + err.message);
        this.loginError = "Une erreur est survenue lors de la demande de réinitialisation.";
      }
    });
  }






}
