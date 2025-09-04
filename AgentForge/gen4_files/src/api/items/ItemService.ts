// Another complete file
import { Item } from '../models/Item';
import { Request, Response } from 'express';

class ItemService {
	constructor(private itemRepository: ItemRepository) {}

	async getItems(request: Request, response: Response): Promise<void> {
		const items = await this.itemRepository.find();

		response.json(items);
	}
}