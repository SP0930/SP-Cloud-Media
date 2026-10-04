# ☁️ SP Cloud - Telegram Media Vault Bot

A production-ready Telegram bot for storing and organizing your photos and videos securely.

## Features

- 📂 Organize media in custom folders
- 📸 Store photos and videos using Telegram's infrastructure
- 🔒 Personal and secure (user-isolated storage)
- 🔍 Search and retrieve media easily
- 💾 Uses PostgreSQL for reliable data storage

## Tech Stack

- **Backend**: Python 3.11+
- **Telegram Library**: python-telegram-bot
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.11 or higher** installed
2. **PostgreSQL** installed and running
3. **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)

## Installation

### 1. Clone or Download the Project

```bash
cd "SP's Cloud Bot"
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Set Up PostgreSQL Database

Create a new database for the bot:

```sql
CREATE DATABASE sp_cloud;
```

### 6. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` file and add your credentials:
   ```
   BOT_TOKEN=your_bot_token_from_botfather
   DATABASE_URL=postgresql://postgres:your_password@localhost:5432/sp_cloud
   ```

**To get your Bot Token:**
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the token provided

## Running the Bot

### Start the bot:

```bash
python bot.py
```

You should see:
```
✅ Database tables created successfully
🚀 SP Cloud Bot is running!
Press Ctrl+C to stop
```

## Testing Stage 1

### 1. Open Telegram and find your bot

Search for your bot by the username you gave it in BotFather.

### 2. Send `/start` command

You should see:
```
☁️ Welcome to SP Cloud

Your personal Telegram Media Vault.
```

With buttons:
- 📂 My Folders
- ➕ New Folder
- 📤 Add Media
- 🔍 Search
- ℹ️ Help

### 3. Test `/help` command

Send `/help` and verify the help message displays.

### 4. Click the "ℹ️ Help" button

Verify it shows the same help message.

## Project Structure

```
sp-cloud/
│
├── bot.py                 # Main bot entry point
├── config.py              # Configuration management
├── database.py            # Database setup and session management
│
├── models/                # SQLAlchemy models
│   ├── __init__.py
│   ├── user.py           # User model
│   ├── folder.py         # Folder model
│   └── media.py          # Media model
│
├── handlers/              # Command and callback handlers
│   ├── __init__.py
│   └── start.py          # Start and help handlers
│
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Current Status: Stage 1 Complete ✅

**Implemented:**
- ✅ Project structure
- ✅ Environment configuration
- ✅ PostgreSQL connection
- ✅ SQLAlchemy models (User, Folder, Media)
- ✅ `/start` command with inline keyboard
- ✅ `/help` command
- ✅ Database initialization
- ✅ Error handling

**Next Stages:**
- Stage 2: Create, list, rename, and delete folders
- Stage 3: Upload photos and videos
- Stage 4: Retrieve media
- Stage 5: Search and security enhancements

## Troubleshooting

### Database Connection Error

If you see database connection errors:
1. Verify PostgreSQL is running
2. Check the DATABASE_URL in `.env` file
3. Ensure the database exists
4. Verify your PostgreSQL username and password

### Bot Token Error

If you see "BOT_TOKEN not found":
1. Ensure you created the `.env` file (not `.env.example`)
2. Verify the token is correct (no extra spaces)
3. Make sure the `.env` file is in the project root directory

### Import Errors

If you see module import errors:
1. Ensure virtual environment is activated
2. Run `pip install -r requirements.txt` again

## Security Notes

- Never commit your `.env` file to git
- Keep your bot token secret
- Each user's data is isolated by `telegram_user_id`
- Database queries are filtered by user ownership

## License

Personal use project.

## Support

For issues or questions, refer to:
- [python-telegram-bot documentation](https://docs.python-telegram-bot.org/)
- [SQLAlchemy documentation](https://docs.sqlalchemy.org/)
