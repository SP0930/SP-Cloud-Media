"""
Start and Help command handlers
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_session
from models.user import User


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Create or update user in database
    session = get_session()
    try:
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            db_user = User(
                telegram_user_id=user.id,
                username=user.username,
                first_name=user.first_name
            )
            session.add(db_user)
            session.commit()
        else:
            # Update user info if changed
            db_user.username = user.username
            db_user.first_name = user.first_name
            session.commit()
    finally:
        session.close()
    
    # Create inline keyboard
    keyboard = [
        [InlineKeyboardButton("📂 My Folders", callback_data="my_folders")],
        [InlineKeyboardButton("➕ New Folder", callback_data="new_folder")],
        [InlineKeyboardButton("📤 Add Media", callback_data="add_media")],
        [InlineKeyboardButton("📥 Get Media", callback_data="get_media")],
        [InlineKeyboardButton("🔍 Search", callback_data="search")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = (
        "☁️ *Welcome to SP Cloud*\n\n"
        "Your personal Telegram Media Vault.\n\n"
        "Store your photos and videos securely in organized folders."
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "☁️ *SP Cloud - Help*\n\n"
        "*Available Commands:*\n\n"
        "/start - Show main menu\n"
        "/help - Show this help message\n"
        "/folders - View your folders\n"
        "/newfolder - Create a new folder\n"
        "/add - Add media to a folder\n"
        "/get - Retrieve media from a folder\n"
        "/search - Search folders by name\n"
        "/cancel - Cancel current operation\n\n"
        "*How to use:*\n\n"
        "1️⃣ Create folders to organize your media\n"
        "2️⃣ Add photos and videos to your folders\n"
        "3️⃣ Retrieve your media anytime\n\n"
        "Your media is stored securely and only accessible by you."
    )
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            help_text,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown'
        )


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help button callback"""
    await help_command(update, context)
