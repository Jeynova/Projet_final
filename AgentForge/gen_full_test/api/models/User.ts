import { Model } from 'objection';
import bcrypt from 'bcryptjs';
const saltRounds = parseInt(process.env.SALT_ROUNDS);
Model.extend({
  tableName: 'users',
  id: 'id',
  hasTimestamps: true,
  fields: {
    email: { type: 'text' },
    password: { type: 'text' }
  },
  async authenticate(password) {
    return bcrypt.compare(password, this.password);
  }
});
export default Model;
