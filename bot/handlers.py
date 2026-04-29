from __future__ import annotations

import logging
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from .scheduler import fire_time_from_now, parse_duration
from .storage import Reminder, ReminderStore

logger = logging.getLogger(__name__)

WELCOME = (
    "Hi! I'm a personal reminder bot.\n\n"
    "Set a reminder with:\n"
    "  /remind 30m Stand up and stretch\n"
    "  /remind 2h Call mom\n"
    "  /remind 1d Pay the rent\n\n"
    "Other commands: /list, /cancel <id>, /help"
)

HELP = (
    "Commands:\n"
    "/remind <duration> <message> — set a reminder\n"
    "/list — show your pending reminders\n"
    "/cancel <id> — cancel a reminder\n\n"
    "Duration format: 30s, 15m, 2h, 1d"
)


async def fire_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    job_data = context.job.data
    reminder_id: int = job_data["reminder_id"]
    chat_id: int = job_data["chat_id"]
    message: str = job_data["message"]

    store: ReminderStore = context.application.bot_data["store"]
    await context.bot.send_message(chat_id=chat_id, text=f"⏰ Reminder: {message}")
    store.mark_fired(reminder_id)


def _schedule_job(context: ContextTypes.DEFAULT_TYPE, reminder: Reminder) -> None:
    delay = (reminder.fire_at - datetime.now(timezone.utc)).total_seconds()
    delay = max(delay, 1.0)
    context.job_queue.run_once(
        fire_reminder,
        when=delay,
        data={
            "reminder_id": reminder.id,
            "chat_id": reminder.chat_id,
            "message": reminder.message,
        },
        name=f"reminder-{reminder.id}",
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP)


async def cmd_remind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /remind <duration> <message>\nExample: /remind 30m Buy milk"
        )
        return

    duration_token = context.args[0]
    message = " ".join(context.args[1:])

    try:
        parse_duration(duration_token)
    except ValueError as exc:
        await update.message.reply_text(str(exc))
        return

    fire_at = fire_time_from_now(duration_token)
    store: ReminderStore = context.application.bot_data["store"]
    reminder_id = store.add(
        chat_id=update.effective_chat.id,
        user_id=update.effective_user.id,
        message=message,
        fire_at=fire_at,
    )

    _schedule_job(
        context,
        Reminder(
            id=reminder_id,
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id,
            message=message,
            fire_at=fire_at,
        ),
    )

    await update.message.reply_text(
        f"✅ Reminder #{reminder_id} set for {duration_token} from now."
    )


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store: ReminderStore = context.application.bot_data["store"]
    pending = store.list_pending_for_user(update.effective_user.id)

    if not pending:
        await update.message.reply_text("No pending reminders.")
        return

    lines = ["Your pending reminders:"]
    for reminder in pending:
        local_time = reminder.fire_at.astimezone().strftime("%Y-%m-%d %H:%M")
        lines.append(f"#{reminder.id} — {local_time} — {reminder.message}")
    await update.message.reply_text("\n".join(lines))


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /cancel <id>")
        return

    try:
        reminder_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Reminder ID must be a number.")
        return

    store: ReminderStore = context.application.bot_data["store"]
    if store.cancel(reminder_id, update.effective_user.id):
        for job in context.job_queue.get_jobs_by_name(f"reminder-{reminder_id}"):
            job.schedule_removal()
        await update.message.reply_text(f"Cancelled reminder #{reminder_id}.")
    else:
        await update.message.reply_text(
            f"No pending reminder #{reminder_id} found for you."
        )


def reschedule_pending_on_startup(application) -> None:
    store: ReminderStore = application.bot_data["store"]
    for reminder in store.list_all_pending():
        delay = (reminder.fire_at - datetime.now(timezone.utc)).total_seconds()
        delay = max(delay, 1.0)
        application.job_queue.run_once(
            fire_reminder,
            when=delay,
            data={
                "reminder_id": reminder.id,
                "chat_id": reminder.chat_id,
                "message": reminder.message,
            },
            name=f"reminder-{reminder.id}",
        )
        logger.info("Rescheduled reminder #%s in %.0fs", reminder.id, delay)
