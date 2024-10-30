#!/bin/bash
set -e

# Run database migrations
python << END
from app import app, db
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")
END

# Start Gunicorn
exec gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 app:app