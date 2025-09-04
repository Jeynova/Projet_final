# Task Management Application
This is a task management application built using Node.js and Express.js for the backend, React.js for the frontend, and PostgreSQL for the database.

## Setup Instructions
To set up the application, follow these steps:
1. Clone this repository to your local machine using `git clone`.
2. Install all dependencies by running `npm install` in both the backend and frontend directories.
3. Create a `.env` file in the root directory of the backend and frontend with the following variables:
* `NODE_ENV=development` for both directories
* `DATABASE_URL=postgres://admin:password@localhost/tasksdb`
4. Start the database using `docker-compose up -d db`.
5. Start the backend and frontend servers using `npm run start` in both directories.
6. Access the application by navigating to `http://localhost:8080/` in your web browser.