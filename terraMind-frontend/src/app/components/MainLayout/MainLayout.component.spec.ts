import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InterfacePrincipaleComponent } from './interface-principale.component';

describe('InterfacePrincipaleComponent', () => {
  let component: InterfacePrincipaleComponent;
  let fixture: ComponentFixture<InterfacePrincipaleComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [InterfacePrincipaleComponent]
    });
    fixture = TestBed.createComponent(InterfacePrincipaleComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
