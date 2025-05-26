import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
@Injectable({
  providedIn: 'root'
})
export class AssistantService {

  constructor(private http: HttpClient) { }

    get_all_assistants(): Observable<any[]> {
    return this.http.get<any[]>(`http://localhost:5000/assistant`);
  }

  updateUserAssistants(userId: string, assistantsIds: number[]) {
  return this.http.put(`http://localhost:5000/assistant/${userId}`, { assistants: assistantsIds });
}

getUserAssistants(userId: string): Observable<number[]> {
  return this.http.get<number[]>(`http://localhost:5000/assistant/user/${userId}`);
}


get_assistants_for_current_user(): Observable<any[]> {
  return this.http.get<any[]>(`http://localhost:5000/assistant/user`);
}














}
