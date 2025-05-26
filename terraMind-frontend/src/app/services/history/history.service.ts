import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class HistoryService {

  constructor(private http: HttpClient) { }
  private baseUrl = 'http://localhost:5000/history';



  deleteSession(sessionId: number) {
    console.log('Suppression de la session avec ID:', sessionId);  
    return this.http.delete<any>(`${this.baseUrl}/delete/${sessionId}`);
  }

  updateTitleSession(sessionId: number, newTitle: string) {
    return this.http.put<any>(`${this.baseUrl}/update/${sessionId}`, { title: newTitle });
  }

  getChatSessions(assistant: string) {
    return this.http.get<any[]>(`${this.baseUrl}/${assistant}`);
  }

  get_all_chat_sessions(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/`);
  }

  getChatDetails(userId: string, sessionId: string): Observable<any[]> {
    const params = new HttpParams()
      .set('user_id', userId)
      .set('session_id', sessionId);

    return this.http.get<any[]>(`${this.baseUrl}/details`, { params });
  }
}
