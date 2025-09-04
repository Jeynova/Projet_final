import { Model } from 'objection';
import bcrypt from 'bcryptjs';
const saltRounds = parseInt(process.env.SALT_ROUNDS);
Model.extend({
  tableName: 'tasks',
  id: 'id',
  hasTimestamps: true,
  fields: {
    title: { type: 'text' },
    description: { type: 'text' },
    priority: { type: 'integer' },
    dueDate: { type: 'date' },
    userId: { type: 'uuid' }
  }
});
export default Model;
