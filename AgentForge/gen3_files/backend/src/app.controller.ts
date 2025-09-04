// Complete implementation with imports, functions, exports
import { Controller, Get } from '@nestjs/common';
@Get('')
export class AppController {
  constructor(private readonly appService: AppService) {}
}
