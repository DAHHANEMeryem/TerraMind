import { Component, OnInit } from '@angular/core';
import { FormGroup, Validators, FormBuilder } from '@angular/forms';
import { AuthService } from '../../../services/auth/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss']
})
export class RegisterComponent implements OnInit {
  registerError: string | null = null;
  successMessage: string | null = null;
  showPassword: boolean = false;
  showConfirmPassword: boolean = false;

  registerForm: FormGroup = this.fb.group({
    nom: ['', Validators.required],
    nom_utilisateur: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    role: ['USER', Validators.required],
    mot_de_passe: ['', [Validators.required, Validators.minLength(6)]],
    confirmer_mot_de_passe: ['', Validators.required]
  });

  constructor(private fb: FormBuilder, private authService: AuthService, private router: Router) { }
  ngOnInit() {

  }

  register(): void {
    if (this.registerForm.get('mot_de_passe')?.value !== this.registerForm.get('confirmer_mot_de_passe')?.value) {
      this.registerError = 'Les mots de passe ne correspondent pas.';
      return;
    }

    const email = this.registerForm.get('email')?.value;
    const password = this.registerForm.get('mot_de_passe')?.value;
    const nom = this.registerForm.get('nom')?.value;
    const nom_utilisateur = this.registerForm.get('nom_utilisateur')?.value;
    const role = this.registerForm.get('role')?.value; // 👈 récupérer le rôle

    this.authService.register(email, password, nom, nom_utilisateur, role).subscribe({
      next: (res) => {
        this.successMessage = 'Inscription réussie. Un e-mail de vérification vous a été envoyé.';
        this.registerError = null;
        console.log("Inscrit avec succès", res);
        setTimeout(() => {
          this.router.navigate(['/login']);
        }, 2000);
      },
      error: (err) => {
        if (err.message) {
          this.registerError = err.message;
        }
        this.successMessage = null;
        console.error("Erreur d'inscription", err);
      }
    });
  }




}
