// routes/auth.js

/**
 * @file Auth routes for task API
 */

const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');
const userController = require('../controllers/userController');

// Importing validation middleware to handle errors in a centralized way
const { validateCreateUser, validateLogin } = require('../middleware/validationMiddleware');

/**
 * POST /register - Register a new user
 */
router.post('/register', [
  validateCreateUser,
  authController.createUser
], (req, res) => {
  res.status(201).json({ message: 'User created successfully' });
});

/**
 * POST /login - Login an existing user
 */
router.post('/login', [
  validateLogin,
  authController.loginUser
], (req, res) => {
  res.json(req.user);
});

/**
 * GET /logout - Logout the current user
 */
router.get('/logout', authController.logoutUser);

// Error handling for all routes in this file
router.use((err, req, res, next) => {
  const error = new Error('Internal Server Error');
  error.status = err.status || 500;
  res.status(error.status).json({ message: error.message });
});

module.exports = router;
