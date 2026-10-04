"""
Search functionality handlers
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import get_session
from models.user import User
from models.folder import Folder
from models.media import Media

# Conversation states
WAITING_FOR_SEARCH_QUERY = 1


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command"""
    user = update.effective_user
    
    # Check if search query provided with command
    if context.args:
        search_query = ' '.join(context.args)
        await perform_search(update, context, search_query, user)
        return ConversationHandler.END
    else:
        # Ask for search query
        await update.message.reply_text(
            "🔍 *Search Folders*\n\n"
            "Enter folder name to search:\n\n"
            "Use /cancel to cancel.",
            parse_mode='Markdown'
        )
        return WAITING_FOR_SEARCH_QUERY


async def search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Search button callback"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔍 *Search Folders*\n\n"
        "Enter folder name to search:\n\n"
        "Use /cancel to cancel.",
        parse_mode='Markdown'
    )
    return WAITING_FOR_SEARCH_QUERY


async def receive_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle search query input"""
    user = update.effective_user
    search_query = update.message.text.strip()
    
    if not search_query:
        await update.message.reply_text(
            "❌ Search query cannot be empty.\n\n"
            "Please enter a folder name or use /cancel."
        )
        return WAITING_FOR_SEARCH_QUERY
    
    await perform_search(update, context, search_query, user)
    return ConversationHandler.END


async def perform_search(update, context, search_query, user):
    """Perform the actual search"""
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            if update.callback_query:
                await update.callback_query.edit_message_text("❌ User not found. Please send /start first.")
            else:
                await update.message.reply_text("❌ User not found. Please send /start first.")
            return
        
        # Search folders (case-insensitive)
        matching_folders = (
            session.query(Folder)
            .filter(
                Folder.user_id == db_user.id,
                Folder.name.ilike(f"%{search_query}%")
            )
            .order_by(Folder.name)
            .all()
        )
        
        if not matching_folders:
            message = (
                f"🔍 *Search results for:* `{search_query}`\n\n"
                "No matching folders found."
            )
            if update.callback_query:
                await update.callback_query.edit_message_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text(message, parse_mode='Markdown')
            return
        
        # Build results message with buttons
        message = f"🔍 *Search results for:* `{search_query}`\n\n"
        
        keyboard = []
        for folder in matching_folders:
            media_count = session.query(Media).filter_by(folder_id=folder.id).count()
            message += f"📁 *{folder.name}*\n"
            message += f"   📦 {media_count} item{'s' if media_count != 1 else ''}\n\n"
            
            # Add button for each folder
            keyboard.append([InlineKeyboardButton(
                f"📁 {folder.name}",
                callback_data=f"view_folder_{folder.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
    finally:
        session.close()


async def cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel search"""
    await update.message.reply_text(
        "❌ Search cancelled.\n\n"
        "Use /start to see the main menu."
    )
    return ConversationHandler.END
