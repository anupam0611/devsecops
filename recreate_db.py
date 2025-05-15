from app import create_app, db
from models import User

# Create the Flask app
app = create_app()

# Recreate the database
with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    print("Creating all tables...")
    db.create_all()
    print("Database created successfully!")

    # Add seed data
    admin_user = User(username="admin", email="admin@example.com", is_admin=True)
    db.session.add(admin_user)
    db.session.commit()

    print("Database recreated and seed data added successfully!")