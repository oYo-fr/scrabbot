"""
Handler for the /start command.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ContextTypes

from ..config import get_settings
from ..utils.godot_launcher import launch_godot_project
from .base import BaseHandler


class StartHandler(BaseHandler):
    """Handler for /start command."""

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle the /start command.

        Args:
            update: Telegram update
            context: Update context
        """
        user_info = self.get_user_info(update)

        welcome_message = f"""
🎲 *Welcome to Scrabbot!*

Hello {user_info.get('first_name', 'Player')}!

I am your intelligent Scrabble game partner.
With me, you can:

• 🎮 Play solo against AI
• 👥 Play with your friends
• 📚 Check game rules
• 📊 View your statistics

Use /help to see all available commands.

*Have fun!* 🎯
        """.strip()

        # Launch Godot scene (game) on local side (desktop)
        settings = get_settings()
        launched = False
        if settings.godot_executable_path:
            launched = launch_godot_project(
                executable_path=settings.godot_executable_path,
                project_dir=settings.godot_project_path,
            )

        suffix = ""
        reply_markup = None
        if settings.godot_web_url:
            # Add buttons to open Mini App (full screen) and browser fallback
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🎮 Open Fullscreen (Mini App)",
                            web_app=WebAppInfo(url=settings.godot_web_url),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🌐 Open in Browser",
                            url=settings.godot_web_url,
                        )
                    ],
                ]
            )
            suffix = "\n\nTip: use the 'Mini App' button for fullscreen."
        elif launched:
            suffix = "\n\n🖥️ Launching Godot interface..."

        await self.send_message(
            update=update,
            context=context,
            text=welcome_message + (suffix or "\n\n⚠️ Godot could not be launched automatically."),
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
