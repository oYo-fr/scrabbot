"""
Bot principal de Scrabbot.
"""

import logging
from typing import Dict, Optional, Type

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from .config import get_settings
from .handlers import HelpHandler, StartHandler


class ScrabbotBot:
    """Bot principal de Scrabbot."""

    def __init__(self):
        """Initialise le bot."""
        settings = get_settings()
        self.application = Application.builder().token(settings.telegram_bot_token).build()
        self.handlers: Dict[str, Type] = {
            "start": StartHandler,
            "help": HelpHandler,
        }
        self._setup_handlers()
        self._setup_logging()

    def _setup_logging(self):
        """Configure le système de logging."""
        settings = get_settings()
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=getattr(logging, settings.log_level.upper()),
        )
        self.logger = logging.getLogger(__name__)

    def _setup_handlers(self):
        """Configure les gestionnaires de commandes."""
        # Commandes de base
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))

        # Callbacks pour les boutons inline
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))

        # Gestionnaire d'erreurs
        self.application.add_error_handler(self._handle_error)

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la commande /start."""
        handler = StartHandler()
        await handler.handle(update, context)

    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la commande /help."""
        handler = HelpHandler()
        await handler.handle(update, context)

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère les callbacks des boutons inline."""
        query = update.callback_query
        if query:
            await query.answer()

            # Traiter les différents types de callbacks
            if query.data == "newgame":
                await self._handle_newgame_callback(update, context)
            elif query.data == "rules":
                await self._handle_rules_callback(update, context)
            elif query.data == "stats":
                await self._handle_stats_callback(update, context)
            elif query.data == "settings":
                await self._handle_settings_callback(update, context)

    async def _handle_newgame_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère le callback pour une nouvelle partie."""
        await update.callback_query.edit_message_text(
            text="🎮 *Nouvelle partie*\n\nFonctionnalité en cours de développement...",
            parse_mode="Markdown",
        )

    async def _handle_rules_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère le callback pour les règles."""
        await update.callback_query.edit_message_text(
            text="📚 *Règles du jeu*\n\nFonctionnalité en cours de développement...",
            parse_mode="Markdown",
        )

    async def _handle_stats_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère le callback pour les statistiques."""
        await update.callback_query.edit_message_text(
            text="📊 *Statistiques*\n\nFonctionnalité en cours de développement...",
            parse_mode="Markdown",
        )

    async def _handle_settings_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère le callback pour les paramètres."""
        await update.callback_query.edit_message_text(
            text="⚙️ *Configuration*\n\nFonctionnalité en cours de développement...",
            parse_mode="Markdown",
        )

    async def _handle_error(self, update: Optional[Update], context: ContextTypes.DEFAULT_TYPE):
        """Gère les erreurs du bot."""
        err_text = str(getattr(context, "error", ""))
        self.logger.error(f"Exception while handling an update: {err_text}")

        # Ne pas répondre au chat pour les erreurs globales ou conflits de polling
        if not update or "Conflict: terminated by other getUpdates request" in err_text:
            return

        if update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Une erreur s'est produite. Veuillez réessayer.",
                )
            except Exception:
                # Évite une boucle d'erreurs si l'envoi échoue
                pass

    def start_polling(self) -> None:
        """Démarre le bot en mode polling (bloquant)."""
        self.logger.info("Démarrage du bot Scrabbot (polling)...")
        # Méthode bloquante et non asynchrone en PTB 20+
        self.application.run_polling()

    def start_webhook(self) -> None:
        """Démarre le bot en mode webhook (bloquant)."""
        settings = get_settings()
        if not settings.telegram_webhook_url:
            raise ValueError("TELEGRAM_WEBHOOK_URL doit être configuré pour le mode webhook")

        self.logger.info("Démarrage du bot Scrabbot (webhook)...")
        # Méthode bloquante et non asynchrone en PTB 20+
        self.application.run_webhook(
            listen="0.0.0.0",
            port=get_settings().api_port,
            webhook_url=get_settings().telegram_webhook_url,
        )


def main() -> None:
    """Fonction principale pour démarrer le bot (bloquante)."""
    settings = get_settings()
    bot = ScrabbotBot()
    try:
        if settings.telegram_webhook_url:
            bot.start_webhook()
        else:
            bot.start_polling()
    except KeyboardInterrupt:
        logging.info("Arrêt demandé par l'utilisateur.")
    except Exception as e:
        logging.error(f"Erreur lors du démarrage du bot: {e}")


if __name__ == "__main__":
    main()
