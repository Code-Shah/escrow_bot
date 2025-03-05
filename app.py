import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import declarative_base
from sqlalchemy import exc
import time
from logger import logger
from dotenv import load_dotenv  # Add this line

# Load environment variables from .env file
load_dotenv()  # Add this line

Base = declarative_base()
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
def get_database_url():
    """Get and validate database URL"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    # Convert postgres:// to postgresql:// if necessary
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    return database_url

# Configure database with retry mechanism
max_retries = 5
retry_delay = 5  # seconds

for attempt in range(max_retries):
    try:
        # Configure database
        app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
            "pool_timeout": 20,
            "pool_size": 30,
            "max_overflow": 10
        }

        # Initialize SQLAlchemy
        db.init_app(app)

        # Test the connection
        with app.app_context():
            db.engine.connect()
            logger.info("Database connection established successfully")
            break  # Connection successful, exit retry loop

    except (exc.OperationalError, exc.DatabaseError) as e:
        if attempt < max_retries - 1:
            logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            time.sleep(retry_delay)
        else:
            logger.error("Failed to connect to database after maximum retries")
            raise

# Create database tables within app context
with app.app_context():
    try:
        # Import models after db initialization to avoid circular imports
        from models import User, EscrowTransaction, Dispute
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise