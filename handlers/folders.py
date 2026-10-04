"""
Folder management handlers
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy import func
from datetime import datetime
from database import get_session
from models.user import User
from models.folder import Folder
from models.media import Media
from config import MAX_FOLDER_NAME_LENGTH

# Conversation states
WAITING_FOR_FOLDER_NAME = 1
SELECTING_FOLDER_ACTION = 2
WAITING_FOR_RENAME = 3


async def folders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /folders command - List user's folders"""
    user = update.effective_user
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            await update.message.reply_text(
                "❌ User not found. Please send /start first."
            )
            return
        
        # Get user's folders with media count
        folders_query = (
            session.query(
                Folder.id,
                Folder.name,
                func.count(Media.id).label('media_count')
            )
            .outerjoin(Media, Media.folder_id == Folder.id)
            .filter(Folder.user_id == db_user.id)
            .group_by(Folder.id, Folder.name)
            .order_by(Folder.created_at.desc())
            .all()
        )
        
        if not folders_query:
            message = (
                "📂 *Your Folders*\n\n"
                "You don't have any folders yet.\n\n"
                "Create your first folder with:\n"
                "➕ /newfolder"
            )
            await update.message.reply_text(message, parse_mode='Markdown')
            return
        
        # Build folder list message
        message = "📂 *Your Folders*\n\n"
        for folder_id, folder_name, media_count in folders_query:
            message += f"📁 *{folder_name}*\n"
            message += f"   📦 {media_count} item{'s' if media_count != 1 else ''}\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    finally:
        session.close()


async def my_folders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle My Folders button callback"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            await query.edit_message_text(
                "❌ User not found. Please send /start first."
            )
            return
        
        # Get user's folders
        folders = (
            session.query(Folder)
            .filter_by(user_id=db_user.id)
            .order_by(Folder.created_at.desc())
            .all()
        )
        
        if not folders:
            message = (
                "📂 *Your Folders*\n\n"
                "You don't have any folders yet.\n\n"
                "Create your first folder with:\n"
                "➕ /newfolder"
            )
            await query.edit_message_text(message, parse_mode='Markdown')
            return
        
        # Build keyboard with folder buttons
        keyboard = []
        for folder in folders:
            # Count media
            media_count = session.query(Media).filter_by(folder_id=folder.id).count()
            button_text = f"📁 {folder.name} ({media_count})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_folder_{folder.id}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📂 *Your Folders*\n\nSelect a folder to view details:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    finally:
        session.close()


