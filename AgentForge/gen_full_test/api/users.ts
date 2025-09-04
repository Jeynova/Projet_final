import express from 'express';
const userRouter = express.Router();
// Create new user endpoint
userRouter.post('/register', async (req, res) => {
  const { email, password } = req.body;
  // Check if user already exists
  if (await User.findOne({ where: { email } })) {
    return res.status(409).json({
      message: 'User already exists'
    });
  }
  // Create new user
  const newUser = await User.create({ email, password });
  res.json(newUser);
});
// Login endpoint
userRouter.post('/login', async (req, res) => {
  const { email, password } = req.body;
  // Check if user exists
  const user = await User.findOne({ where: { email } });
  if (!user) {
    return res.status(401).json({
      message: 'Invalid credentials'
    });
  }
  // Compare passwords
  if (await bcrypt.compare(password, user.password)) {
    const token = createJWTToken({ id: user.id, email: user.email });
    res.json({ token });
  } else {
    return res.status(401).json({
      message: 'Invalid credentials'
    });
  }
});
// Export user router
export default userRouter;