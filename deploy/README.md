# Deploy Guide — Ubuntu 22.04+ VPS

This guide walks through deploying the reminder bot on a fresh Ubuntu VPS (e.g. Hetzner CX22, ~$5/month).

## 1. Create a non-root user

```bash
sudo adduser botuser
sudo usermod -aG sudo botuser
su - botuser
```

## 2. Install dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-venv git
```

## 3. Clone and set up the bot

```bash
cd ~
git clone https://github.com/lumufa/telegram-reminder-bot.git
cd telegram-reminder-bot

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env   # paste your TELEGRAM_BOT_TOKEN
```

## 4. Test it runs

```bash
python -m bot
```

Open the bot in Telegram and send `/start`. If it responds, stop the process with `Ctrl+C` and continue.

## 5. Install as a systemd service

```bash
sudo cp deploy/reminder-bot.service /etc/systemd/system/reminder-bot.service
sudo systemctl daemon-reload
sudo systemctl enable reminder-bot
sudo systemctl start reminder-bot
```

## 6. Verify

```bash
sudo systemctl status reminder-bot
journalctl -u reminder-bot -f
```

You should see "Reminder bot starting. Database: reminders.db" in the logs.

## Updating

```bash
cd ~/telegram-reminder-bot
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart reminder-bot
```

## Backups

The entire bot state lives in one SQLite file (`reminders.db`). Back it up with:

```bash
cp ~/telegram-reminder-bot/reminders.db ~/backups/reminders-$(date +%F).db
```
