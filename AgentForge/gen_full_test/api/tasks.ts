import express from 'express';
const taskRouter = express.Router();
// Create new task endpoint
taskRouter.post('/create', async (req, res) => {
  const { title, description, priority, dueDate } = req.body;
  // Check if user is authenticated
  if (!req.user) {
    return res.status(401).json({
      message: 'Must be authenticated to create tasks'
    });
  }
  // Create new task
  const newTask = await Task.create({ title, description, priority, dueDate, userId: req.user.id });
  res.json(newTask);
});
// Read all tasks endpoint
taskRouter.get('/', async (req, res) => {
  const tasks = await Task.findAll({ where: { userId: req.user.id } });
  res.json(tasks);
});
// Update task endpoint
taskRouter.put('/update/:taskId', async (req, res) => {
  const { taskId } = req.params;
  // Check if task exists
  const task = await Task.findOne({ where: { id: taskId, userId: req.user.id } });
  if (!task) {
    return res.status(404).json({
      message: 'Task not found'
    });
  }
  // Update task
  const updatedTask = await Task.update(req.body, { where: { id: taskId } });
  res.json(updatedTask);
});
// Delete task endpoint
taskRouter.delete('/delete/:taskId', async (req, res) => {
  const { taskId } = req.params;
  // Check if task exists
  const task = await Task.findOne({ where: { id: taskId, userId: req.user.id } });
  if (!task) {
    return res.status(404).json({
      message: 'Task not found'
    });
  }
  // Delete task
  await Task.destroy({ where: { id: taskId } });
  res.json({ success: true });
});
// Export task router
export default taskRouter;