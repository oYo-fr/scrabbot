"""
Base class for command handlers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from telegram import Update
from telegram.ext import ContextTypes


class BaseHandler(ABC):
    """Base class for all command handlers."""

    def __init__(self):
        """Initialize the handler."""
        self.name = self.__class__.__name__.replace("Handler", "").lower()

    @abstractmethod
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle the command.

        Args:
            update: Telegram update
            context: Update context
        """

    async def send_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[Any] = None,
    ) -> None:
        """
        Send a message.

        Args:
            update: Telegram update
            text: Message text
            parse_mode: Parsing mode (Markdown, HTML)
            reply_markup: Reply keyboard
        """
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )

    def get_user_info(self, update: Update) -> Dict[str, Any]:
        """
        Retrieve user information.

        Args:
            update: Telegram update

        Returns:
            User information
        """
        user = update.effective_user
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "language_code": user.language_code,
            }
        return {}
