import { Model } from 'objection';
const Category = {
  tableName: 'categories',
  id: 'id',
  hasTimestamps: true,
  fields: {
    name: { type: 'text' },
    userId: { type: 'uuid' }
  }
};
export default Category;
