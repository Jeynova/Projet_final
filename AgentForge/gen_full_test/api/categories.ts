import express from 'express';
const categoryRouter = express.Router();
// Create new category endpoint
cateogryRouter.post('/create', async (req, res) => {
  const { name } = req.body;
  // Check if user is authenticated
  if (!req.user) {
    return res.status(401).json({
      message: 'Must be authenticated to create categories'
    });
  }
  // Create new category
  const newCategory = await Category.create({ name, userId: req.user.id });
  res.json(newCategory);
});
// Read all categories endpoint
cateogryRouter.get('/', async (req, res) => {
  const categories = await Category.findAll({ where: { userId: req.user.id } });
  res.json(categories);
});
// Update category endpoint
cateogryRouter.put('/update/:categoryId', async (req, res) => {
  const { categoryId } = req.params;
  // Check if category exists
  const category = await Category.findOne({ where: { id: categoryId, userId: req.user.id } });
  if (!category) {
    return res.status(404).json({
      message: 'Category not found'
    });
  }
  // Update category
  const updatedCategory = await Category.update(req.body, { where: { id: categoryId } });
  res.json(updatedCategory);
});
// Delete category endpoint
cateogryRouter.delete('/delete/:categoryId', async (req, res) => {
  const { categoryId } = req.params;
  // Check if category exists
  const category = await Category.findOne({ where: { id: categoryId, userId: req.user.id } });
  if (!category) {
    return res.status(404).json({
      message: 'Category not found'
    });
  }
  // Delete category
  await Category.destroy({ where: { id: categoryId } });
  res.json({ success: true });
});
// Export category router
export default categoryRouter;