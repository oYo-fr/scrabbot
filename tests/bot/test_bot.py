"""
Tests pour le bot Scrabbot.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, User, Chat
from telegram.ext import ContextTypes

from bot.bot import ScrabbotBot
from bot.handlers.start import StartHandler
from bot.handlers.help import HelpHandler


class TestScrabbotBot:
    """Tests pour la classe ScrabbotBot."""

    def test_bot_initialization(self):
        """Test l'initialisation du bot."""
        # Mock des settings pour éviter les erreurs de configuration
        with pytest.MonkeyPatch().context() as m:
            # Jeton factice conforme au format attendu par PTB (9 chiffres + ':' + 35 chars)
            m.setenv("TELEGRAM_BOT_TOKEN", "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef123")
            m.setenv("API_SECRET_KEY", "test_secret")
            # Désactive tout webhook pour les tests
            m.delenv("TELEGRAM_WEBHOOK_URL", raising=False)

            bot = ScrabbotBot()
            assert bot is not None
            assert hasattr(bot, 'application')
            assert hasattr(bot, 'handlers')


class TestStartHandler:
    """Tests pour le gestionnaire StartHandler."""

    @pytest.mark.asyncio
    async def test_handle_start(self):
        """Test la commande /start."""
        # Créer un mock Update
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.first_name = "Test"
        update.effective_chat = MagicMock(spec=Chat)
        update.effective_chat.id = 123456

        # Créer un mock Context
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot.send_message = AsyncMock()

        # Tester le handler
        handler = StartHandler()
        await handler.handle(update, context)

        # Vérifier que send_message a été appelé
        context.bot.send_message.assert_called_once()


class TestHelpHandler:
    """Tests pour le gestionnaire HelpHandler."""

    @pytest.mark.asyncio
    async def test_handle_help(self):
        """Test la commande /help."""
        # Créer un mock Update
        update = MagicMock(spec=Update)
        update.effective_chat = MagicMock(spec=Chat)
        update.effective_chat.id = 123456

        # Créer un mock Context
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot.send_message = AsyncMock()

        # Tester le handler
        handler = HelpHandler()
        await handler.handle(update, context)

        # Vérifier que send_message a été appelé
        context.bot.send_message.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
