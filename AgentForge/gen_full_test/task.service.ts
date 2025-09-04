// Complete implementation with imports, functions, exports
import { Task } from '../models/task';
import { Injectable } from '@nestjs/common';
@Injectable()
export class TaskService {
  private tasks: Task[] = [];

  create(title: string): Task {
    const task = new Task();
    task.title = title;
    this.tasks.push(task);
    return task;
  }

  findAll(): Task[] {
    return this.tasks;
  }
}
