// Complete implementation with inputs, functions, exports
import { Module } from '@nest.comon';
@Module(
  {
    imports: [DatabaseModule],
    controllers: [TagController],
    providers: [TagService],
  },
)
export class TagModule {}
