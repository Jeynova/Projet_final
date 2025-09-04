// Import required modules
const express = require('express');
const bodyParser = require('body-parser');
const mongoose = require('mongoose');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

// Connect to MongoDB
mongoose.connect('mongodb://localhost/task-api', { useNewUrlParser: true, useUnifiedTopology: true });

// Define Mongoose schema for Task model
const taskSchema = new mongoose.Schema({
  title: String,
  description: String,
  completed: Boolean,
});

const User = require('./models/User');
const Task = mongoose.model('Task', taskSchema);

// Create Express app instance
const app = express();

// Set up middlewares
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Define authentication middleware
function authenticateToken(req, res, next) {
  const token = req.header('Authorization');
  if (!token) return res.status(401).send({ error: 'Unauthorized' });
  
  try {
    const decoded = jwt.verify(token, process.env.SECRET_KEY);
    req.user = decoded;
    next();
  } catch (ex) {
    res.status(400).send({ error: 'Invalid token' });
  }
}

// Define API routes
app.post('/users', async (req, res) => {
  try {
    const user = new User({
      name: req.body.name,
      email: req.body.email,
      password: bcrypt.hashSync(req.body.password),
    });
    
    await user.save();
    const token = jwt.sign({ _id: user._id }, process.env.SECRET_KEY);
    res.send({ token, userId: user._id });
  } catch (ex) {
    console.error(ex);
    res.status(400).send({ error: 'Failed to create user' });
  }
});

app.get('/tasks', authenticateToken, async (req, res) => {
  try {
    const tasks = await Task.find({ userId: req.user._id }).exec();
    res.send(tasks);
  } catch (ex) {
    console.error(ex);
    res.status(500).send({ error: 'Failed to retrieve tasks' });
  }
});

app.post('/tasks', authenticateToken, async (req, res) => {
  try {
    const task = new Task({
      title: req.body.title,
      description: req.body.description,
      completed: false,
      userId: req.user._id,
    });
    
    await task.save();
    res.send(task);
  } catch (ex) {
    console.error(ex);
    res.status(400).send({ error: 'Failed to create task' });
  }
});

app.put('/tasks/:id', authenticateToken, async (req, res) => {
  try {
    const id = req.params.id;
    const task = await Task.findByIdAndUpdate(id, { $set: req.body }, { new: true }).exec();
    
    if (!task) return res.status(404).send({ error: 'Task not found' });
    res.send(task);
  } catch (ex) {
    console.error(ex);
    res.status(500).send({ error: 'Failed to update task' });
  }
});

app.delete('/tasks/:id', authenticateToken, async (req, res) => {
  try {
    const id = req.params.id;
    await Task.findByIdAndDelete(id).exec();
    
    if (!await User.findById(req.user._id).select('tasks').exec()) 
      return res.status(404).send({ error: 'Task not found' });
    res.send({ message: 'Task deleted successfully' });
  } catch (ex) {
    console.error(ex);
    res.status(500).send({ error: 'Failed to delete task' });
  }
});

// Start server
const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server started on port ${port}`));