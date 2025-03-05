from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from logger import logger
from app import db, app
from models import User, EscrowTransaction
from config import Config
from decimal import Decimal
from datetime import datetime

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    try:
        user = update.effective_user
        chat_type = update.effective_chat.type

        with app.app_context():
            # For group chats, show simplified message
            if chat_type in ['group', 'supergroup']:
                welcome_message = (
                    "👋 *Hi! I'm your AI Escrow Assistant!*\n\n"
                    "I'm here to help make deals safe and easy. Here's what I can do:\n\n"
                    "🤝 `/new` - Start a new deal\n"
                    "🔍 `/status` - Check your deals\n"
                    "✅ `/ok` - Confirm everything's good\n"
                    "❓ `/help` - Get my help\n\n"
                    "💡 *Example:* Type `/new @seller 100 Product`\n"
                    "I'll guide you through the whole process!\n\n"
                    "🔒 *Fixed Fee:* $0.50 per transaction for secure escrow service"
                )
                await update.message.reply_text(welcome_message, parse_mode='Markdown')
                return

            # For private chats, create or get user
            db_user = User.query.filter_by(telegram_id=str(user.id)).first()
            if not db_user:
                db_user = User(telegram_id=str(user.id), username=user.username)
                db.session.add(db_user)
                db.session.commit()
                logger.info(f"Created new user record for {user.id}")

            # Create language selection keyboard
            keyboard = []
            for code, name in Config.SUPPORTED_LANGUAGES.items():
                keyboard.append([InlineKeyboardButton(f"🌐 {name}", callback_data=f"lang_{code}")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            welcome_message = (
                f"👋 *Hello {user.first_name}!*\n\n"
                "I'm your AI Escrow Assistant, and I'm here to help make your deals safe and easy!\n\n"
                "🛡️ *How I Help You:*\n"
                "1️⃣ Create secure deals\n"
                "2️⃣ Handle payments safely\n"
                "3️⃣ Guide both parties\n"
                "4️⃣ Verify transactions\n\n"
                "💰 *Service Fee:*\n"
                "• Fixed $0.50 per transaction\n"
                "• Automatically deducted\n"
                "• Ensures secure escrow service\n\n"
                "🌍 *First, let's set your preferred language:*"
            )

            await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")
        await update.message.reply_text("Oops! Something went wrong. Let's try again with /start")

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection callback"""
    try:
        query = update.callback_query
        lang_code = query.data.replace("lang_", "")
        user = update.effective_user

        with app.app_context():
            # Update user language preference
            db_user = User.query.filter_by(telegram_id=str(user.id)).first()
            if not db_user:
                db_user = User(telegram_id=str(user.id), username=user.username)
                db.session.add(db_user)

            db_user.language = lang_code
            db.session.commit()

            welcome_message = (
                f"🎉 *Perfect! I'll speak {Config.SUPPORTED_LANGUAGES[lang_code]} with you!*\n\n"
                f"Hey {user.first_name}, I'm ready to help you make safe deals!\n\n"
                "💫 *Quick Start:*\n"
                "1. Add me to your group chat\n"
                "2. Start a deal with `/new`\n"
                "3. I'll guide you step by step!\n\n"
                "Need help? Just type /help anytime! 😊"
            )

            await query.message.edit_text(
                welcome_message,
                parse_mode='Markdown'
            )
            await query.answer(f"Language set to {Config.SUPPORTED_LANGUAGES[lang_code]}! 🌟")

    except Exception as e:
        logger.error(f"Error in language selection: {str(e)}")
        if 'query' in locals():
            await query.answer("Oops! Something went wrong. Let's try again! 😅")

async def create_escrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /new command for creating escrow"""
    try:
        logger.info("Received /new command for creating escrow.")
        
        with app.app_context():
            user = update.effective_user
            chat = update.effective_chat
            
            logger.info(f"User: {user.username}, Chat Type: {chat.type}")

            # Only allow in groups
            if chat.type not in ['group', 'supergroup']:
                await update.message.reply_text(
                    "🤔 Let's do this in a group chat where both buyer and seller are present!\n"
                    "Add me to your group and try again. 👥"
                )
                return

            # Check command format
            args = context.args
            logger.info(f"Command arguments: {args}")

            # Ensure that there are at least 3 arguments: seller, amount, and description
            if len(args) < 3:
                await update.message.reply_text(
                    "👋 *Let me help you create a deal!*\n\n"
                    "Here's how to do it:\n"
                    "Type `/new @seller amount description`\n\n"
                    "*For example:*\n"
                    "`/new @john 100 Product`\n\n"
                    "💰 *Note:* A fixed fee of $0.50 will be added to the transaction amount.\n"
                    "I'll help guide you through the rest! 🤝",
                    parse_mode='Markdown'
                )
                return

            # Parse command
            seller_username = args[0].replace('@', '')
            try:
                amount = Decimal(args[1])
                if amount <= 0:
                    raise ValueError
                total_amount = amount + Decimal('0.50')
            except ValueError:
                await update.message.reply_text(
                    "🤔 The amount doesn't look right.\n"
                    "Please use a positive number, like:\n"
                    "`/new @seller 100 Product`",
                    parse_mode='Markdown'
                )
                return

            description = ' '.join(args[2:])
            description = description.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


            # Get or create users
            buyer = User.query.filter_by(telegram_id=str(user.id)).first()
            if not buyer:
                buyer = User(telegram_id=str(user.id), username=user.username)
                db.session.add(buyer)
                try:
                    db.session.commit()
                    logger.info("New buyer created and committed to the database.")
                except Exception as e:
                    logger.error(f"Error committing buyer to the database: {str(e)}")
                    await update.message.reply_text(
                        "Sorry, there was an issue saving your data. Please try again."
                    )
                    return

            seller = User.query.filter_by(username=seller_username).first()
            if not seller:
                await update.message.reply_text(
                    f"👋 I see that @{seller_username} hasn't met me yet!\n\n"
                    "🤝 Ask them to:\n"
                    "1. Start a chat with me (@Legit_escrow_bot)\n"
                    "2. Send me a /start message\n"
                    "3. Then we can create the deal!"
                )
                return

            # Create transaction
            transaction = EscrowTransaction(
                buyer_id=buyer.id,
                seller_id=seller.id,
                amount=amount,
                description=description,
                chat_id=str(chat.id),
                fee_amount=Decimal('0.50'),
                fee_paid=False
            )

            db.session.add(transaction)
            try:
                db.session.commit()
                logger.info("Transaction created and committed to the database.")
            except Exception as e:
                logger.error(f"Error committing transaction to the database: {str(e)}")
                await update.message.reply_text(
                    "Sorry, there was an issue processing your transaction. Please try again."
                )
                return

            # Create blockchain selection keyboard
            keyboard = []
            for chain, info in Config.BLOCKCHAIN_INFO.items():
                speed_emoji = "⚡️" if "1s" in info['speed'] else "🚀"
                button = [InlineKeyboardButton(
                    f"{info['icon']} {chain} • {speed_emoji} {info['speed']} • 💰 {info['gas_fee']}",
                    callback_data=f"chain_{chain}_{transaction.id}"
                )]
                keyboard.append(button)

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"🎉 *Great! Let's set up your deal #{transaction.id}*\n\n"
                f"💫 *Deal Summary:*\n"
                f"💰 Base Amount: ${amount}\n"
                f"🔒 Service Fee: $0.50\n"
                f"💎 Total Amount: ${total_amount}\n"
                f"📝 For: {description}\n"
                f"🤝 Between: @{buyer.username} and @{seller_username}\n\n"
                "🌟 *Next Step:*\n"
                "Choose a payment network below. I'll help you pick:\n\n"
                "💡 *Quick Guide:*\n"
                "• BEP20: Lowest fees\n"
                "• ERC20: Most secure\n"
                "• Optimism: Fast & cheap\n"
                "• Arbitrum: Ultra fast",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

    except Exception as e:
        logger.error(f"Error creating escrow: {str(e)}")
        await update.message.reply_text(
            "Oops! Something didn't work right. 😅\n"
            "Let's try that again! Need help? Type /help"
        )


async def blockchain_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle blockchain selection"""
    try:
        with app.app_context():
            query = update.callback_query
            user = update.effective_user

            # Get transaction info
            chain = query.data.split('_')[1]
            tx_id = int(query.data.split('_')[2])

            transaction = EscrowTransaction.query.get(tx_id)
            if not transaction:
                await query.answer("I couldn't find that deal! Let's start a new one.")
                return

            if str(user.id) != transaction.buyer.telegram_id:
                await query.answer("Only the buyer can select the payment network! 👀")
                return

            # Update transaction
            transaction.blockchain = chain
            db.session.commit()

            # Get wallet address
            wallet = Config.NETWORK_WALLETS[chain]
            network = Config.BLOCKCHAIN_INFO[chain]

            payment_message = (
                f"🎉 *Perfect! Deal #{tx_id} is ready!*\n\n"
                f"💰 *Amount to Send:* ${transaction.amount + transaction.fee_amount}\n"
                f"🔗 *Network:* {chain}\n"
                f"⚡️ *Speed:* {network['speed']}\n"
                f"💸 *Network Fee:* {network['gas_fee']}\n\n"
                "📤 *Send payment to:*\n"
                f"`{wallet}`\n\n"
                "🎯 *What's Next:*\n"
                f"1. Send ${transaction.amount + transaction.fee_amount} to the address above\n"
                f"2. Once sent, type: `/ok {tx_id}`\n"
                "3. I'll verify everything and help complete the deal!\n\n"
                "💡 Need help? Just type /help"
            )

            await query.message.edit_text(payment_message, parse_mode='Markdown')
            await query.answer("Great choice! Let's proceed with payment! 🚀")

            # Notify group
            group_message = (
                "🎉 *New Deal Started!*\n\n"
                f"💰 Amount: ${transaction.amount + transaction.fee_amount}\n"
                f"🤝 Buyer: @{transaction.buyer.username}\n"
                f"🤝 Seller: @{transaction.seller.username}\n"
                f"🔗 Network: {chain}\n\n"
                "⏳ Waiting for payment...\n"
                "I'll keep everyone updated on the progress! 👀"
            )

            if transaction.chat_id:
                await context.bot.send_message(
                    chat_id=transaction.chat_id,
                    text=group_message,
                    parse_mode='Markdown'
                )

    except Exception as e:
        logger.error(f"Error in blockchain selection: {str(e)}")
        if 'query' in locals():
            await query.answer("Oops! Something went wrong. Let's try again! 😅")

async def release_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /ok command"""
    try:
        with app.app_context():
            user = update.effective_user
            args = context.args

            if not args:
                await update.message.reply_text(
                    "❌ *Wrong Format*\n\n"
                    "Type like this:\n"
                    "`/ok 123`",
                    parse_mode='Markdown'
                )
                return

            tx_id = int(args[0])
            transaction = EscrowTransaction.query.get(tx_id)

            if not transaction:
                await update.message.reply_text("❌ Deal not found")
                return

            if str(user.id) != transaction.buyer.telegram_id:
                await update.message.reply_text("❌ Only the buyer can confirm")
                return

            # Complete the deal
            transaction.status = 'completed'
            transaction.completed_at = datetime.utcnow()
            transaction.fee_paid = True
            db.session.commit()

            # Notify group
            if transaction.chat_id:
                await context.bot.send_message(
                    chat_id=transaction.chat_id,
                    text=(
                        f"✅ *Deal #{tx_id} Complete!*\n\n"
                        f"💰 Amount: ${transaction.amount + transaction.fee_amount}\n"
                        f"👤 Buyer: @{transaction.buyer.username}\n"
                        f"👤 Seller: @{transaction.seller.username}\n\n"
                        "🎉 Everyone happy!"
                    ),
                    parse_mode='Markdown'
                )

            await update.message.reply_text("✅ Deal completed!")

    except Exception as e:
        logger.error(f"Error releasing payment: {str(e)}")
        await update.message.reply_text("❌ Something went wrong")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /status command"""
    try:
        with app.app_context():
            user = update.effective_user
            chat = update.effective_chat

            # For group chat
            if chat.type in ['group', 'supergroup']:
                transactions = EscrowTransaction.query.filter_by(
                    chat_id=str(chat.id)
                ).order_by(EscrowTransaction.created_at.desc()).limit(5).all()

                if not transactions:
                    await update.message.reply_text("No active deals in this group")
                    return

                status = "🔍 *Recent Deals*\n\n"
                for tx in transactions:
                    status += (
                        f"💫 *Deal #{tx.id}*\n"
                        f"💰 Amount: ${tx.amount + tx.fee_amount}\n"
                        f"👤 Buyer: @{tx.buyer.username}\n"
                        f"👤 Seller: @{tx.seller.username}\n"
                        f"📊 Status: {tx.status}\n"
                        "➖➖➖➖➖➖➖➖\n"
                    )

                await update.message.reply_text(status, parse_mode='Markdown')
                return

            # For private chat
            buyer_deals = EscrowTransaction.query.join(
                User, EscrowTransaction.buyer_id == User.id
            ).filter(User.telegram_id == str(user.id)).all()

            seller_deals = EscrowTransaction.query.join(
                User, EscrowTransaction.seller_id == User.id
            ).filter(User.telegram_id == str(user.id)).all()

            if not (buyer_deals or seller_deals):
                await update.message.reply_text(
                    "No deals found.\n"
                    "Create new deal with /new in group chat"
                )
                return

            status = "🔍 *Your Deals*\n\n"

            if buyer_deals:
                status += "💳 *As Buyer:*\n"
                for tx in buyer_deals:
                    status += (
                        f"📝 *#{tx.id}*\n"
                        f"💰 Amount: ${tx.amount + tx.fee_amount}\n"
                        f"👤 Seller: @{tx.seller.username}\n"
                        f"📊 Status: {tx.status}\n"
                        "➖➖➖➖➖➖➖➖\n"
                    )

            if seller_deals:
                status += "\n🏦 *As Seller:*\n"
                for tx in seller_deals:
                    status += (
                        f"📝 *#{tx.id}*\n"
                        f"💰 Amount: ${tx.amount + tx.fee_amount}\n"
                        f"👤 Buyer: @{tx.buyer.username}\n"
                        f"📊 Status: {tx.status}\n"
                        "➖➖➖➖➖➖➖➖\n"
                    )

            await update.message.reply_text(status, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        await update.message.reply_text("❌ Something went wrong")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command"""
    help_message = (
        "👋 *Hey there! Need help? I've got you covered!*\n\n"
        "🚀 *Simple Commands:*\n"
        "• `/new` - Start a new deal\n"
        "• `/status` - Check your deals\n"
        "• `/ok` - Confirm everything's good\n"
        "• `/help` - Get my help\n\n"
        "💰 *Service Fee:*\n"
        "• Fixed $0.50 per transaction\n"
        "• Automatically added to deal amount\n"
        "• Ensures secure escrow service\n\n"
        "💡 *Quick Example:*\n"
        "1. Type `/new @seller 100 Product`\n"
        "2. Choose payment network\n"
        "3. Send payment (amount + $0.50 fee)\n"
        "4. Type `/ok` when done\n\n"
        "🤝 *I'll guide you through each step!*\n"
        "Just start a deal and I'll help you both stay safe! 😊"
    )

    await update.message.reply_text(help_message, parse_mode='Markdown')

# Export handlers
__all__ = [
    'start_command',
    'help_command',
    'create_escrow_command',
    'blockchain_callback',
    'release_command',
    'status_command',
    'language_callback'
]