# PhotoShare

FastAPI application for photo uploads, Cloudinary transformations, QR codes and comments.

## Run locally

Prerequisites: Python 3.12+, Docker Compose, and Cloudinary and SMTP credentials.
Run these commands from the project root.

1. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   python -m pip install -r requirements.txt
   ```

2. Start PostgreSQL and Redis, then apply migrations once PostgreSQL is ready:

   ```bash
   docker compose up -d
   alembic upgrade head
   ```

3. Start the application:

   ```bash
   uvicorn main:app --reload
   ```

Open http://localhost:8000/docs to explore the API. Register, confirm your email,
then log in. The first registered user in an empty database becomes an administrator.

## Project documentation

```bash
python -m sphinx -W --keep-going -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` in your browser.
