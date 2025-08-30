"""
Tests for the Scrabbot bot.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Chat, Update, User
from telegram.ext import ContextTypes

from bot.bot import ScrabbotBot
from bot.handlers.help import HelpHandler
from bot.handlers.start import StartHandler


class TestScrabbotBot:
    """Tests for the ScrabbotBot class."""

    def test_bot_initialization(self):
        """Test bot initialization."""
        # Mock settings to avoid configuration errors
        with pytest.MonkeyPatch().context() as m:
            # Dummy token conforming to PTB expected format (9 digits + ':' + 35 chars)
            m.setenv(
                "TELEGRAM_BOT_TOKEN",
                "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef123",
            )
            m.setenv("API_SECRET_KEY", "test_secret")
            # Disable any webhook for tests
            m.delenv("TELEGRAM_WEBHOOK_URL", raising=False)

            bot = ScrabbotBot()
            assert bot is not None
            assert hasattr(bot, "application")
            assert hasattr(bot, "handlers")


class TestStartHandler:
    """Tests for the StartHandler."""

    @pytest.mark.asyncio
    async def test_handle_start(self):
        """Test the /start command."""
        # Create a mock Update
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.first_name = "Test"
        update.effective_chat = MagicMock(spec=Chat)
        update.effective_chat.id = 123456

        # Create a mock Context
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot.send_message = AsyncMock()

        # Test the handler
        handler = StartHandler()
        await handler.handle(update, context)

        # Verify that send_message was called
        context.bot.send_message.assert_called_once()


class TestHelpHandler:
    """Tests for the HelpHandler."""

    @pytest.mark.asyncio
    async def test_handle_help(self):
        """Test the /help command."""
        # Create a mock Update
        update = MagicMock(spec=Update)
        update.effective_chat = MagicMock(spec=Chat)
        update.effective_chat.id = 123456

        # Create a mock Context
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot.send_message = AsyncMock()

        # Test the handler
        handler = HelpHandler()
        await handler.handle(update, context)

        # Verify that send_message was called
        context.bot.send_message.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
