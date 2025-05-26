import { Component, ViewChild, ElementRef, OnInit, OnDestroy, Input, OnChanges, Output, EventEmitter } from '@angular/core';
import { SharedService } from '../../../services/shared/shared.service';
import { ChatService } from 'src/app/services/chat/chat.service';
import { AssistantService } from 'src/app/services/assistant/assistant.service';


@Component({
  selector: 'app-main-content',
  templateUrl: './main-content.component.html',
  styleUrls: ['./main-content.component.scss']
})
export class MainContentComponent implements OnInit, OnChanges {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;
  message: string = "";
  chatId: number | undefined;
  messages: { text: string; isUser: boolean }[] = [];
  selectedFiles: File[] = [];
  isFirstMessageSent: boolean = false;
  isTextNotEmpty: boolean = false;
  @Input() collapsed: boolean = false;

  @Input() afficherAssistants: boolean = false;
  @Output() fermerAssistantsEvent = new EventEmitter<void>();
  @Output() assistantAjouteEvent = new EventEmitter<any>();
  assistants: any[] = [];


  constructor(private sharedService: SharedService, private chatService: ChatService,
    private assistantService: AssistantService) { }


  ngOnInit() {

    this.sharedService.loggedOut$.subscribe((isLoggedOut) => {
      if (isLoggedOut) {
        this.resetChat();
        localStorage.removeItem('chatId');
      } else {
        const savedChatId = localStorage.getItem('chatId');
        if (savedChatId) {
          this.chatId = Number(savedChatId);
          this.loadMessages(this.chatId);
          this.sharedService.setFirstMessageSent(true);
        }
      }
    });

    this.sharedService.isTextNotEmpty$.subscribe(status => {
      this.isTextNotEmpty = status;
    });

    this.sharedService.messages$.subscribe(msgs => {
      this.messages = msgs;
    });

    this.sharedService.isFirstMessageSent$.subscribe(status => {
      this.isFirstMessageSent = status;
    });

    this.sharedService.getChatId().subscribe((chatId) => {
      if (chatId !== null) {
        this.chatId = chatId;
        localStorage.setItem('chatId', chatId.toString());
        this.loadMessages(this.chatId);
        this.sharedService.setFirstMessageSent(true);
      }
    });

    this.sharedService.newChat$.subscribe(() => {
      this.resetChat();
    });
  }

  ngAfterViewInit() {
    this.checkScroll();
  }

  resetChat() {
    this.sharedService.setMessages([]);
    this.message = '';
    this.sharedService.setFirstMessageSent(false);
    this.sharedService.setIsTextNotEmpty(false);
    this.chatId = undefined;
    localStorage.removeItem('chatId');
    this.sharedService.setHasScroll(false);
  }

  toggleIcons(event: Event): void {
    const textarea = event.target as HTMLTextAreaElement;
    const isNotEmpty = textarea.value.trim().length > 0;
    this.sharedService.setIsTextNotEmpty(isNotEmpty);
  }

  scrollToBottom() {
    if (this.messagesContainer) {
      setTimeout(() => {
        this.messagesContainer.nativeElement.scrollTop = this.messagesContainer.nativeElement.scrollHeight;
        this.checkScroll();
      }, 0);
    }
  }

  checkScroll() {
    if (this.messagesContainer) {
      const element = this.messagesContainer.nativeElement;
      const hasScroll = element.scrollHeight > element.clientHeight;
      this.sharedService.setHasScroll(hasScroll);
    }
  }

  sendMessage(event: Event) {
    event.preventDefault();
    this.message = this.message.trim();

    if (this.message.length === 0) {
      return;
    }

    const fullMessage = this.message;
    const firstWords = fullMessage.split(' ').slice(0, 4).join(' ');

    // Affiche immédiatement le message de l'utilisateur
    const userMessage = this.message;
    const updatedMessages = [...this.messages, { text: userMessage, isUser: true }];
    this.sharedService.setMessages(updatedMessages);
    this.message = '';
    this.sharedService.setIsTextNotEmpty(false);
    this.scrollToBottom();

    if (!this.isFirstMessageSent) {
      this.sharedService.setFirstMessageSent(true);
      const assistant = localStorage.getItem('selectedAssistantName');
      const assistantName = assistant !== null && assistant !== undefined ? assistant : "ChatBot";
      this.chatService.createNewChat(firstWords, assistantName).subscribe({
        next: (response) => {
          console.log("Chat créé avec succès:", response);
          this.chatId = response.chat_id;
          if (this.chatId !== undefined) {
            localStorage.setItem('chatId', this.chatId.toString());
          }
          this.scrollToBottom();
          this.sendToBackend(userMessage);
        },
        error: (error) => {
          console.error('Erreur lors de la création du chat:', error);
          const updatedMessages = [...this.messages, { text: 'Erreur lors de la création du chat.', isUser: false }];
          this.sharedService.setMessages(updatedMessages);
          this.scrollToBottom();
        }
      });

    } else {
      this.sendToBackend(userMessage);
    }
  }

  sendToBackend(message: string) {
    if (this.chatId !== undefined) {
      const assistant = localStorage.getItem('selectedAssistantName') || 'chatBot';
      this.chatService.sendMessage(message, this.chatId, assistant).subscribe({
        next: (response) => {
          const botReply = response.message;
          this.messages.push({ text: botReply, isUser: false });
          this.scrollToBottom();
        },
        error: (error) => {
          console.error('Erreur lors de l\'appel API :', error);
          this.messages.push({ text: 'Erreur lors de la communication avec le serveur.', isUser: false });
          this.scrollToBottom();
        }
      });
    } else {
      console.error("chatId non défini. Impossible d'envoyer le message.");
    }
  }

  loadMessages(chatId: number) {
    if (!chatId) {
      console.error('Chat ID is missing');
      return;
    }
    this.chatService.get_chat_history(chatId).subscribe({
      next: (msgs) => {
        this.sharedService.setMessages(msgs);
        this.scrollToBottom();
      },

      error: (error) => {
        console.error('Erreur lors du chargement des messages :', error);
      }
    });
  }


  fermerAssistants() {
    this.fermerAssistantsEvent.emit();
  }

  ngOnChanges() {
    if (this.afficherAssistants) {
      this.chargerAssistants();
    }
  }

  chargerAssistants() {
    this.assistantService.get_assistants_for_current_user().subscribe({
      next: (response) => {
        this.assistants = response.map((assistant) => {
          let imagePath = '';

          switch (assistant.name) {
            case 'VisionData':
              imagePath = 'assets/images/img1.png';
              break;
            case 'TourBot':
              imagePath = 'assets/images/img2.png';
              break;
            case 'MailBot':
              imagePath = 'assets/images/img3.png';
              break;
            default:
              imagePath = 'assets/images/default.png';
          }

          return {
            image: imagePath,
            nom: assistant.name,
            assistantId: assistant.assistantId
          };
        });
      },
      error: (err) => {
        console.error('Erreur lors de la récupération des assistants:', err);
      }
    });
  }


  ajouterAssistant(assistant: any) {
    this.assistantAjouteEvent.emit(assistant);
  }


}
