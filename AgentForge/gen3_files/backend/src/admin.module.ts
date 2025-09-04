// Complete implementation with inputs, functions, exports
import { Module } from '@nestjs/common';
@Module(
  {
    imports: [DatabaseModule],
    controllers: [AdminController],
    providers: [AdminService],
  },
)
export class AdminModule {}
