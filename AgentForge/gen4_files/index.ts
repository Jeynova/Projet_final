// Complete implementation with imports, functions, exports
import express from 'express';
const port = process.env.PORT || 3000;
const app = express();

// Define routes
app.use('/users', usersRouter);
app.use('/items', itemsRouter);
app.use('/reports', reportsRouter);
export default app;