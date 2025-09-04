import { Model, DataTypes } from 'sequelize';

export default class Item extends Model {
  public id!: number;
  public name!: string;
  public description!: string;
  public dueDate!: Date;
  public priority!: string;
  public userId!: number;
  public createdAt!: Date;
  public updatedAt!: Date;
}
