import os
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-secret')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'postgresql://postgres:admin123@localhost:2005/postgres')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
