from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    filters
)
from config import Config
from handlers import (
    start_command, help_command, create_escrow_command, blockchain_callback,
    language_callback, status_command, release_command
)
from logger import logger
import asyncio

class TelegramBot:
    def __init__(self):
        """Initialize the bot"""
        if not Config.TOKEN:
            raise ValueError("Bot token not found in environment variables")

        try:
            self.application = Application.builder().token(Config.TOKEN).build()
            self._setup_handlers()
            self._running = False  # Private running state
            logger.info("Bot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize bot: {str(e)}")
            raise

    def _setup_handlers(self):
        
        """Setup command and message handlers"""
        try:
            # Main commands
            self.application.add_handler(CommandHandler("start", start_command))
            self.application.add_handler(CommandHandler("help", help_command))
            self.application.add_handler(CommandHandler("new", create_escrow_command))
            self.application.add_handler(CommandHandler("status", status_command))
            self.application.add_handler(CommandHandler("ok", release_command))

            # Callback handlers for interactive buttons
            self.application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
            self.application.add_handler(CallbackQueryHandler(blockchain_callback, pattern="^chain_"))

            # Add error handler
            self.application.add_error_handler(self._error_handler)

            logger.info("Handlers setup completed")
        except Exception as e:
            logger.error(f"Error setting up handlers: {str(e)}")
            raise

    async def _error_handler(self, update, context):
        """Handle errors in the bot"""
        logger.error(f"Update {update} caused error {context.error}")

    @property
    def is_running(self):
        """Check if the bot is running"""
        return self._running

    async def start(self):

        """Start the bot with retry mechanism"""
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                logger.info("Starting bot...")
                await self.application.initialize()
                logger.info("Application initialized.")

                await self.application.start()
                logger.info("Application started.")

            # Start polling with explicit update types
                await self.application.updater.start_polling(
                    drop_pending_updates=True,
                    allowed_updates=[
                        "message",
                        "edited_message",
                        "callback_query",
                        "chat_member"
                    ]
                )
                logger.info("Polling started.")

                self._running = True
                logger.info("Bot started successfully")
                return True

            except Exception as e:
                logger.error(f"Error starting bot (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Max retries reached, bot failed to start")
                    raise


    async def stop(self):
        """Stop the bot gracefully"""
        try:
            logger.info("Stopping bot...")
            self._running = False

            # Stop in reverse order: first updater, then application
            if hasattr(self.application, 'updater') and self.application.updater:
                await self.application.updater.stop()

            await self.application.stop()
            await self.application.shutdown()
            logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")
            raise