Improved Dockerfile with correct implementation of multi-stage builds and dependency management:

FROM node:14-alpine AS build-stage
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . /
RUN npm run build
FROM nginx:alpine
WORKDIR /usr/share/nginx/html
COPY --from=build-stage /app/build/