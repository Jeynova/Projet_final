// models/Task.js
const mongoose = require('mongoose');
const Joi = require('joi');
const taskSchema = new mongoose.Schema({
  title: {
    type: String,
    required: true,
    trim: true,
    maxLength: 50
  },
  description: {
    type: String,
    trim: true,
    maxLength: 200
  },
  dueDate: {
    type: Date,
    validate: {
      validator: function(v) {
        return v instanceof Date && !isNaN(v);
      },
      message: 'Invalid date'
    }
  },
  status: {
    type: String,
    enum: ['pending', 'inProgress', 'completed'],
    default: 'pending'
  },
  assignedTo: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: false
  },
  createdOn: {
    type: Date,
    default: Date.now
  }
});

const Task = mongoose.model('Task', taskSchema);

// Validation Schema for Task Model
const taskValidationSchema = Joi.object({
  title: Joi.string().required(),
  description: Joi.string(),
  dueDate: Joi.date().iso(),
  status: Joi.string()
});

function validate(task) {
  return taskValidationSchema.validate(task);
}

module.exports = { Task, validate };

// Error handling middleware
const errorMiddleware = function(err, req, res, next) {
  console.error('Error occurred:', err);
  const errorResponse = {
    message: 'Internal Server Error',
    status: 500
  };
  res.status(500).send(errorResponse);
};

module.exports.errorMiddleware = errorMiddleware;