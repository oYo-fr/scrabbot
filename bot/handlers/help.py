"""
Handler for the /help command.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from .base import BaseHandler


class HelpHandler(BaseHandler):
    """Handler for /help command."""

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle the /help command.

        Args:
            update: Telegram update
            context: Update context
        """
        help_message = """
📚 *Available Commands:*

*🎮 Game Commands:*
• /newgame - Create a new game
• /join <id> - Join a game
• /play <word> <position> - Play a word
• /pass - Skip your turn
• /exchange <letters> - Exchange letters

*📋 Information Commands:*
• /start - Start the bot
• /help - Display this help
• /rules - View game rules
• /status - Current game status
• /stats - Your statistics

*⚙️ Configuration Commands:*
• /language <fr/en> - Change language
• /difficulty <easy/medium/hard> - AI level

*💡 Examples:*
• `/newgame` - Create a solo game
• `/play CHAT H8` - Place "CHAT" at H8
• `/exchange QZ` - Exchange Q and Z

*Need help?* Contact @support
        """.strip()

        # Create inline buttons for quick actions
        keyboard = [
            [
                InlineKeyboardButton("🎮 New Game", callback_data="newgame"),
                InlineKeyboardButton("📚 Rules", callback_data="rules"),
            ],
            [
                InlineKeyboardButton("📊 Statistics", callback_data="stats"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await self.send_message(
            update=update,
            context=context,
            text=help_message,
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
