import { Injectable } from '@angular/core';
import { BehaviorSubject, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SharedService {

  constructor() { }

  // Variable de message
  private messageSubject = new BehaviorSubject<string>('');
  message$ = this.messageSubject.asObservable();
  setMessage(message: string) {
    this.messageSubject.next(message);
  }

  // Liste des messages
  private messagesSubject = new BehaviorSubject<{ text: string; isUser: boolean }[]>([]);
  messages$ = this.messagesSubject.asObservable();
  setMessages(messages: { text: string; isUser: boolean }[]) {
    this.messagesSubject.next(messages);
  }

  // Premier message envoyé
  private isFirstMessageSentSubject = new BehaviorSubject<boolean>(false);
  isFirstMessageSent$ = this.isFirstMessageSentSubject.asObservable();
  setFirstMessageSent(status: boolean) {
    this.isFirstMessageSentSubject.next(status);
  }

  // Etat de texte
  private isTextNotEmptySubject = new BehaviorSubject<boolean>(false);
  isTextNotEmpty$ = this.isTextNotEmptySubject.asObservable();
  setIsTextNotEmpty(status: boolean) {
    this.isTextNotEmptySubject.next(status);
  }

  private hasScrollSubject = new BehaviorSubject<boolean>(false);
  hasScroll$ = this.hasScrollSubject.asObservable();
  setHasScroll(value: boolean) {
    this.hasScrollSubject.next(value);
  }

  private newChatSubject = new Subject<void>();
  newChat$ = this.newChatSubject.asObservable();
  startNewChat() {
    this.newChatSubject.next();
  }

  private loggedOutSubject = new BehaviorSubject<boolean>(false);
  loggedOut$ = this.loggedOutSubject.asObservable();

  setLoggedOut(value: boolean) {
    this.loggedOutSubject.next(value);
  }

  private chatIdSubject = new BehaviorSubject<number | null>(null);

  setChatId(chatId: number) {
    this.chatIdSubject.next(chatId);
  }
  getChatId() {
    return this.chatIdSubject.asObservable();
  }




  //asistants

    private assistantsSelectionnesSubject = new BehaviorSubject<any[]>([]);
  assistantsSelectionnes$ = this.assistantsSelectionnesSubject.asObservable();

  // Pour obtenir la dernière valeur
  getCurrentAssistants(): any[] {
    return this.assistantsSelectionnesSubject.getValue();
  }

  setAssistantsSelectionnes(nouvelleListe: any[]) {
    this.assistantsSelectionnesSubject.next(nouvelleListe);
    localStorage.setItem('assistantsSelectionnes', JSON.stringify(nouvelleListe));
  }




}
