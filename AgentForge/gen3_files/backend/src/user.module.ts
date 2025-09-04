// Complete implementation with inputs, functions, exports
import { Module } from '@nestjs/common';
@Module(
  {
    imports: [DatabaseModule],
    controllers: [UserController],
    providers: [UserService],
  },
)
export class UserModule {}