async def newfolder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /newfolder command - Start folder creation"""
    await update.message.reply_text(
        "📁 *Create New Folder*\n\n"
        "Please enter a name for your new folder.\n\n"
        "Use /cancel to cancel.",
        parse_mode='Markdown'
    )
    return WAITING_FOR_FOLDER_NAME


async def new_folder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle New Folder button callback"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📁 *Create New Folder*\n\n"
        "Please enter a name for your new folder.\n\n"
        "Use /cancel to cancel.",
        parse_mode='Markdown'
    )
    return WAITING_FOR_FOLDER_NAME


async def receive_folder_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and process folder name"""
    user = update.effective_user
    folder_name = update.message.text.strip()
    
    # Validate folder name
    if not folder_name:
        await update.message.reply_text(
            "❌ Folder name cannot be empty.\n\n"
            "Please enter a valid folder name or use /cancel."
        )
        return WAITING_FOR_FOLDER_NAME
    
    if len(folder_name) > MAX_FOLDER_NAME_LENGTH:
        await update.message.reply_text(
            f"❌ Folder name is too long (max {MAX_FOLDER_NAME_LENGTH} characters).\n\n"
            "Please enter a shorter name or use /cancel."
        )
        return WAITING_FOR_FOLDER_NAME
    
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            await update.message.reply_text(
                "❌ User not found. Please send /start first."
            )
            return ConversationHandler.END
        
        # Check for duplicate folder name
        existing_folder = (
            session.query(Folder)
            .filter_by(user_id=db_user.id, name=folder_name)
            .first()
        )
        
        if existing_folder:
            await update.message.reply_text(
                f"⚠️ *Folder already exists!*\n\n"
                f"📁 {folder_name}\n\n"
                "Please choose another folder name or use /cancel.",
                parse_mode='Markdown'
            )
            return WAITING_FOR_FOLDER_NAME
        
        # Create new folder
        new_folder = Folder(
            user_id=db_user.id,
            name=folder_name
        )
        session.add(new_folder)
        session.commit()
        
        # Success message with options
        keyboard = [
            [InlineKeyboardButton("📤 Add Media", callback_data="add_media")],
            [InlineKeyboardButton("📂 My Folders", callback_data="my_folders")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *Folder created successfully!*\n\n"
            f"📁 {folder_name}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        session.rollback()
        await update.message.reply_text(
            "❌ An error occurred while creating the folder. Please try again."
        )
    finally:
        session.close()
    
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command"""
    await update.message.reply_text(
        "❌ Operation cancelled.\n\n"
        "Use /start to see the main menu."
    )
    return ConversationHandler.END


async def view_folder_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed folder view with media counts"""
    query = update.callback_query
    await query.answer()
    
    # Extract folder_id from callback data (format: "view_folder_<id>")
    folder_id = int(query.data.split('_')[2])
    user = update.effective_user
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            await query.edit_message_text("❌ User not found. Please send /start first.")
            return
        
        # Get folder (verify ownership)
        folder = (
            session.query(Folder)
            .filter_by(id=folder_id, user_id=db_user.id)
            .first()
        )
        
        if not folder:
            await query.edit_message_text("❌ Folder not found.")
            return
        
        # Count photos and videos
        photo_count = (
            session.query(Media)
            .filter_by(folder_id=folder.id, media_type='photo')
            .count()
        )
        
        video_count = (
            session.query(Media)
            .filter_by(folder_id=folder.id, media_type='video')
            .count()
        )
        
        total_count = photo_count + video_count
        
        # Build message
        message = (
            f"📁 *{folder.name}*\n\n"
            f"🖼️ Photos: {photo_count}\n"
            f"🎥 Videos: {video_count}\n"
            f"📦 Total: {total_count}"
        )
        
        # Build keyboard
        keyboard = []
        if photo_count > 0:
            keyboard.append([InlineKeyboardButton("🖼️ View Photos", callback_data=f"view_photos_{folder.id}")])
        if video_count > 0:
            keyboard.append([InlineKeyboardButton("🎥 View Videos", callback_data=f"view_videos_{folder.id}")])
        if total_count > 0:
            keyboard.append([InlineKeyboardButton("📦 View All", callback_data=f"view_all_{folder.id}")])
        
        keyboard.append([InlineKeyboardButton("📤 Add Media", callback_data=f"add_to_folder_{folder.id}")])
        keyboard.append([InlineKeyboardButton("✏️ Rename Folder", callback_data=f"rename_folder_{folder.id}")])
        keyboard.append([InlineKeyboardButton("🗑️ Delete Folder", callback_data=f"delete_folder_{folder.id}")])
        keyboard.append([InlineKeyboardButton("⬅️ Back to Folders", callback_data="my_folders")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    finally:
        session.close()



async def rename_folder_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start rename folder flow"""
    query = update.callback_query
    await query.answer()
    
    # Extract folder_id from callback data (format: "rename_folder_<id>")
    folder_id = int(query.data.split('_')[2])
    user = update.effective_user
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            await query.edit_message_text("❌ User not found. Please send /start first.")
            return ConversationHandler.END
        
        # Verify folder ownership
        folder = (
            session.query(Folder)
            .filter_by(id=folder_id, user_id=db_user.id)
            .first()
        )
        
        if not folder:
            await query.edit_message_text("❌ Folder not found.")
            return ConversationHandler.END
        
        # Store folder info in context
        context.user_data['rename_folder_id'] = folder_id
        context.user_data['rename_folder_old_name'] = folder.name
        
        await query.edit_message_text(
            f"✏️ *Rename Folder*\n\n"
            f"Current name: *{folder.name}*\n\n"
            f"Enter the new folder name:\n\n"
            f"Use /cancel to cancel.",
            parse_mode='Markdown'
        )
        
        return WAITING_FOR_RENAME
        
    finally:
        session.close()


async def receive_new_folder_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and process new folder name"""
    user = update.effective_user
    new_name = update.message.text.strip()
    
    # Get stored folder info
    folder_id = context.user_data.get('rename_folder_id')
    old_name = context.user_data.get('rename_folder_old_name')
    
    if not folder_id:
        await update.message.reply_text("❌ Error: Folder information not found.")
        return ConversationHandler.END
    
    # Validate new name
    if not new_name:
        await update.message.reply_text(
            "❌ Folder name cannot be empty.\n\n"
            "Please enter a valid folder name or use /cancel."
        )
        return WAITING_FOR_RENAME
    
    if len(new_name) > MAX_FOLDER_NAME_LENGTH:
        await update.message.reply_text(
            f"❌ Folder name is too long (max {MAX_FOLDER_NAME_LENGTH} characters).\n\n"
            "Please enter a shorter name or use /cancel."
        )
        return WAITING_FOR_RENAME
    
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            await update.message.reply_text("❌ User not found. Please send /start first.")
            return ConversationHandler.END
        
        # Get the folder to rename (verify ownership)
        folder = (
            session.query(Folder)
            .filter_by(id=folder_id, user_id=db_user.id)
            .first()
        )
        
        if not folder:
            await update.message.reply_text("❌ Folder not found.")
            return ConversationHandler.END
        
        # Check for duplicate folder name (case-insensitive)
        duplicate_folder = (
            session.query(Folder)
            .filter(
                Folder.user_id == db_user.id,
                Folder.id != folder_id,  # Exclude current folder
                func.lower(Folder.name) == func.lower(new_name)
            )
            .first()
        )
        
        if duplicate_folder:
            await update.message.reply_text(
                f"❌ *A folder with this name already exists.*\n\n"
                f"Please choose another name or use /cancel.",
                parse_mode='Markdown'
            )
            return WAITING_FOR_RENAME
        
        # Rename the folder
        old_name = folder.name
        folder.name = new_name
        folder.updated_at = datetime.utcnow()
        session.commit()
        
        # Clear context
        context.user_data.pop('rename_folder_id', None)
        context.user_data.pop('rename_folder_old_name', None)
        
        # Show success message with option to view folder
        keyboard = [
            [InlineKeyboardButton("📁 View Folder", callback_data=f"view_folder_{folder.id}")],
            [InlineKeyboardButton("📂 My Folders", callback_data="my_folders")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *Folder renamed successfully!*\n\n"
            f"Old name: {old_name}\n"
            f"New name: {new_name}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        session.rollback()
        await update.message.reply_text(
            "❌ An error occurred while renaming the folder. Please try again."
        )
    finally:
        session.close()
    
    return ConversationHandler.END


async def delete_folder_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show delete confirmation dialog"""
    query = update.callback_query
    await query.answer()
    
    # Extract folder_id from callback data (format: "delete_folder_<id>")
    folder_id = int(query.data.split('_')[2])
    user = update.effective_user
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            await query.edit_message_text("❌ User not found. Please send /start first.")
            return
        
        # Verify folder ownership
        folder = (
            session.query(Folder)
            .filter_by(id=folder_id, user_id=db_user.id)
            .first()
        )
        
        if not folder:
            await query.edit_message_text("❌ Folder not found.")
            return
        
        # Count photos and videos
        photo_count = (
            session.query(Media)
            .filter_by(folder_id=folder.id, media_type='photo')
            .count()
        )
        
        video_count = (
            session.query(Media)
            .filter_by(folder_id=folder.id, media_type='video')
            .count()
        )
        
        total_count = photo_count + video_count
        
        # Build confirmation message
        message = (
            f"⚠️ *Delete Folder?*\n\n"
            f"Folder: *{folder.name}*\n"
            f"🖼️ Photos: {photo_count}\n"
            f"🎥 Videos: {video_count}\n"
            f"📦 Total media: {total_count}\n\n"
            f"All media records inside this folder will also be deleted.\n\n"
            f"Are you sure?"
        )
        
        # Build keyboard
        keyboard = [
            [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_delete_{folder.id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_delete_{folder.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    finally:
        session.close()


async def delete_folder_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute folder deletion"""
    query = update.callback_query
    await query.answer()
    
    # Extract folder_id from callback data (format: "confirm_delete_<id>")
    folder_id = int(query.data.split('_')[2])
    user = update.effective_user
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            await query.edit_message_text("❌ User not found. Please send /start first.")
            return
        
        # Verify folder ownership
        folder = (
            session.query(Folder)
            .filter_by(id=folder_id, user_id=db_user.id)
            .first()
        )
        
        if not folder:
            await query.edit_message_text("❌ Folder not found.")
            return
        
        folder_name = folder.name
        
        # Delete folder (cascade will delete media)
        session.delete(folder)
        session.commit()
        
        await query.edit_message_text(
            f"✅ *Folder deleted successfully.*\n\n"
            f"Deleted: {folder_name}",
            parse_mode='Markdown'
        )
        
        # Show folder list after 1 second delay
        import asyncio
        await asyncio.sleep(1)
        
        # Get updated folder list
        folders = (
            session.query(Folder)
            .filter_by(user_id=db_user.id)
            .order_by(Folder.created_at.desc())
            .all()
        )
        
        if not folders:
            message = (
                "📂 *Your Folders*\n\n"
                "You don't have any folders yet.\n\n"
                "Create your first folder with:\n"
                "➕ /newfolder"
            )
            await query.message.reply_text(message, parse_mode='Markdown')
            return
        
        # Build keyboard with folder buttons
        keyboard = []
        for folder in folders:
            media_count = session.query(Media).filter_by(folder_id=folder.id).count()
            button_text = f"📁 {folder.name} ({media_count})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_folder_{folder.id}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            "📂 *Your Folders*\n\nSelect a folder to view details:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        session.rollback()
        await query.edit_message_text(
            "❌ An error occurred while deleting the folder. Please try again."
        )
    finally:
        session.close()


async def cancel_delete_folder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel folder deletion and return to folder view"""
    query = update.callback_query
    await query.answer()
    
    # Extract folder_id from callback data (format: "cancel_delete_<id>")
    folder_id = int(query.data.split('_')[2])
    
    # Return to folder view
    context.user_data['callback_data'] = f"view_folder_{folder_id}"
    await view_folder_details(update, context)


async def cancel_rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel rename operation"""
    # Clear context
    folder_id = context.user_data.pop('rename_folder_id', None)
    context.user_data.pop('rename_folder_old_name', None)
    
    if folder_id:
        keyboard = [[InlineKeyboardButton("📁 Back to Folder", callback_data=f"view_folder_{folder_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ Rename cancelled.",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "❌ Rename cancelled.\n\n"
            "Use /start to see the main menu."
        )
    
    return ConversationHandler.END
