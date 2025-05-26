import { Component, OnInit } from '@angular/core';

import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AssistantService } from 'src/app/services/assistant/assistant.service';
import { AuthService } from 'src/app/services/auth/auth.service';
import { HistoryService } from 'src/app/services/history/history.service';
import { UserService } from 'src/app/services/user/user.service';

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.scss']
})
export class AdminComponent implements OnInit {
  users: any[] = [];
  filteredUsers: any[] = [];
  searchUser: string = '';
  isModalOpen = false;
  roles: any[] = [];
  currentUserPage: number = 1;
  usersPerPage: number = 5;

  editingUser: any = null;
  showHistory = false;
  histories: any[] = [];
  currentHistoryPage: number = 1;
  historiesPerPage: number = 5;

  searchHistory: string = '';
  filteredHistories: any[] = [];
  chats: any[] = [];
  selectedChatMessages: any[] = [];
  currentView: 'users' | 'histories' | 'details' = 'users';

  selectedUser: any = null;
  showAssistantModal: boolean = false;
  assistants: any[] = [];
  selectedAssistants: number[] = [];

  showPassword: boolean = false;
  showConfirmPassword: boolean = false;


  registerForm!: FormGroup;
  registerError: string | null = null;
  successMessage: string | null = null;

  constructor(private fb: FormBuilder, private authService: AuthService, private historyService: HistoryService,
    private userService: UserService, private assistantService: AssistantService) { }

  ngOnInit() {
    this.getUsers();
    this.getRoles();
    this.filteredHistories = this.histories;
    this.registerForm = this.fb.group({
      nom: ['', Validators.required],
      nom_utilisateur: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      role: ['', Validators.required],
      mot_de_passe: ['', [Validators.required, Validators.minLength(6)]],
      confirmer_mot_de_passe: ['', [Validators.required, Validators.minLength(6)]]
    });
  }

  getRoles() {
    this.userService.getRoles().subscribe({
      next: (data) => {
        this.roles = data;
      },
      error: (err) => {
        console.error('Erreur lors du chargement des rôles', err);
      }
    });
  }


  filterUsers(): void {
    const term = this.searchUser.toLowerCase();
    this.filteredUsers = this.users.filter(user =>
      user.nom.toLowerCase().includes(term) ||
      user.email.toLowerCase().includes(term) ||
      user.role.toLowerCase().includes(term)
    );
    this.currentUserPage = 1; // réinitialise la page
  }

  getUsers(): void {
    this.userService.getUsers().subscribe((data) => {
      this.users = data.map(user => ({
        ...user,
        isBlocked: user.is_blocked
      }));
      this.filteredUsers = this.users;
    });
  }

  get paginatedUsers(): any[] {
    const startIndex = (this.currentUserPage - 1) * this.usersPerPage;
    return this.filteredUsers.slice(startIndex, startIndex + this.usersPerPage);
  }

  get totalPages(): number {
    return Math.ceil(this.filteredUsers.length / this.usersPerPage);
  }

  onDeleteUser(user: any) {
    if (confirm(`Voulez-vous vraiment supprimer ${user.nom} ?`)) {
      this.userService.deleteUser(user.id, user.nom_utilisateur).subscribe({
        next: () => {
          alert('Utilisateur supprimé');
          this.getUsers();
        },
        error: (err) => {
          const errorMessage = err || 'Erreur lors de la suppression';
          alert(errorMessage);
          console.error(err);
        }
      });
    }
  }

  openModal(user?: any) {
    this.isModalOpen = true;
    if (user) {
      this.editingUser = user;
      this.registerForm.patchValue({
        nom: user.nom,
        nom_utilisateur: user.nom_utilisateur,
        email: user.email,
        role: user.role,
      });

      // Ne pas afficher les champs de mot de passe en modification
      this.registerForm.get('mot_de_passe')?.clearValidators();
      this.registerForm.get('confirmer_mot_de_passe')?.clearValidators();
      this.registerForm.get('mot_de_passe')?.updateValueAndValidity();
      this.registerForm.get('confirmer_mot_de_passe')?.updateValueAndValidity();

    } else {
      this.editingUser = null;
      this.registerForm.reset();

      // Ajouter les validateurs de mot de passe
      this.registerForm.get('mot_de_passe')?.setValidators([Validators.required, Validators.minLength(6)]);
      this.registerForm.get('confirmer_mot_de_passe')?.setValidators([Validators.required, Validators.minLength(6)]);
      this.registerForm.get('mot_de_passe')?.updateValueAndValidity();
      this.registerForm.get('confirmer_mot_de_passe')?.updateValueAndValidity();
    }
    this.successMessage = null;
    this.registerError = null;
  }

  closeModal() {
    this.isModalOpen = false;
    this.registerForm.reset();
    this.editingUser = null;
    this.successMessage = null;
    this.registerError = null;
  }

