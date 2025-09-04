// Complete implementation with inputs, functions, exports
import { Controller, Get } from '@nestjs/common';
@Get('posts')
export class PostController {
  constructor(private readonly postService: PostService) {}
}
