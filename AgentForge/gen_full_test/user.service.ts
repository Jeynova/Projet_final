// Complete implementation with imports, functions, exports
import { User } from '../models/user';
import { Injectable } from '@nestjs/common';
@Injectable()
export class UserService {
  private users: User[] = [];

  create(email: string): User {
    const user = new User();
    user.email = email;
    this.users.push(user);
    return user;
  }

  findAll(): User[] {
    return this.users;
  }
}
