import { Component, OnInit } from '@angular/core';
import { AssistantService } from 'src/app/services/assistant/assistant.service';
import { ChangeDetectorRef } from '@angular/core';

@Component({
  selector: 'app-MainLayout',
  templateUrl: './MainLayout.component.html',
  styleUrls: ['./MainLayout.component.scss']
})
export class MainLayoutComponent implements OnInit {
  isSidebarCollapsed = false;
  afficherAssistants = false;
  assistantsSelectionnes: any[] = [];
  assistantsPrincipaux: any[] = [];

  constructor(private assistantService: AssistantService, private cdr: ChangeDetectorRef) {}

  ngOnInit() {
    // Charger les assistants sélectionnés depuis localStorage
    const data = localStorage.getItem('assistantsSelectionnes');
    if (data) {
      this.assistantsSelectionnes = JSON.parse(data);
    }

    // Charger la liste principale d'assistants
   this.rechargerAssistantsPrincipaux();

  }

  mettreAJourListePrincipale(nouvelleListe: any[]) {
    this.assistantsPrincipaux = nouvelleListe;
    // Synchroniser la sidebar avec la liste principale
    this.assistantsSelectionnes = this.assistantsSelectionnes.filter(sel =>
      this.assistantsPrincipaux.some(principal => principal.assistantId === sel.assistantId)
    );

    localStorage.setItem('assistantsSelectionnes', JSON.stringify(this.assistantsSelectionnes));
  }

  rechargerAssistantsPrincipaux() {
  this.assistantService.get_assistants_for_current_user().subscribe(data => {
    this.mettreAJourListePrincipale(data);
  });
}


  ouvrirAssistants() {
    this.afficherAssistants = true;
  }

  fermerAssistants() {
    this.afficherAssistants = false;
  }

onAssistantAjoute(assistant: any) {
  const existe = this.assistantsSelectionnes.some(a => a.assistantId === assistant.assistantId);
  if (!existe) {
    this.assistantsSelectionnes.push(assistant);
    this.assistantsSelectionnes = [...this.assistantsSelectionnes]; // <-- force la mise à jour Angular
    localStorage.setItem('assistantsSelectionnes', JSON.stringify(this.assistantsSelectionnes));
    this.rechargerAssistantsPrincipaux();
    this.cdr.detectChanges();

  }
}

onAssistantSupprime(assistant: any) {
  this.assistantsSelectionnes = this.assistantsSelectionnes.filter(a => a.assistantId !== assistant.assistantId);
  localStorage.setItem('assistantsSelectionnes', JSON.stringify(this.assistantsSelectionnes));
  this.assistantsSelectionnes = [...this.assistantsSelectionnes]; // <-- force la mise à jour Angular
  this.rechargerAssistantsPrincipaux();
  this.cdr.detectChanges();

}


  toggleSidebarState(collapsed: boolean) {
    this.isSidebarCollapsed = collapsed;
  }
}
