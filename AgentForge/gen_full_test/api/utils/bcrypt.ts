import bcrypt from 'bcryptjs';
const saltRounds = parseInt(process.env.SALT_ROUNDS);
const hashPassword = (password) => {
  return bcrypt.hashSync(password, saltRounds);
};
export { hashPassword };