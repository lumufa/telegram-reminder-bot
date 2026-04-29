from __future__ import annotations

import logging
import os
import sys

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

from .handlers import (
    cmd_cancel,
    cmd_help,
    cmd_list,
    cmd_remind,
    cmd_start,
    reschedule_pending_on_startup,
)
from .storage import ReminderStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    load_dotenv()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Copy .env.example to .env.")
        return 1

    db_path = os.environ.get("DATABASE_PATH", "reminders.db")
    store = ReminderStore(db_path)

    application = Application.builder().token(token).build()
    application.bot_data["store"] = store

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("remind", cmd_remind))
    application.add_handler(CommandHandler("list", cmd_list))
    application.add_handler(CommandHandler("cancel", cmd_cancel))

    async def post_init(app: Application) -> None:
        reschedule_pending_on_startup(app)

    application.post_init = post_init

    logger.info("Reminder bot starting. Database: %s", db_path)
    application.run_polling()
    return 0


if __name__ == "__main__":
    sys.exit(main())
