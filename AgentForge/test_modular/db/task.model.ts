// db/task.model.ts
import { Document } from 'mongoose';
import passport from 'passport';
import * as Yup from 'yup';
import { taskSchema } from './schema';
import { User } from '../user.model';

interface TaskModel extends Document {
  title: string;
  description: string;
  status: string;
  userId: string | number;
  categoryId?: string | number;
}

const schema = new taskSchema({
  title: {
    type: String,
    required: true,
    trim: true,
  },
  description: {
    type: String,
    required: false,
    trim: true,
  },
  status: {
    type: String,
    enum: ['pending', 'in-progress', 'completed'],
    default: 'pending',
  },
  userId: {
    type: String,
    ref: User.name,
    required: true,
  },
  categoryId: {
    type: String,
    ref: 'Category',
    default: null,
  },
});

schema.index({ title: 'text' });
schema.index({ description: 'text' });

const Task = mongoose.model<TaskModel>('Task', schema);

// Custom methods
Task.statics.findAllForUser = async function (userId: string | number) {
  const tasks = await this.find({ userId, status: { $ne: 'completed' } }).exec();
  return tasks;
};

Task.statics.findCompletedTasks = async function () {
  const completedTasks = await this.find({ status: 'completed' });
  return completedTasks;
};

// Validation rules
const taskValidationSchema = Yup.object().shape({
  title: Yup.string().required(),
});

interface ValidateTaskInput {
  title: string;
}

async function validateTask(input: ValidateTaskInput) {
  try {
    await taskValidationSchema.validateAsync(input);
  } catch (error) {
    if (error instanceof Yup.ValidationError) {
      throw new Error(`Invalid input for Task: ${error.message}`);
    }
  }
}

// Serialization/deserialization logic
interface SerializedTask extends Document {
  id: string;
  title: string;
  description: string;
  status: string;
  userId: string | number;
  categoryId?: string | number;
}

const serializeTask = (task: Task) => ({
  id: task._id.toString(),
  title: task.title,
  description: task.description,
  status: task.status,
  userId: task.userId,
  categoryId: task.categoryId,
});

interface DeserializeTask {
  _id: string;
  title: string;
  description: string;
  status: string;
  userId: string | number;
  categoryId?: string | number;
}

const deserializeTask = (task: DeserializeTask) => ({
  id: new mongoose.Types.ObjectId(task._id),
  title: task.title,
  description: task.description,
  status: task.status,
  userId: task.userId,
  categoryId: task.categoryId,
});

export { Task, schema, validateTask, serializeTask, deserializeTask };