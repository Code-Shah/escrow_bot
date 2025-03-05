# Telegram Escrow Bot Deployment Guide

## Required Files
Download and organize these files in your server:
```
├── main.py              # Main application entry
├── bot.py              # Telegram bot core
├── handlers.py         # Command handlers
├── models.py          # Database models
├── config.py          # Configuration
├── logger.py          # Logging setup
├── app.py             # Flask application
├── keep_alive.py      # Server monitoring
├── .env               # Environment variables
└── requirements.txt   # Python dependencies
```

## System Requirements
1. Python 3.11 or higher
2. PostgreSQL database
3. Telegram Bot Token (from @BotFather)

## Installation Steps

1. **System Setup**
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip postgresql postgresql-contrib -y
```

2. **Create Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install python-telegram-bot[job-queue]==21.10
pip install flask==3.1.0
pip install flask-sqlalchemy==3.1.1
pip install sqlalchemy==2.0.38
pip install psycopg2-binary==2.9.10
pip install python-dotenv==1.0.0
pip install waitress==2.1.2
pip install gunicorn==23.0.0
```

4. **Database Setup**
```sql
-- Run these commands in PostgreSQL
CREATE DATABASE escrow_bot_db;
CREATE USER escrow_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE escrow_bot_db TO escrow_user;
```

5. **Environment Setup**
Create a `.env` file with:
```
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://username:password@localhost:5432/escrow_bot_db
```

## Running the Bot

1. **Development Mode**
```bash
python main.py
```

2. **Production Mode (using Gunicorn)**
```bash
gunicorn --bind 0.0.0.0:8000 app:app
```

## Monitoring and Maintenance

1. **Check Bot Status**
```bash
# View logs
tail -f bot.log
```

2. **Database Backup**
```bash
pg_dump -U escrow_user escrow_bot_db > backup.sql
```

3. **Restore Database**
```bash
psql -U escrow_user escrow_bot_db < backup.sql
```

## Security Recommendations

1. Use strong passwords for database
2. Keep system and dependencies updated
3. Enable firewall rules
4. Monitor system logs
5. Use SSL/TLS for database connections

## Troubleshooting

1. If bot doesn't start:
   - Check logs in bot.log
   - Verify environment variables
   - Ensure database connection is working

2. If database connection fails:
   - Check PostgreSQL service status
   - Verify database credentials
   - Check database permissions

## Maintenance

1. Regular Updates:
```bash
git pull origin main
pip install -r requirements.txt
```

2. Log Rotation:
The bot automatically rotates logs (1MB size, 5 backup files)

For additional support or questions, refer to the project documentation or create an issue in the repository.
