# Metreecs Backend

## Setup

```bash
# 1. PostgreSQL
sudo apt install postgresql -y
sudo systemctl start postgresql
sudo -u postgres psql -c "CREATE DATABASE metreecs_db;"
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'your_password_here';"

# 2. Virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure database
cp database/.env.example database/.env  # Edit with your credentials

# 4. Initialize tables & seed data
python src/setup.py

# 5. Run server
cd src && uvicorn app:app --reload
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/movements` | Create movement (header: `idempotency-key`) |
| GET | `/products/{id}/stock` | Get stock (supports ETag/304) |
| GET | `/health` | Health check |
