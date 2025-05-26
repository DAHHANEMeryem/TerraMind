import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatService {

  constructor(private http: HttpClient) { }
    private baseUrl = 'http://localhost:5000/chat';

  createNewChat(firstMessage: string, assistant: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/new_chat`, { first_message: firstMessage, assistant: assistant });
  }

  sendMessage(message: string, chatId: number, assistant: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/`, { message, chat_id: chatId, assistant: assistant });
  }

  get_chat_history(chatId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/${chatId}`);
  }





}
