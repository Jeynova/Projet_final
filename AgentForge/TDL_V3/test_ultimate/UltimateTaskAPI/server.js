// server.js
const express = require('express');
const cors = require('cors');
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.get('/api/health', (req, res) => {
  res.json({ message: 'API is running', timestamp: new Date() });
});

app.get('/api/tasks', (req, res) => {
  res.json({ tasks: [], message: 'Tasks endpoint' });
});

app.post('/api/tasks', (req, res) => {
  const task = req.body;
  res.json({ message: 'Task created', task });
});

app.get('/api/users', (req, res) => {
  res.json({ users: [], message: 'Users endpoint' });
});

app.post('/api/auth/login', (req, res) => {
  const { email, password } = req.body;
  res.json({ message: 'Login endpoint', token: 'jwt_token_here' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;
