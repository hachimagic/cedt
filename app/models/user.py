import csv
import os
from pathlib import Path
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.username = kwargs.get('username')
        self.email = kwargs.get('email')
        self.password_hash = kwargs.get('password_hash')
        self.created_at = kwargs.get('created_at', datetime.now().isoformat())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_user_csv_path():
        """Get the path to the users CSV file"""
        Path('user_data').mkdir(exist_ok=True)
        return Path('user_data/users.csv')

    @staticmethod
    def get_all_users():
        """Read all users from CSV"""
        file_path = User.get_user_csv_path()
        if not file_path.exists():
            return []
        
        users = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append(User(**row))
        return users

    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        users = User.get_all_users()
        return next((u for u in users if u.id == user_id), None)

    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        users = User.get_all_users()
        return next((u for u in users if u.username == username), None)

    @staticmethod
    def create_user(username, email, password):
        """Create a new user"""
        users = User.get_all_users()
        user_id = str(len(users) + 1)
        
        user = User(
            id=user_id,
            username=username,
            email=email
        )
        user.set_password(password)
        
        # Add new user to CSV
        with open(User.get_user_csv_path(), 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'username', 'email', 'password_hash', 'created_at'])
            if not f.tell():  # If file is empty, write header
                writer.writeheader()
            writer.writerow(user.__dict__)
        
        return user
