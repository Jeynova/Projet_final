import { Model, DataTypes } from 'sequelize';

export default class Report extends Model {
  public id!: number;
  public name!: string;
  public description!: string;
  public userId!: number;
  public createdAt!: Date;
  public updatedAt!: Date;
}
