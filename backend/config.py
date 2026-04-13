import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DB_USER = os.getenv('DB_USER', 'cybersentinel')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'PG@dmin89')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'cybersentinel')
    
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Secret Key
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'b4b81342c636cf864982161fab1ba82eb9edabab7d7d624dc4c93b7b1d8f87ab18b3da0a3a22bd04444f4a17e794764c7bc8ebdb328c3a7ec9f9b6ee7dee11c8')
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 60 * 60  # 24 hours
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', '5c84cdbde12079832ca47a60126f7f47386606ade32a5a6971811666fc2ddaeb819502ac19967c71')