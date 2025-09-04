// Complete implementation with imports, functions, exports
import { User } from '../models/User';
import { Request, Response } from 'express';

class UserService {
	constructor(private userRepository: UserRepository) {}

	async register(request: Request, response: Response): Promise<void> {
		const { name, email, password } = request.body;

		const existingUser = await this.userRepository.findOne({ email });

		if (existingUser) {
			request.flash('error', 'A user with that email already exists');
			response.redirect('/users/register');
		} else {
			const user = new User(name, email, password);

			try {
				await this.userRepository.save(user);
				response.redirect('/users/login');
			} catch (error) {
				request.flash('error', 'Failed to create user');
				response.redirect('/users/register');
			}
		}
	}
}