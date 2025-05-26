import { Component, HostListener, OnInit, Output, EventEmitter,Input } from '@angular/core';
import { SharedService } from '../../../services/shared/shared.service';
import { HistoryService } from 'src/app/services/history/history.service';


@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent implements OnInit {
  isSearchOpen = false;
  searchQuery: string = "";
  historyItems: any[] = [];
  sidebarState: boolean = true;
  isCollapsed = false;
  @Output() sidebarToggled = new EventEmitter<boolean>();

  selectedAssistant: string | null = null;
  @Output() ajouterAssistantEvent = new EventEmitter<void>();
  @Input() assistants: any[] = [];
  @Output() assistantSupprimeEvent = new EventEmitter<any>();



  constructor(private sharedService: SharedService,
    private historyService: HistoryService) { }

  ngOnInit() {
    this.loadChatSessions();
    const savedAssistant = localStorage.getItem('selectedAssistantName');
    if (savedAssistant) {
      this.selectedAssistant = savedAssistant;
    }
    
  }

  toggleSidebar() {
    this.isCollapsed = !this.isCollapsed;
    this.sidebarToggled.emit(this.isCollapsed);
    this.sidebarState = !this.sidebarState;
  }

  loadChatSessions() {
    const assistant = localStorage.getItem('selectedAssistantName');
    const assistantName = assistant !== null && assistant !== undefined ? assistant : "ChatBot";
    this.historyService.getChatSessions(assistantName).subscribe({
      next: (sessions) => {
        const savedChatId = Number(localStorage.getItem('chatId'));
        this.historyItems = sessions.map(session => ({
          title: session.title,
          showDropdown: false,
          isActive: session.id === savedChatId,
          chatId: session.id
        }));
      },
      error: (err) => {
        console.error("Erreur lors du chargement des sessions :", err);
      }
    });

  }

  afficheChat(chatId: number) {
    const selectedItem = this.historyItems.find(item => item.chatId === chatId);
    this.setActiveChat(selectedItem);

    console.log('Chat ID:', chatId);

    if (chatId !== undefined && chatId !== null) {
      this.sharedService.setChatId(chatId);
      this.isSearchOpen = false
      // 🔥 Ajouter cette ligne :
      localStorage.setItem('chatId', chatId.toString());
    } else {
      console.error('Chat ID is undefined');
    }
  }

  setActiveChat(selectedItem: any) {
    this.historyItems.forEach(item => item.isActive = false);
    selectedItem.isActive = true;
  }

  toggleSearch() {
    this.isSearchOpen = !this.isSearchOpen;  // Inverse l'état de la recherche
    if (this.isSearchOpen) {
      this.searchQuery = '';  // Réinitialise la requête de recherche quand le modal est ouvert
    }
  }

  filteredHistory() {
    return this.historyItems.filter(chat =>
      chat.title.toLowerCase().includes(this.searchQuery.toLowerCase())
    );
  }

  toggleDropdown(item: any) {
    this.historyItems.forEach((i) => {
      if (i !== item) {
        i.showDropdown = false;
        i.isActive = false;
      }
    });

    item.showDropdown = !item.showDropdown;
    item.isActive = item.showDropdown;
  }

  @HostListener('document:click', ['$event'])
  closeMenusOnClickOutside(event: Event) {
    const targetElement = event.target as HTMLElement;

    // Ferme seulement les dropdowns, ne touche pas à isActive ici
    if (!targetElement.closest('.options-menu') && !targetElement.closest('.dropdown')) {
      this.historyItems.forEach(item => item.showDropdown = false);
    }

    if (!targetElement.closest('.search-container') && !targetElement.closest('.search')) {
      this.isSearchOpen = false;
    }
  }

  newChat() {
    this.sharedService.startNewChat();
    this.loadChatSessions();

  }

  enableEdit(item: any) {
    item.isEditing = true;
    item.newTitle = item.title;
  }

  updateTitle(item: any) {
    if (item.newTitle && item.newTitle !== item.title) {
      // Appeler l'API pour mettre à jour le titre dans la base de données
      this.historyService.updateTitleSession(item.chatId, item.newTitle).subscribe({
        next: (response) => {
          item.title = item.newTitle;  // Mettre à jour le titre localement
          item.isEditing = false;      // Désactiver le mode édition
        },
        error: (err) => {
          console.error("Erreur lors de la mise à jour du titre :", err);
          alert("Une erreur est survenue lors de la mise à jour du titre.");
          item.isEditing = false;  // Désactiver le mode édition même en cas d'erreur
        }
      });
    } else {
      item.isEditing = false;  // Désactiver l'édition si le titre n'a pas changé
    }
  }

  confirmDelete(item: any, event: Event) {
    event.stopPropagation(); // Empêche le clic de déclencher l'affichage du chat
    console.log(item.chatId)
    const confirmed = confirm(`Voulez-vous vraiment supprimer la session "${item.title}" ?`);
    if (confirmed) {
      console.log('ID de la session à supprimer:', item.chatId);  // Vérifie l'ID de la session
      this.historyService.deleteSession(item.chatId).subscribe({
        next: (res) => {
          this.historyItems = this.historyItems.filter(h => h.chatId !== item.chatId);
        },
        error: (err) => {
          console.error('Erreur suppression:', err);
          alert('Erreur lors de la suppression de la session.');
        }
      });
    }
  }

 

  saveAssistantNameToLocalStorage(assistantName: string) {
    // Si l'assistant cliqué est déjà sélectionné, on le désélectionne
    if (this.selectedAssistant === assistantName) {
      localStorage.removeItem('selectedAssistantName');
      this.selectedAssistant = null;
      this.newChat();
      console.log('Assistant désélectionné');
      this.loadChatSessions()
    } else {
      // Sinon, on le sélectionne et l'enregistre dans le localStorage
      localStorage.setItem('selectedAssistantName', assistantName);
      this.selectedAssistant = assistantName;
      this.newChat();
      console.log('Nom de l\'assistant enregistré dans le localStorage:', assistantName);
      this.loadChatSessions()
    }
  }

  afficherAssistant() {
    this.ajouterAssistantEvent.emit(); 
  }
supprimerAssistant(assistant: any, event: MouseEvent) {
  event.stopPropagation(); // pour éviter le clic sur le li
  this.assistantSupprimeEvent.emit(assistant); // Émet vers parent
}







}
