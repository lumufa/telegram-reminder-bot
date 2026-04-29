# Telegram Reminder Bot

A simple, self-hosted Telegram bot that lets users set personal reminders via chat. Built with `python-telegram-bot` (async) and SQLite for persistence — no external services required.

Designed to run 24/7 on a small VPS (e.g. a $5/month Hetzner CX22 box). Includes a `systemd` service file and step-by-step deploy guide in `deploy/`.

## Features

- `/remind 30m Buy milk` — set a relative reminder (`30s`, `15m`, `2h`, `1d`)
- `/list` — list your pending reminders
- `/cancel <id>` — cancel a reminder by ID
- Per-user storage in SQLite (multi-user safe)
- Survives restarts: pending reminders are reloaded from the database on startup
- Single-file SQLite storage — easy to back up

## Requirements

- Python 3.10+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

## Install

```bash
git clone https://github.com/lumufa/telegram-reminder-bot.git
cd telegram-reminder-bot
pip install -r requirements.txt
cp .env.example .env
# Edit .env and paste your TELEGRAM_BOT_TOKEN
```

## Run Locally

```bash
python -m bot
```

The bot will start polling Telegram. Open the bot in Telegram and send `/start`.

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Show welcome message |
| `/help` | Show command reference |
| `/remind <duration> <message>` | Set a reminder. Examples: `/remind 30m Stand up`, `/remind 2h Call mom`, `/remind 1d Pay rent` |
| `/list` | List your pending reminders |
| `/cancel <id>` | Cancel a pending reminder by its ID |

## Duration Format

| Suffix | Meaning | Example |
|--------|---------|---------|
| `s` | seconds | `30s` |
| `m` | minutes | `15m` |
| `h` | hours | `2h` |
| `d` | days | `1d` |

## Deploy to a VPS

See [`deploy/README.md`](deploy/README.md) for a complete walkthrough using `systemd` on a fresh Ubuntu 22.04+ server.

## Project Structure

```
telegram-reminder-bot/
├── bot/
│   ├── __init__.py
│   ├── __main__.py        # Entry point (python -m bot)
│   ├── handlers.py        # Command handlers
│   ├── scheduler.py       # In-memory job scheduling
│   └── storage.py         # SQLite persistence
├── deploy/
│   ├── README.md          # VPS deploy guide
│   └── reminder-bot.service  # systemd unit
├── .env.example
├── requirements.txt
└── README.md
```

## License

MIT
