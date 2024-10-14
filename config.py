import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'supersecretkey'
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL') or 'postgresql://mealmaster_user:password@db/mealmaster_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
