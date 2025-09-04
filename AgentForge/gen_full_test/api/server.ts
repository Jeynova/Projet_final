import express from 'express';
const app = express();
app.use('/auth', require('./auth'));
app.use('/tasks', require('./tasks'));
app.use('/categories', require('./categories'));
app.use('/users', require('./users'));
export default app;