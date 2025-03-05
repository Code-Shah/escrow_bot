import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import __version__ as TG_VER
from telegram.ext import ContextTypes
from keep_alive import keep_alive
from logger import logger
from bot import TelegramBot
from app import app, db
# from flask import Flask, jsonify

# app = Flask(__name__)

# @app.route('/')
# def home():
#     return jsonify({"message": "Namaste Vercel!"})

# # Vercel ke liye WSGI adapter
# def handler(request):
#     from flask import Response
#     with app.app_context():
#         response = app.full_dispatch_request()
#         return Response(response.get_data(), status=response.status_code, headers=dict(response.headers))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")

async def main():
    """Main function to run the bot"""
    # Check environment variables
    if not os.getenv("BOT_TOKEN"):
        raise ValueError("BOT_TOKEN environment variable is not set")
    if not os.getenv("DATABASE_URL"):
        raise ValueError("DATABASE_URL environment variable is not set")

    bot = None
    keep_alive_started = False

    try:
        # Initialize Flask app context and ensure database is ready
        with app.app_context():
            # Verify database connection
            try:
                db.engine.connect()
                logger.info("Database connection successful")
            except Exception as db_error:
                logger.error(f"Database connection failed: {str(db_error)}")
                raise

            # Make sure tables exist
            db.create_all()
            logger.info("Database initialized successfully")

            # Start keep-alive server only if not already running
            if not keep_alive_started:
                try:
                    keep_alive()
                    keep_alive_started = True
                    logger.info("Keep-alive server started")
                except Exception as ka_error:
                    logger.warning(f"Keep-alive server error (non-critical): {str(ka_error)}")

            # Initialize bot
            bot = TelegramBot()

            # Start bot and wait for it to be ready
            start_success = await bot.start()
            if not start_success:
                raise Exception("Bot failed to start properly")

            logger.info("Bot started successfully and is now running")

            # Keep the bot running with proper health checks
            while True:
                if not bot.is_running:
                    logger.error("Bot stopped running unexpectedly")
                    raise Exception("Bot stopped unexpectedly")
                await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        raise
    finally:
        if bot:
            try:
                await bot.stop()
            except Exception as stop_error:
                logger.error(f"Error stopping bot: {str(stop_error)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")