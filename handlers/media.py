"""
Media upload and retrieval handlers
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import get_session
from models.user import User
from models.folder import Folder
from models.media import Media

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_FOLDER_FOR_UPLOAD = 1
UPLOADING_MEDIA = 2
SELECTING_FOLDER_FOR_GET = 3


async def add_media_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add command - Start media upload flow"""
    user = update.effective_user
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            await update.message.reply_text("❌ User not found. Please send /start first.")
            return ConversationHandler.END
        
        # Get user's folders
        folders = (
            session.query(Folder)
            .filter_by(user_id=db_user.id)
            .order_by(Folder.name)
            .all()
        )
        
        if not folders:
            await update.message.reply_text(
                "📂 *No folders found*\n\n"
                "Please create a folder first using /newfolder",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Build folder selection keyboard
        keyboard = []
        for folder in folders:
            keyboard.append([InlineKeyboardButton(f"📁 {folder.name}", callback_data=f"upload_to_{folder.id}")])
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_upload")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📁 *Select a folder:*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return SELECTING_FOLDER_FOR_UPLOAD
        
    finally:
        session.close()


async def add_media_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Add Media button callback"""
    logger.info("📤 Add Media button clicked")
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    logger.info(f"Add Media handler entered for user {user.id}")
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            logger.warning(f"User {user.id} not found in database")
            await query.edit_message_text("❌ User not found. Please send /start first.")
            return ConversationHandler.END
        
        # Get user's folders
        folders = (
            session.query(Folder)
            .filter_by(user_id=db_user.id)
            .order_by(Folder.name)
            .all()
        )
        
        logger.info(f"Found {len(folders)} folders for user {user.id}")
        
        if not folders:
            logger.info("No folders found, prompting user to create one")
            await query.edit_message_text(
                "📂 *No folders found*\n\n"
                "Please create a folder first using /newfolder",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Build folder selection keyboard
        keyboard = []
        for folder in folders:
            keyboard.append([InlineKeyboardButton(f"📁 {folder.name}", callback_data=f"upload_to_{folder.id}")])
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_upload")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        logger.info("Showing folder selection menu")
        await query.edit_message_text(
            "📁 *Select a folder:*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        logger.info("Entering SELECTING_FOLDER_FOR_UPLOAD state")
        return SELECTING_FOLDER_FOR_UPLOAD
        
    finally:
        session.close()


async def folder_selected_for_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle folder selection for upload"""
    query = update.callback_query
    await query.answer()
    
    # Extract folder_id from callback data
    folder_id = int(query.data.split('_')[2])
    logger.info(f"Folder {folder_id} selected for upload")
    
    user = update.effective_user
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            await query.edit_message_text("❌ User not found.")
            return ConversationHandler.END
        
        # Verify folder ownership
        folder = (
            session.query(Folder)
            .filter_by(id=folder_id, user_id=db_user.id)
            .first()
        )
        
        if not folder:
            logger.warning(f"Folder {folder_id} not found or doesn't belong to user {user.id}")
            await query.edit_message_text("❌ Folder not found.")
            return ConversationHandler.END
        
        # Store folder_id in context for later use
        context.user_data['upload_folder_id'] = folder_id
        context.user_data['upload_folder_name'] = folder.name
        
        logger.info(f"Entering upload mode for folder: {folder.name}")
        
        # Create done button
        keyboard = [[InlineKeyboardButton("✅ Done", callback_data="done_uploading")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📤 *Send photos or videos for folder:*\n\n"
            f"📁 {folder.name}\n\n"
            "Send your media files now. You can send multiple files.\n"
            "Click ✅ Done when finished or use /cancel",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return UPLOADING_MEDIA
        
    finally:
        session.close()


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo upload"""
    # Check if we're in upload mode
    if 'upload_folder_id' not in context.user_data:
        logger.warning("Photo received but not in upload mode")
        return
    
    folder_id = context.user_data['upload_folder_id']
    folder_name = context.user_data['upload_folder_name']
    user = update.effective_user
    
    logger.info(f"Photo received from user {user.id} for folder {folder_name}")
    
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            return
        
        # Verify folder ownership
        folder = (
            session.query(Folder)
            .filter_by(id=folder_id, user_id=db_user.id)
            .first()
        )
        
        if not folder:
            await update.message.reply_text("❌ Folder not found.")
            return
        
        # Get the highest resolution photo
        photo = update.message.photo[-1]
        
        logger.info(f"Saving photo with file_id: {photo.file_id}")
        
        # Save to database
        new_media = Media(
            folder_id=folder_id,
            telegram_file_id=photo.file_id,
            file_unique_id=photo.file_unique_id,
            media_type='photo'
        )
        session.add(new_media)
        session.commit()
        
        logger.info(f"Photo saved successfully to folder {folder_name}")
        await update.message.reply_text(f"✅ Saved to {folder_name}")
        
    except Exception as e:
        logger.error(f"Error saving photo: {e}")
        session.rollback()
        await update.message.reply_text("❌ Failed to save photo. Please try again.")
    finally:
        session.close()
    
    return UPLOADING_MEDIA


async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video upload"""
    # Check if we're in upload mode
    if 'upload_folder_id' not in context.user_data:
        return
    
    folder_id = context.user_data['upload_folder_id']
    folder_name = context.user_data['upload_folder_name']
    user = update.effective_user
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            return
        
        # Verify folder ownership
        folder = (
            session.query(Folder)
            .filter_by(id=folder_id, user_id=db_user.id)
            .first()
        )
        
        if not folder:
            await update.message.reply_text("❌ Folder not found.")
            return
        
        # Get video
        video = update.message.video
        
        # Save to database
        new_media = Media(
            folder_id=folder_id,
            telegram_file_id=video.file_id,
            file_unique_id=video.file_unique_id,
            media_type='video'
        )
        session.add(new_media)
        session.commit()
        
        await update.message.reply_text(f"✅ Saved to {folder_name}")
        
    except Exception as e:
        session.rollback()
        await update.message.reply_text("❌ Failed to save video. Please try again.")
    finally:
        session.close()
    
    return UPLOADING_MEDIA


async def done_uploading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle done button - finish upload"""
    query = update.callback_query
    await query.answer()
    
    folder_name = context.user_data.get('upload_folder_name', 'your folder')
    
    # Clear upload context
    context.user_data.pop('upload_folder_id', None)
    context.user_data.pop('upload_folder_name', None)
    
    await query.edit_message_text(
        f"✅ *Upload complete!*\n\n"
        f"Media saved to: {folder_name}\n\n"
        "Use /folders to view your folders.",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END


async def cancel_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel upload"""
    query = update.callback_query
    await query.answer()
    
    # Clear upload context
    context.user_data.pop('upload_folder_id', None)
    context.user_data.pop('upload_folder_name', None)
    
    await query.edit_message_text("❌ Upload cancelled.")
    
    return ConversationHandler.END


async def add_to_folder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle add media to specific folder from folder view"""
    query = update.callback_query
    await query.answer()
    
    # Extract folder_id from callback data
    folder_id = int(query.data.split('_')[3])
    user = update.effective_user
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            await query.edit_message_text("❌ User not found.")
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
        
        # Store folder_id in context
        context.user_data['upload_folder_id'] = folder_id
        context.user_data['upload_folder_name'] = folder.name
        
        # Create done button
        keyboard = [[InlineKeyboardButton("✅ Done", callback_data="done_uploading")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📤 *Send photos or videos for folder:*\n\n"
            f"📁 {folder.name}\n\n"
            "Send your media files now. You can send multiple files.\n"
            "Click ✅ Done when finished or use /cancel",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return UPLOADING_MEDIA
        
    finally:
        session.close()


# GET MEDIA FUNCTIONALITY

async def get_media_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /get command or button - retrieve media from folder"""
    user = update.effective_user
    session = get_session()
    
    # Check if this is from a callback query
    is_callback = bool(update.callback_query)
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            message = "❌ User not found. Please send /start first."
            if is_callback:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(message)
            else:
                await update.message.reply_text(message)
            return ConversationHandler.END
        
        # Get user's folders
        folders = (
            session.query(Folder)
            .filter_by(user_id=db_user.id)
            .order_by(Folder.name)
            .all()
        )
        
        if not folders:
            message = (
                "📂 *No folders found*\n\n"
                "Please create a folder first using /newfolder"
            )
            if is_callback:
                await update.callback_query.edit_message_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text(message, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Build folder selection keyboard
        keyboard = []
        for folder in folders:
            media_count = session.query(Media).filter_by(folder_id=folder.id).count()
            keyboard.append([InlineKeyboardButton(
                f"📁 {folder.name} ({media_count})", 
                callback_data=f"get_from_{folder.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_get")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = "📥 *Select a folder to retrieve media:*"
        if is_callback:
            await update.callback_query.answer()
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
        
        return SELECTING_FOLDER_FOR_GET
        
    finally:
        session.close()


async def retrieve_all_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retrieve and send all media from a folder"""
    query = update.callback_query
    await query.answer()
    
    # Extract folder_id from callback data (format: "get_from_<id>" or "view_all_<id>")
    parts = query.data.split('_')
    folder_id = int(parts[-1])
    
    user = update.effective_user
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            await query.edit_message_text("❌ User not found.")
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
        
        # Get all media from folder
        media_items = (
            session.query(Media)
            .filter_by(folder_id=folder_id)
            .order_by(Media.created_at)
            .all()
        )
        
        if not media_items:
            await query.edit_message_text(
                f"📁 *{folder.name}* is empty.\n\n"
                "Use /add to add media.",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Send initial message
        await query.edit_message_text(
            f"📥 Retrieving media from *{folder.name}*...\n"
            f"📦 Total: {len(media_items)} items",
            parse_mode='Markdown'
        )
        
        # Send media in batches
        for media in media_items:
            try:
                if media.media_type == 'photo':
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=media.telegram_file_id
                    )
                elif media.media_type == 'video':
                    await context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        video=media.telegram_file_id
                    )
            except Exception as e:
                # If file_id is invalid, skip it
                continue
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"✅ Retrieved {len(media_items)} items from *{folder.name}*",
            parse_mode='Markdown'
        )
        
    finally:
        session.close()
    
    return ConversationHandler.END


async def retrieve_photos_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retrieve and send only photos from a folder"""
    query = update.callback_query
    await query.answer()
    
    # Extract folder_id from callback data
    folder_id = int(query.data.split('_')[2])
    
    user = update.effective_user
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            await query.edit_message_text("❌ User not found.")
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
        
        # Get photos from folder
        photos = (
            session.query(Media)
            .filter_by(folder_id=folder_id, media_type='photo')
            .order_by(Media.created_at)
            .all()
        )
        
        if not photos:
            await query.edit_message_text(
                f"📁 *{folder.name}* has no photos.\n\n"
                "Use /add to add media.",
                parse_mode='Markdown'
            )
            return
        
        # Send initial message
        await query.edit_message_text(
            f"📥 Retrieving photos from *{folder.name}*...\n"
            f"🖼️ Total: {len(photos)} photos",
            parse_mode='Markdown'
        )
        
        # Send photos
        for photo in photos:
            try:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo.telegram_file_id
                )
            except Exception as e:
                continue
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"✅ Retrieved {len(photos)} photos from *{folder.name}*",
            parse_mode='Markdown'
        )
        
    finally:
        session.close()


async def retrieve_videos_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retrieve and send only videos from a folder"""
    query = update.callback_query
    await query.answer()
    
    # Extract folder_id from callback data
    folder_id = int(query.data.split('_')[2])
    
    user = update.effective_user
    session = get_session()
    
    try:
        # Get user from database
        db_user = session.query(User).filter_by(telegram_user_id=user.id).first()
        
        if not db_user:
            await query.edit_message_text("❌ User not found.")
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
        
        # Get videos from folder
        videos = (
            session.query(Media)
            .filter_by(folder_id=folder_id, media_type='video')
            .order_by(Media.created_at)
            .all()
        )
        
        if not videos:
            await query.edit_message_text(
                f"📁 *{folder.name}* has no videos.\n\n"
                "Use /add to add media.",
                parse_mode='Markdown'
            )
            return
        
        # Send initial message
        await query.edit_message_text(
            f"📥 Retrieving videos from *{folder.name}*...\n"
            f"🎥 Total: {len(videos)} videos",
            parse_mode='Markdown'
        )
        
        # Send videos
        for video in videos:
            try:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=video.telegram_file_id
                )
            except Exception as e:
                continue
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"✅ Retrieved {len(videos)} videos from *{folder.name}*",
            parse_mode='Markdown'
        )
        
    finally:
        session.close()


async def cancel_get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel get media"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("❌ Cancelled.")
    
    return ConversationHandler.END


async def cancel_media_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel during media operations"""
    # Clear upload context
    context.user_data.pop('upload_folder_id', None)
    context.user_data.pop('upload_folder_name', None)
    
    await update.message.reply_text(
        "❌ Operation cancelled.\n\n"
        "Use /start to see the main menu."
    )
    return ConversationHandler.END
