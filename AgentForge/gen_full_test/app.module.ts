// Complete implementation with imports, functions, exports
import { Module } from '@nestjs/common';
import { UserModule } from './user/user.module';
import { TaskModule } from './task/task.module';
@Module({ imports: [UserModule, TaskModule], controllers: [], providers: [] }) export class AppModule { }
