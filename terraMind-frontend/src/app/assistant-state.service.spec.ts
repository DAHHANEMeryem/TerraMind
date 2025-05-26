import { TestBed } from '@angular/core/testing';

import { AssistantStateService } from './assistant-state.service';

describe('AssistantStateService', () => {
  let service: AssistantStateService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AssistantStateService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