  onSubmit() {
    this.successMessage = null;
    this.registerError = null;

    if (!this.editingUser) {
      // === AJOUT ===
      if (this.registerForm.get('mot_de_passe')?.value !== this.registerForm.get('confirmer_mot_de_passe')?.value) {
        this.registerError = 'Les mots de passe ne correspondent pas.';
        return;
      }

      const { email, mot_de_passe, nom, nom_utilisateur, role } = this.registerForm.value;

      this.authService.register(email, mot_de_passe, nom, nom_utilisateur, role).subscribe({
        next: () => {
          this.successMessage = 'Utilisateur ajouté avec succès. Un e-mail de vérification vous a été envoyé.';
          this.getUsers();
          setTimeout(() => this.closeModal(), 2000);
        },
        error: (err) => {
          if (err && err.message) {
            this.registerError = err.message;
          } else if (err.error) {
            this.registerError = err.error;
          } else {
            this.registerError = 'Erreur lors de l’ajout.';
          }
        }
      });
    } else {
      const { nom, nom_utilisateur, email, role } = this.registerForm.value;

      const updatedUser = {
        nom,
        nom_utilisateur,
        email,
        role
      };

      this.authService.updateUser(this.editingUser.id, updatedUser.email, updatedUser.nom, updatedUser.nom_utilisateur, updatedUser.role).subscribe({
        next: () => {
          this.successMessage = 'Utilisateur modifié avec succès.';
          this.getUsers();
          setTimeout(() => this.closeModal(), 2000);
        },
        error: (err) => {
          if (err && err.message) {
            this.registerError = err.message;
          } else if (err.error) {
            this.registerError = err.error;
          } else {
            this.registerError = 'Erreur lors de l’ajout.';
          }
        }
      });
    }
  }

  blockOrUnblockUser(user: any) {
    this.userService.blockOrUnblockUser(user.id).subscribe({
      next: (res) => {
        user.isBlocked = res.is_blocked;
      },
      error: (err) => {
        console.error("Erreur lors du blocage/déblocage :", err);
        alert("Échec du blocage/déblocage de l'utilisateur.");
      }
    });
  }

  filterHistories() {
    const search = this.searchHistory.toLowerCase();
    this.filteredHistories = this.histories.filter(hist =>
      hist.assistant_name.toLowerCase().includes(search) ||
      hist.title.toLowerCase().includes(search)
    );
    this.currentHistoryPage = 1;
  }

  viewHistory(user: any) {
    this.currentView = 'histories'; // On passe à l'affichage des historiques
    this.historyService.get_all_chat_sessions().subscribe({
      next: (data: any[]) => {
        this.histories = data.filter(h => h.user_id === user.id);
        this.filteredHistories = [...this.histories];
      },
      error: (err: any) => {
        console.error('Erreur chargement historique:', err);
        alert('Impossible de charger l’historique');
      }
    });
  }
  get paginatedHistories(): any[] {
    const startIndex = (this.currentHistoryPage - 1) * this.historiesPerPage;
    return this.filteredHistories.slice(startIndex, startIndex + this.historiesPerPage);
  }

  get totalHistoryPages(): number {
    return Math.ceil(this.filteredHistories.length / this.historiesPerPage);
  }

  loadChatDetails(chat: any): void {
    this.currentView = 'details'; // On passe à l'affichage des détails
    this.historyService.getChatDetails(chat.user_id, chat.session_id).subscribe({
      next: messages => this.selectedChatMessages = messages,
      error: err => console.error('Erreur détails chat', err)
    });
  }


  back(): void {
    if (this.currentView === 'details') {
      this.currentView = 'histories';
      this.selectedChatMessages = [];
    } else if (this.currentView === 'histories') {
      this.currentView = 'users';
      this.histories = [];
      this.filteredHistories = [];
    }
  }

  openAssistantModal(user: any) {
    this.selectedUser = user;
    this.showAssistantModal = true;
    this.selectedAssistants = [];

    // Charger tous les assistants
    this.assistantService.get_all_assistants().subscribe({
      next: (assistants) => {
        this.assistants = assistants;

        // Charger les assistants liés à l'utilisateur sélectionné
        this.assistantService.getUserAssistants(user.id).subscribe({
          next: (userAssistantsIds: number[]) => {
            this.selectedAssistants = userAssistantsIds;
          },
          error: (err) => {
            console.error("Erreur lors de la récupération des assistants de l'utilisateur", err);
            this.selectedAssistants = [];
          }
        });
      },
      error: (err) => {
        console.error("Erreur lors de la récupération des assistants", err);
      }
    });
  }

  toggleAssistantSelection(assistantId: number) {
    const index = this.selectedAssistants.indexOf(assistantId);
    if (index > -1) {
      this.selectedAssistants.splice(index, 1);
    } else {
      this.selectedAssistants.push(assistantId);
    }
  }
  closeAssistantModal() {
    this.showAssistantModal = false;
    this.selectedUser = null;
    this.selectedAssistants = [];
  }

  saveAssistants() {
    if (!this.selectedUser) return;

    const userId = this.selectedUser.id;
    const assistantsIds = this.selectedAssistants;

    // Appelle le service pour enregistrer la liste des assistants liés à cet utilisateur
    this.assistantService.updateUserAssistants(userId, assistantsIds).subscribe({
      next: () => {
        alert('Assistants mis à jour avec succès.');
        this.closeAssistantModal();
      },
      error: (err) => {
        alert('Erreur lors de la mise à jour des assistants');
        console.error(err);
      }
    });
  }



}
