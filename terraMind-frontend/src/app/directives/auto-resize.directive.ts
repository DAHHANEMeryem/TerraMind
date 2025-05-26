import { Directive, ElementRef, HostListener } from '@angular/core';

@Directive({
  selector: '[appAutoResize]'
})
export class AutoResizeDirective {

  private readonly maxHeight = 250;

  constructor(private el: ElementRef) {}

  @HostListener('input') onInput() {
    const textarea = this.el.nativeElement;
    textarea.style.height = 'auto'; 
    const newHeight = textarea.scrollHeight;

    if (newHeight > this.maxHeight) {
      textarea.style.height = this.maxHeight + 'px';
      textarea.style.overflowY = 'auto'; 
    } else {
      textarea.style.height = newHeight + 'px';
      textarea.style.overflowY = 'hidden'; 
    }
  }

}
