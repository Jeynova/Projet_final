import { JWT } from 'express-jsonwebtoken';
const jwt = new JWT();
const createJWTToken = (payload) => {
  return jwt.sign(payload, process.env.SECRET_KEY);
};
export { createJWTToken };