/**
 * Middleware for authentication
 *
 * @module auth
 */

const express = require('express');
const jwt = require('jsonwebtoken');
const dotenv = require('dotenv');

// Load environment variables from .env file
dotenv.config();

// Define secret key for JWT
const SECRET_KEY = process.env.SECRET_KEY;

/**
 * Authenticate user using JWT
 *
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Next middleware function in the stack
 */
function authenticate(req, res, next) {
  // Check if authentication token is present in header or query string
  const authHeader = req.header('Authorization');
  const token = authHeader ? authHeader.split(' ')[1] : null;

  if (!token) return res.status(401).send({ error: 'Unauthorized' });

  try {
    // Verify JWT signature
    jwt.verify(token, SECRET_KEY);
  } catch (error) {
    return res.status(403).send({ error: 'Invalid token' });
  }

  // If authentication is successful, proceed to next middleware function
  next();
}

/**
 * Generate JWT for user login
 *
 * @param {Object} user - User object with id and username
 */
function generateToken(user) {
  const payload = {
    sub: user._id,
    username: user.username,
  };

  return jwt.sign(payload, SECRET_KEY);
}

// Export authentication middleware functions
module.exports = {
  authenticate,
  generateToken,
};