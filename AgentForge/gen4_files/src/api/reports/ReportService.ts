// Another complete file
import { Report } from '../models/Report';
import { Request, Response } from 'express';

class ReportService {
	constructor(private reportRepository: ReportRepository) {}

	async getReports(request: Request, response: Response): Promise<void> {
		const reports = await this.reportRepository.find();

		response.json(reports);
	}
}