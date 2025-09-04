const express = require('express');
const router = express.Router();
const passport = require('passport');
const bcrypt = require('bcryptjs');
const User = require('../models/User');

/**
 * @desc Login Route for Authentication
 * @route POST /login
 */
router.post('/login', (req, res) => {
  const { username, password } = req.body;
  
  if (!username || !password) {
    return res.status(400).json({ success: false, message: 'Please provide both username and password' });
  }
  
  passport.authenticate('local', (err, user, info) => {
    if (err) {
      console.error(err);
      return res.status(500).json({ success: false, message: 'Internal Server Error' });
    }
    
    if (!user) {
      return res.status(401).json({ success: false, message: info.message });
    }
    
    req.login(user, (err) => {
      if (err) {
        console.error(err);
        return res.status(500).json({ success: false, message: 'Internal Server Error' });
      }
      
      res.json({ success: true, user: user._id });
    });
  })(req, res);
});

/**
 * @desc Register Route for User Creation
 * @route POST /register
 */
router.post('/register', (req, res) => {
  const { username, email, password } = req.body;
  
  if (!username || !email || !password) {
    return res.status(400).json({ success: false, message: 'Please provide both username, email and password' });
  }
  
  User.findOne({ username }, (err, user) => {
    if (err) {
      console.error(err);
      return res.status(500).json({ success: false, message: 'Internal Server Error' });
    }
    
    if (user) {
      return res.status(400).json({ success: false, message: 'Username already taken' });
    }
    
    const newUser = new User({
      username,
      email,
      password: bcrypt.hashSync(password, 10),
    });
    
    newUser.save((err, user) => {
      if (err) {
        console.error(err);
        return res.status(500).json({ success: false, message: 'Internal Server Error' });
      }
      
      res.json({ success: true, user: user._id });
    });
  });
});

/**
 * @desc Logout Route for User De-Authentication
 * @route GET /logout
 */
router.get('/logout', (req, res) => {
  req.logout();
  
  res.redirect('/');
});

module.exports = router;