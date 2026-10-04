"""
SP Cloud Bot - Main entry point
"""
import logging
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters
)
from config import BOT_TOKEN
from database import init_db

# Import handlers
from handlers.start import start_command, help_command, help_callback
from handlers.folders import (
    folders_command,
    my_folders_callback,
    newfolder_command,
    new_folder_callback,
    receive_folder_name,
    cancel_command,
    view_folder_details,
    rename_folder_start,
    receive_new_folder_name,
    delete_folder_confirm,
    delete_folder_execute,
    cancel_delete_folder,
    cancel_rename,
    WAITING_FOR_FOLDER_NAME,
    WAITING_FOR_RENAME
)
from handlers.media import (
    add_media_command,
    add_media_callback,
    folder_selected_for_upload,
    receive_photo,
    receive_video,
    done_uploading,
    cancel_upload,
    add_to_folder_callback,
    get_media_command,
    retrieve_all_media,
    retrieve_photos_only,
    retrieve_videos_only,
    cancel_get,
    cancel_media_operation,
    SELECTING_FOLDER_FOR_UPLOAD,
    UPLOADING_MEDIA,
    SELECTING_FOLDER_FOR_GET
)
from handlers.search import (
    search_command,
    search_callback,
    receive_search_query,
    cancel_search,
    WAITING_FOR_SEARCH_QUERY
)
from handlers.placeholders import main_menu_callback

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update, context):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred. Please try again later."
        )


def main():
    """Start the bot"""
    # Initialize database
    try:
        init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        print(f"❌ Database initialization failed: {e}")
        print("Please check your DATABASE_URL in .env file")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler for folder creation
    folder_creation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("newfolder", newfolder_command),
            CallbackQueryHandler(new_folder_callback, pattern="^new_folder$")
        ],
        states={
            WAITING_FOR_FOLDER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_folder_name)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command)
        ],
        per_message=False,
        allow_reentry=True
    )
    
    # Conversation handler for folder rename
    folder_rename_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(rename_folder_start, pattern="^rename_folder_")
        ],
        states={
            WAITING_FOR_RENAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_folder_name)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_rename)
        ],
        per_message=False,
        allow_reentry=True
    )
    
    # Conversation handler for media upload
    media_upload_handler = ConversationHandler(
        entry_points=[
            CommandHandler("add", add_media_command),
            CallbackQueryHandler(add_media_callback, pattern="^add_media$"),
            CallbackQueryHandler(add_to_folder_callback, pattern="^add_to_folder_")
        ],
        states={
            SELECTING_FOLDER_FOR_UPLOAD: [
                CallbackQueryHandler(folder_selected_for_upload, pattern="^upload_to_"),
                CallbackQueryHandler(cancel_upload, pattern="^cancel_upload$")
            ],
            UPLOADING_MEDIA: [
                MessageHandler(filters.PHOTO, receive_photo),
                MessageHandler(filters.VIDEO, receive_video),
                CallbackQueryHandler(done_uploading, pattern="^done_uploading$"),
                CommandHandler("cancel", cancel_media_operation)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_media_operation),
            CallbackQueryHandler(cancel_upload, pattern="^cancel_upload$")
        ],
        per_message=False,
        allow_reentry=True
    )
    
    # Conversation handler for get media
    get_media_handler = ConversationHandler(
        entry_points=[
            CommandHandler("get", get_media_command),
            CallbackQueryHandler(get_media_command, pattern="^get_media$")
        ],
        states={
            SELECTING_FOLDER_FOR_GET: [
                CallbackQueryHandler(retrieve_all_media, pattern="^get_from_"),
                CallbackQueryHandler(cancel_get, pattern="^cancel_get$")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_media_operation)
        ],
        per_message=False,
        allow_reentry=True
    )
    
    # Conversation handler for search
    search_handler = ConversationHandler(
        entry_points=[
            CommandHandler("search", search_command),
            CallbackQueryHandler(search_callback, pattern="^search$")
        ],
        states={
            WAITING_FOR_SEARCH_QUERY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_search_query)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_search)
        ],
        per_message=False,
        allow_reentry=True
    )
    
    # Register conversation handlers first (highest priority)
    application.add_handler(folder_creation_handler)
    application.add_handler(folder_rename_handler)
    application.add_handler(media_upload_handler)
    application.add_handler(get_media_handler)
    application.add_handler(search_handler)
    
    # Register basic command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("folders", folders_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Register callback query handlers for main menu buttons
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(my_folders_callback, pattern="^my_folders$"))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    
    # Register callback query handlers for folder operations
    application.add_handler(CallbackQueryHandler(view_folder_details, pattern="^view_folder_"))
    application.add_handler(CallbackQueryHandler(retrieve_all_media, pattern="^view_all_"))
    application.add_handler(CallbackQueryHandler(retrieve_photos_only, pattern="^view_photos_"))
    application.add_handler(CallbackQueryHandler(retrieve_videos_only, pattern="^view_videos_"))
    
    # Register callback query handlers for delete folder
    application.add_handler(CallbackQueryHandler(delete_folder_confirm, pattern="^delete_folder_"))
    application.add_handler(CallbackQueryHandler(delete_folder_execute, pattern="^confirm_delete_"))
    application.add_handler(CallbackQueryHandler(cancel_delete_folder, pattern="^cancel_delete_"))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("🚀 SP Cloud Bot is starting...")
    print("🚀 SP Cloud Bot is running!")
    print("Press Ctrl+C to stop")
    
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == '__main__':
    main()
