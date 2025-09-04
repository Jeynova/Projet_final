// Import required modules
import { Document, Schema } from 'mongoose';
import bcrypt from 'bcryptjs';
import passport from 'passport';

/**
 * Category model definition
 */
const categorySchema = new Schema({
  name: {
    type: String,
    trim: true,
    required: [true, 'Category name is required'],
    minLength: [3, 'Minimum character length for category name is 3'],
    maxLength: [255, 'Maximum character length for category name is 255']
  },
  description: {
    type: String,
    trim: true
  },
  image: {
    type: String,
    trim: true
  },
  tasks: [{ type: Schema.Types.ObjectId, ref: 'Task' }]
}, {
  timestamps: true,
  versionKey: false
});

// Define custom methods for category model
categorySchema.methods.serialize = function () {
  return {
    id: this._id,
    name: this.name,
    description: this.description,
    image: this.image
  };
};

categorySchema.methods.deserialize = function (data) {
  const category = new Category(data);
  category.id = data.id;
  return category;
};

// Define validation rules for category model
const validateCategory = async (category) => {
  try {
    await Promise.all([
      validateName(category.name),
      validateDescription(category.description)
    ]);
  } catch (error) {
    throw new Error('Validation failed: ' + error.message);
  }
};

async function validateName(name) {
  if (!name || name.length < 3) {
    throw new Error('Category name is required and must be at least 3 characters long');
  }
}

async function validateDescription(description) {
  if (description && description.length > 255) {
    throw new Error('Description cannot exceed 255 characters');
  }
}

// Define pre-save hook for category model
categorySchema.pre('save', async function (next) {
  try {
    await validateCategory(this);
  } catch (error) {
    next(error);
  }
});

// Define middleware to hash password before saving user document
categorySchema.pre('save', async function (next) {
  if (this.isModified('name')) {
    this.name = bcrypt.hashSync(this.name, 10);
  }
  next();
});

// Export the Category model
export default categorySchema;