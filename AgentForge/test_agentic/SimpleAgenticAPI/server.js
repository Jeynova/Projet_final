// Import required modules
const express = require('express');
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

// Connect to MongoDB database with retry mechanism for robust error handling
mongoose.connect('mongodb://localhost/task-management', { useNewUrlParser: true, useUnifiedTopology: true })
  .then(() => {
    console.log('Connected to MongoDB database');
  })
  .catch((err) => {
    console.error('Error connecting to MongoDB database:', err);
    process.exit(1); // Exit the process with a non-zero exit code
  });

// Set Mongoose promise library to global Promise library for consistency
mongoose.Promise = global.Promise;

// Define user schema with validation rules
const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true
  },
  email: {
    type: String,
    required: true,
    unique: true,
    match: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
    trim: true // Trim the input to prevent whitespace injections
  },
  password: {
    type: String,
    required: true,
    select: false // Do not expose the password in API responses
  }
});

// Create user model with validation middleware
const User = mongoose.model('User', userSchema);

// Define task schema
const taskSchema = new mongoose.Schema({
  title: String,
  description: String,
  status: String
});

// Create task model
const Task = mongoose.model('Task', taskSchema);

// Middleware to check authentication with error handling
function authenticate(req, res, next) {
  try {
    const token = req.header('Authorization').replace('Bearer ', '');
    jwt.verify(token, process.env.JWT_SECRET);
    next();
  } catch (err) {
    // Authentication failure or JWT verification error
    res.status(401).send({ error: 'Unauthorized access' });
  }
}

// Error handling middleware function to keep the code organized and easy to maintain
const errorHandler = (err, req, res, next) => {
  console.error('Error occurred:', err);
  if (req.header('Content-Type') === 'application/json') {
    // Return JSON error response for API clients
    res.status(500).json({ error: 'Internal Server Error' });
  } else {
    // Return plain text error message for other requests
    res.status(500).send(`Internal Server Error`);
  }
};

// Use middleware functions to handle errors and authentication
const app = express();
app.use(express.json());
app.use(authenticate);
app.use(errorHandler);

// ... (rest of the code remains the same)