// Import required packages
const mongoose = require('mongoose');
const bcrypt = require('bcrypt');

// Define the User schema
const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    trim: true
  },
  email: {
    type: String,
    required: true,
    unique: true,
    match: [/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/, 'Please fill a valid email address'],
    trim: true
  },
  password: {
    type: String,
    required: true,
    trim: true
  }
}, { timestamps: true });

// Hash the password before saving to MongoDB
userSchema.pre('save', async function(next) {
  const user = this;
  if (!user.isModified('password')) return next();
  try {
    user.password = await bcrypt.hash(user.password, 10);
    return next();
  } catch (err) {
    return next(err);
  }
});

// Define the User model
const User = mongoose.model('User', userSchema);

module.exports = User;