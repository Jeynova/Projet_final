// Complete implementation with imports, functions, exports
import { Task } from '../models/task';
import { Controller, Get, Post, Body } from '@nestjs/common';
import { TaskService } from './task.service';
@Controller('tasks')
export class TaskController {
  constructor(private taskService: TaskService) { }

  @Post()
  async create(@Body() task: Task): Promise<Task> {
    return await this.taskService.create(task);
  }

  @Get()
  async findAll(): Promise<Task[]> {
    return await this.taskService.findAll();
  }
}
