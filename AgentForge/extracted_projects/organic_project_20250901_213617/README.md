# Data Analytics API

## Setup
1. Clone the repository:
   ```sh
git clone https://github.com/yourusername/data-analytics-api.git
cd data-analytics-api
```
2. Create a virtual environment and activate it:
   ```sh
pip install -r requirements.txt
docker-compose up --build
```
3. Run migrations:
   ```sh
./backend/manage.py migrate
```