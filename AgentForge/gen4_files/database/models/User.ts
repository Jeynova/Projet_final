import { Model, DataTypes } from 'sequelize';

export default class User extends Model {
  public id!: number;
  public email!: string;
  public password!: string;
  public createdAt!: Date;
  public updatedAt!: Date;
}
