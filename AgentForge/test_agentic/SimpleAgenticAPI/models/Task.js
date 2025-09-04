// models/Task.js

const mongoose = require('mongoose');
const Schema = mongoose.Schema;

/**
 * Task model definition.
 *
 * @author [Your Name]
 */
const taskSchema = new Schema({
  title: {
    type: String,
    required: true,
    trim: true,
  },
  description: {
    type: String,
    required: false,
  },
  completed: {
    type: Boolean,
    default: false,
  },
  userId: {
    type: Schema.Types.ObjectId,
    ref: 'User',
    required: true,
  },
}, {
  timestamps: true,
});

taskSchema.index({ userId: 1 }, { unique: true });

// Pre-save hook to validate task completion status
taskSchema.pre('save', function(next) {
  const task = this;

  // Ensure that completed is a boolean value
  if (typeof task.completed !== 'boolean') {
    task.completed = false;
  }

  next();
});

const Task = mongoose.model('Task', taskSchema);

module.exports = Task;