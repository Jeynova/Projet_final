const express = require('express');
const router = express.Router();
const User = require('../models/User');
const Task = require('../models/Task');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

// Generate a new JWT token for the user when logging in
function generateToken(user) {
  const token = jwt.sign({ userId: user._id }, process.env.SECRET_KEY, { expiresIn: '1h' });
  return token;
}

// Verify if the provided token is valid and matches the user's ID
function verifyToken(req, res, next) {
  const token = req.headers['x-access-token'] || req.headers['authorization'];
  if (!token) return res.status(403).send({ auth: false, message: 'No token provided.' });
  jwt.verify(token, process.env.SECRET_KEY, (err, decoded) => {
    if (err) return res.status(500).send({ auth: false, message: 'Failed to authenticate token.' });
    req.userId = decoded.userId;
    next();
  });
}

// GET all tasks
router.get('/', verifyToken, async (req, res) => {
  try {
    const tasks = await Task.find({ user: req.userId }).populate('user');
    res.json(tasks);
  } catch (err) {
    console.error(err.message);
    res.status(500).send({ message: 'Error getting tasks' });
  }
});

// GET a specific task by ID
router.get('/:id', verifyToken, async (req, res) => {
  try {
    const id = req.params.id;
    const task = await Task.findById(id).populate('user');
    if (!task || task.user.toString() !== req.userId) {
      return res.status(404).send({ message: 'Task not found' });
    }
    res.json(task);
  } catch (err) {
    console.error(err.message);
    res.status(500).send({ message: 'Error getting task' });
  }
});

// POST a new task
router.post('/', verifyToken, async (req, res) => {
  try {
    const task = new Task(req.body);
    task.user = req.userId;
    await task.save();
    res.json(task);
  } catch (err) {
    console.error(err.message);
    res.status(500).send({ message: 'Error creating task' });
  }
});

// PUT an existing task
router.put('/:id', verifyToken, async (req, res) => {
  try {
    const id = req.params.id;
    const task = await Task.findById(id);
    if (!task || task.user.toString() !== req.userId) {
      return res.status(404).send({ message: 'Task not found' });
    }
    await Task.updateOne({ _id: id }, { $set: req.body });
    res.json(await Task.findById(id));
  } catch (err) {
    console.error(err.message);
    res.status(500).send({ message: 'Error updating task' });
  }
});

// DELETE a specific task by ID
router.delete('/:id', verifyToken, async (req, res) => {
  try {
    const id = req.params.id;
    await Task.findByIdAndDelete(id);
    if (!await Task.exists({ _id: id })) {
      return res.status(204).send();
    }
    res.status(500).send({ message: 'Error deleting task' });
  } catch (err) {
    console.error(err.message);
    res.status(500).send({ message: 'Error deleting task' });
  }
});

module.exports = router;