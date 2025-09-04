import Joi from 'joi';
const validateBody = (schema) => {
  return async (req, res, next) => {
    const { error } = schema.validate(req.body);
    if (error) {
      return res.status(400).json({
        message: 'Validation failed',
        errors: error.details.map((err) => err.message)
      });
    }
    next();
  };
};
export { validateBody };