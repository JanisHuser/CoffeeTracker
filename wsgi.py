from app import app, db

def init_db():
    with app.app_context():
        db.create_all()
        print("Database initialized.")

init_db()

if __name__ == "__main__":
    app.run()