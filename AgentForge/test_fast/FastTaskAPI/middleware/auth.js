// middleware/auth.js
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const User = require('../models/User');

/**
 * Authenticate user using JWT token
 *
 * @param {Object} req - Express request object
 * @returns {Object|Error} - Authenticated user data or error
 */
async function authenticate(req, res, next) {
  const token = req.header('Authorization');
  if (!token) return res.status(401).send({ message: 'Unauthorized' });

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    // Check if user still exists in the database
    const user = await User.findById(decoded.id);
    if (!user) return res.status(401).send({ message: 'Invalid token' });
    req.user = user;
    next();
  } catch (error) {
    return res.status(500).send({ message: 'Internal Server Error', error });
  }
}

/**
 * Validate user credentials
 *
 * @param {Object} req - Express request object
 * @returns {Object|Error} - Validated user data or error
 */
async function validateUser(req, res, next) {
  const { email, password } = req.body;
  if (!email || !password) return res.status(400).send({ message: 'Invalid credentials' });

  try {
    // Find user by email and compare passwords
    const user = await User.findOne({ email });
    if (!user) return res.status(401).send({ message: 'Invalid credentials' });
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.status(401).send({ message: 'Invalid credentials' });

    // If user and password match, generate JWT token
    const token = jwt.sign(
      { id: user._id },
      process.env.JWT_SECRET,
      {
        expiresIn: 86400, // Token expires after 24 hours
      }
    );
    res.status(200).send({ message: 'Login successful', token });
  } catch (error) {
    return res.status(500).send({ message: 'Internal Server Error', error });
  }
}

module.exports = { authenticate, validateUser };