// Complete implementation with inputs, functions, exports
import { Module } from '@nestjs/common';
@Module(
  {
    imports: [DatabaseModule],
    controllers: [CommentController],
    providers: [CommentService],
  },
)
export class CommentModule {}
