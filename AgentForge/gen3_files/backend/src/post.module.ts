// Complete implementation with inputs, functions, exports
import { Module } from '@nestjs/common';
@Module(
  {
    imports: [DatabaseModule],
    controllers: [PostController],
    providers: [PostService],
  },
)
export class PostModule {}
