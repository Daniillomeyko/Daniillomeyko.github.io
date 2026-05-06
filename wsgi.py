from app import app, init_db


# Ensure DB tables exist when service starts.
init_db()

